from lxml import etree

from pcooja.radio.udgm.medium import UDGM
from pcooja.radio.dgrm.medium import DGRM
from pcooja.topology import Topology

class CSCParser:

    @staticmethod
    def export_simulation(simulation, filename, enable_log=True, enable_pcap=True, gui_enabled=False):
        """
        Simple and primitive .csc file exporter.
        """
        xb = XmlBuilder()

        xb.write(f'''<?xml version="1.0" encoding="UTF-8"?>
        <simconf>
            <simulation>
                <title>{simulation.title}</title>
                <randomseed>{simulation.seed}</randomseed>
                <motedelay_us>1000000</motedelay_us>''')

        # Radio settings
        simulation.topology.radiomedium.to_xml(xb)

        xb.write(f'''
        <events>
            <logoutput>40000</logoutput>
        </events>''')

        # Mote Types
        for mote_type in simulation.mote_types:
            mote_type.to_xml(xb)

        # Motes
        for mote in simulation.topology:
            mote.to_xml(xb)

        xb.write('</simulation>')

        #Run script
        simulation.script_runner.to_xml(xb, False)

        if gui_enabled:
            xb.write('''
            <plugin>
                org.contikios.cooja.plugins.LogListener
                <plugin_config>
                    <filter />
                    <formatted_time />
                    <coloring />
                </plugin_config>
                <width>838</width>
                <z>1</z>
                <height>978</height>
                <location_x>237</location_x>
                <location_y>1</location_y>
            </plugin>''')

        if gui_enabled or enable_pcap:
            analyzer = "6lowpan-pcap" if enable_pcap else "6lowpan"
            xb.write(f'''
            <plugin>
                org.contikios.cooja.plugins.RadioLogger
                <plugin_config>
                    <split>639</split>
                    <formatted_time />
                    <showdups>false</showdups>
                    <hidenodests>true</hidenodests>
                    <analyzers name=\"{analyzer}\" />
                </plugin_config>
                <width>837</width>
                <z>0</z>
                <height>979</height>
                <location_x>1075</location_x>
                <location_y>0</location_y>
            </plugin>''')

        if gui_enabled:
            udgm_visualizer = ""
            if str(simulation.topology.radiomedium.get_type()) == str(UDGM):
                udgm_visualizer = "<skin>org.contikios.cooja.plugins.skins.UDGMVisualizerSkin</skin>"
            xb.write(f'''
            <plugin>
                org.contikios.cooja.plugins.Visualizer
                <plugin_config>
                    <moterelations>true</moterelations>
                    <skin>org.contikios.cooja.plugins.skins.TrafficVisualizerSkin</skin>
                    <skin>org.contikios.cooja.plugins.skins.IDVisualizerSkin</skin>
                    {udgm_visualizer} 
                    <skin>org.contikios.cooja.plugins.skins.MoteTypeVisualizerSkin</skin>
                </plugin_config>
                <width>243</width>
                <z>2</z>
                <height>700</height>
                <location_x>0</location_x>
                <location_y>144</location_y>
            </plugin>
            <plugin>
                org.contikios.cooja.plugins.SimControl
                <width>254</width>
                <z>3</z>
                <height>144</height>
                <location_x>-1</location_x>
                <location_y>1</location_y>
            </plugin>''')

        if str(simulation.topology.radiomedium.get_type()) == str(DGRM):
            simulation.topology.radiomedium.event_to_xml(xb)

        xb.write("</simconf>")
        

        xb.save(filename)

class XmlBuilder:
    indent_count=0
    indent_symbol="  "

    def __init__(self):
        self.content=[]

    def indent(self):
        self.indent_count += 1

    def unindent(self):
        self.indent_count -= 1

    def write(self, line):
        self.content.append((self.indent_symbol*self.indent_count)+line+'\n')
    
    def undo(self):
        self.content.pop()

    def save(self, filename):
        f=open(filename,"w")
        for line in self.content:
            f.write(line)
        f.close()

    def __str__(self):
        return self.content
