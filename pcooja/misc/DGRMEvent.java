/*
 * Copyright (c) 2010, Swedish Institute of Computer Science.
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
import java.util.ArrayList;
import java.util.Collection;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.SwingConstants;

import org.jdom.Element;

import org.apache.log4j.Logger;

import org.contikios.cooja.ClassDescription;
import org.contikios.cooja.Cooja;
import org.contikios.cooja.PluginType;
import org.contikios.cooja.Simulation;
import org.contikios.cooja.SupportedArguments;
import org.contikios.cooja.interfaces.Radio;
import org.contikios.cooja.RadioMedium;
import org.contikios.cooja.TimeEvent;
import org.contikios.cooja.VisPlugin;
import org.contikios.cooja.radiomediums.DGRMDestinationRadio;
import org.contikios.cooja.radiomediums.DirectedGraphMedium;
import org.contikios.cooja.radiomediums.DirectedGraphMedium.Edge;


/**
 * Event on DGRM edge.
 * 
 * @author Maximilien Charlier
 */
@ClassDescription("DGRM Event") /* Description shown in menu */
@PluginType(PluginType.SIM_PLUGIN)
@SupportedArguments(radioMediums = {DirectedGraphMedium.class})
public class DGRMEvent extends VisPlugin {

  private static Logger logger = Logger.getLogger(DGRMEvent.class);

  private Simulation simulation;
  private DirectedGraphMedium radioMedium;
  private ArrayList<DGRMEventEdge> eventEdges;

  private JLabel label;

  /**
   * @param simulation Simulation object
   * @param gui GUI object 
   */
  public DGRMEvent(Simulation simulation, Cooja gui) {
    super("DGRM Event", gui, false);
  	this.simulation = simulation;

    this.radioMedium = (DirectedGraphMedium) simulation.getRadioMedium();

    this.eventEdges = new ArrayList<DGRMEventEdge>();
    /* Text field */
    label = new JLabel("Interaction not available.", SwingConstants.CENTER);
    add(BorderLayout.CENTER, label);

    setSize(300,100);
 	}
 	/**
 	* @return a Collection<Element> for the exportation in XML.
 	*/
  public Collection<Element> getConfigXML() {
    ArrayList<Element> config = new ArrayList<Element>();
    for (DGRMEventEdge eventEdge : this.eventEdges){
      Element element = new Element("DGRMEventEdge");
    	element.addContent(eventEdge.getConfigXML());
      config.add(element);
    }

    return config;
  }
  /**
  * Configure the plugin according an XML file.
  */
	public boolean setConfigXML(final Collection<Element> configXML, boolean visAvailable) {

    for (Element element : configXML) {
			if (element.getName().equals("DGRMEventEdge")) {
				DGRMEventEdge eventEdge = DGRMEventEdge.fromConfigXML(element, this.simulation);
				if (eventEdge != null){
					this.scheduleEvent(eventEdge);
				}
			}
		}
    return true;
	}

	/**
	 * Schedule the change in the simulation according a DGRMEventEdge.
	 */
	public void scheduleEvent(final DGRMEventEdge eventEdge){
		final DirectedGraphMedium radioMedium = this.radioMedium;

		TimeEvent delayedEvent = new TimeEvent(0) {
			public void execute(long t) {
				switch(eventEdge.action){
					case ADD : 
						radioMedium.addEdge(eventEdge.edge);
						break;
					case REMOVE:
						radioMedium.removeEdge(eventEdge.edge);
						break;
					case MODIFY:
						radioMedium.removeEdge(eventEdge.edge);
						radioMedium.addEdge(eventEdge.edge);
						break;
				}
			}
		};

		this.simulation.scheduleEvent(delayedEvent, eventEdge.time);

		/* Add the event in a list for the exportation in XML */
		this.eventEdges.add(eventEdge);

		updateLabel();
	}

	/**
	 * Add a link between the node 1 et 2 after 3 seconds
	 */
	private void testFunction(){
		Radio source =  simulation.getMoteWithID(1).getInterfaces().getRadio();
		DGRMDestinationRadio dest = new DGRMDestinationRadio(simulation.getMoteWithID(2).getInterfaces().getRadio());
		Edge edge = new Edge(source, dest);
		scheduleEvent(new DGRMEventEdge(DGRMEventAction.ADD, 60000000, edge));
		scheduleEvent(new DGRMEventEdge(DGRMEventAction.REMOVE, 120000000, edge));
	}

