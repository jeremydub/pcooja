/*
 * Copyright (c) 2006, Swedish Institute of Computer Science.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */

package org.contikios.cooja.plugins;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Observable;
import java.util.Observer;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

import org.apache.log4j.Logger;
import org.jdom.Element;

import java.io.IOException;
import java.io.File;

import org.contikios.cooja.ClassDescription;
import org.contikios.cooja.Cooja;
import org.contikios.cooja.plugins.analyzers.PcapExporter;
import org.contikios.cooja.PluginType;
import org.contikios.cooja.RadioConnection;
import org.contikios.cooja.RadioMedium;
import org.contikios.cooja.RadioPacket;
import org.contikios.cooja.Simulation;
import org.contikios.cooja.TimeEvent;
import org.contikios.cooja.VisPlugin;

/**
 * This is a simple Pcap logger.
 * 
 * @author Jeremy Dubrulle
 */
@ClassDescription("Pcap Logger") /* Description shown in menu */
@PluginType(PluginType.SIM_PLUGIN)
public class PcapLogger extends VisPlugin {
  private static Logger logger = Logger.getLogger(PcapLogger.class);

  private Simulation sim;
  private JLabel label;
  private RadioMedium radioMedium;
  private Observer radioMediumObserver;
  private PcapExporter pcapExporter = null;

  private JTextField textField;

  /**
   * @param simulation Simulation object
   * @param gui GUI object 
   */
  public PcapLogger(final Simulation simulation, final Cooja gui) {
    super("Pcap Logger", gui, false);
    this.sim = simulation;

    radioMedium = simulation.getRadioMedium();

    /* Text field */
    label = new JLabel("Pcap Logger");
    add(BorderLayout.NORTH, label);

    /* Text field */
    textField = new JTextField("radio.pcap");
    add(BorderLayout.SOUTH, textField);

    radioMedium.addRadioTransmissionObserver(radioMediumObserver = new Observer() {
      @Override
      public void update(Observable obs, Object obj) {
        RadioConnection conn = radioMedium.getLastConnection();
        if (conn == null) {
          return;
        }
        final RadioConnectionLog loggedConn = new RadioConnectionLog();
        loggedConn.packet = conn.getSource().getLastPacketTransmitted();
        if (loggedConn.packet == null)
          return;
        loggedConn.startTime = conn.getStartTime();
        loggedConn.endTime = sim.getSimulationTime();
        loggedConn.connection = conn;

        if(pcapExporter == null){
          String destination = textField.getText();
          if(destination.equals("")){
            destination = "radio.pcap";
          }
          File pcapFile = new File(destination);
          try{
            pcapExporter = new PcapExporter();
            pcapExporter.openPcap(pcapFile);
          }
          catch(IOException e){
            logger.error(e);
          }
        }

        try{
          pcapExporter.exportPacketData(loggedConn.packet.getPacketData(),loggedConn.startTime);
        }
        catch(IOException e){
          logger.error(e);
        }
      }
    });

    setSize(300,100);
  }

  public void closePlugin() {
    /* Clean up plugin resources */
    logger.info("Deleting radio medium observer");
    radioMedium.deleteRadioTransmissionObserver(radioMediumObserver);
    try{
      if(pcapExporter != null) pcapExporter.closePcap();
    }
    catch(IOException e){
      logger.error(e);
    }
  }

  private class RadioConnectionLog {

    long startTime;
    long endTime;
    RadioConnection connection;
    RadioPacket packet;

    RadioConnectionLog hiddenBy = null;
    int hides = 0;

    String data = null;
    String tooltip = null;
  }

  public Collection<Element> getConfigXML() {
    ArrayList<Element> config = new ArrayList<Element>();
    Element element;

    /* Save text field */
    element = new Element("destination_file");
    element.setText(textField.getText());
    config.add(element);

    return config;
  }

  public boolean setConfigXML(Collection<Element> configXML, boolean visAvailable) {
    for (Element element : configXML) {
      if (element.getName().equals("destination_file")) {
        final String text = element.getText();
        SwingUtilities.invokeLater(new Runnable() {
          public void run() {
            textField.setText(text);
          }
        });
      }
    }
    return true;
  }

}