	private void updateLabel(){
		String output = "<html>Interaction not available<br/>";
		output += "" + this.eventEdges.size() + " events: ";
		output += "" + coutEdge(DGRMEventAction.ADD) + " ADD | ";
		output += "" + coutEdge(DGRMEventAction.REMOVE) + " REMOVE | ";
		output += "" + coutEdge(DGRMEventAction.MODIFY) + " MODIFY.";
		output +="</html>";
		label.setText(output);
	}
	private int coutEdge(DGRMEventAction action){
		int output = 0;
		for (DGRMEventEdge eventEdge : this.eventEdges){
			if(eventEdge.action == action){
				output ++;
			}
		}
		return output;
	}
  public static class DGRMEventEdge {
  	public DGRMEventAction action;
  	public Edge edge;
  	public long time;

  	/**
  	 * Event Edge for a DGRM.
  	 * @param action specify the type of action (add, remove, modify)
  	 * @param time is the Execution time is in micro second.
  	 * 							A value of 1'000'000 is for one second.
  	 * @param edge is a DGRM Edge.
  	 */
	  public DGRMEventEdge(DGRMEventAction action, long time, Edge edge){
	  	this.action = action;
	  	this.edge = edge;
	  	this.time = time;
	  }

	  public Collection<Element> getConfigXML(){
      ArrayList<Element> config = new ArrayList<Element>();
      Element element = new Element("action");
      element.setText("" + this.action.name());
      config.add(element);

      element = new Element("time");
      element.setText("" + this.time);
      config.add(element);

			element = new Element("edge");
      element.addContent(this.edge.getConfigXML());
      config.add(element);

      return config;
	  }
	  /**
	   * fromConfigXML retrun a DGRMEventEdge from a configXML gived by the \
	   *	DGRMEvent.
	   * @param configXML a xml "DGRMEventEdge" element.
	   * @return a DGRMEventEdge from a configXML.
	   */
	  public static DGRMEventEdge fromConfigXML(Element configXML, Simulation simulation) {
	  	if(!configXML.getName().equals("DGRMEventEdge")){
	  		/* Check if the element is a DGRMEventEdge */
	  		return null;
	  	}

	  	DGRMEventAction action = null;
	  	long time = 0;
	  	Edge edge =null;
	  	@SuppressWarnings("unchecked")
			Collection<Element> eventEdgeConfig = configXML.getChildren();
			if(eventEdgeConfig.size() != 3){
				/* We need 3 elements: action, time and edge. */
	      throw new RuntimeException("Failed loading DGRM event links, aborting");
			}
			for (Element element : eventEdgeConfig){
				if (element.getName().equals("action")) {
					action = DGRMEventAction.valueOf(element.getText());
					if (action == null) {
						throw new RuntimeException("No action type " + element.getText());
					}
				}
				else if(element.getName().equals("time")){
					time = Integer.parseInt(element.getText());
					if (time == 0) {
						throw new RuntimeException("Not a time " + element.getText());
					}
				}
	      else if (element.getName().equals("edge")) {
	        @SuppressWarnings("unchecked")
					Collection<Element> edgeConfig = element.getChildren();
	        Radio source = null;
	        DGRMDestinationRadio dest = null;
	        for (Element edgeElement : edgeConfig) {
	          if (edgeElement.getName().equals("source")) {
	            source = simulation.getMoteWithID(
	            		Integer.parseInt(edgeElement.getText())
	            	).getInterfaces().getRadio();
	          } 
	          else if (edgeElement.getName().equals("dest")) {
	          	dest = new DGRMDestinationRadio();
              @SuppressWarnings("unchecked")
							Collection<Element> children = edgeElement.getChildren();
							dest.setConfigXML(children, simulation);
	          }
	        }
	        if (source == null || dest == null) {
	        	throw new RuntimeException("Failed loading DGRM event links, aborting");
	        } else {
	          edge = new Edge(source, dest);
	        }
	      }
	    }
	    if(action != null && time > 0 && edge!= null){
	    	/* Check if e have a valide DGRMEventEdge */
	    	return new DGRMEventEdge(action, time, edge);
	    }
	    else{
	    	return null;
	    }
	  }
	}

	public enum DGRMEventAction { 
		ADD, 
		REMOVE, 
		MODIFY; 
	};

}
