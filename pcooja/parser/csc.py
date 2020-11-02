from pcooja.radio.udgm.medium import UDGM
from pcooja.radio.dgrm.medium import DGRM

class CSCParser:
    @staticmethod
    def import_simulation(simulation):
        """"""
    
    @staticmethod
    def export_simulation(simulation, filename, enable_log=True, enable_pcap=True, gui_enabled=False):
        """
        Simple and primitive .csc file exporter.
        """
        xb = XmlBuilder()

        xb.write('<?xml version="1.0" encoding="UTF-8"?>')
        xb.write("<simconf>")
        xb.indent()
        xb.write('<project EXPORT="discard">[APPS_DIR]/mrm</project>')
        xb.write('<project EXPORT="discard">[APPS_DIR]/mspsim</project>')
        xb.write('<project EXPORT="discard">[APPS_DIR]/avrora</project>')
        xb.write('<project EXPORT="discard">[APPS_DIR]/serial_socket</project>')
        xb.write('<project EXPORT="discard">[APPS_DIR]/collect-view</project>')
        xb.write('<project EXPORT="discard">[APPS_DIR]/powertracker</project>')
        
        xb.write("<simulation>")
        xb.indent()

        # General settings
        xb.write('<title>'+simulation.title+'</title>')
        xb.write('<randomseed>'+str(simulation.seed)+'</randomseed>')
        xb.write('<motedelay_us>'+str(1000000)+'</motedelay_us>')

        # Radio settings
        simulation.topology.radiomedium.to_xml(xb)

        xb.write('<events>')
        xb.indent()
        xb.write('<logoutput>40000</logoutput>')
        xb.unindent()
        xb.write('</events>')

        # Mote Types
        for mote_type in simulation.mote_types:
            mote_type.to_xml(xb)

        # Motes
        for mote in simulation.topology:
            mote.to_xml(xb)

        xb.unindent()
        xb.write("</simulation>")

        #Run script
        simulation.script_runner.to_xml(xb, gui_enabled)

        if gui_enabled:
            xb.write("<plugin>")
            xb.indent()
            xb.write("org.contikios.cooja.plugins.LogListener")
            xb.write("<plugin_config>")
            xb.indent()
            xb.write("<filter />")
            xb.write("<formatted_time />")
            xb.write("<coloring />")
            xb.unindent()
            xb.write("</plugin_config>")
            xb.write("<width>838</width>")
            xb.write("<z>1</z>")
            xb.write("<height>978</height>")
            xb.write("<location_x>237</location_x>")
            xb.write("<location_y>1</location_y>")
            xb.unindent()
            xb.write("</plugin>")

            xb.write("<plugin>")
            xb.indent()
            xb.write("org.contikios.cooja.plugins.RadioLogger")
            xb.write("<plugin_config>")
            xb.indent()
            xb.write("<split>639</split>")
            xb.write("<formatted_time />")
            xb.write("<showdups>false</showdups>")
            xb.write("<hidenodests>true</hidenodests>")
            xb.write("<analyzers name=\"6lowpan\" />")
            xb.unindent()
            xb.write("</plugin_config>")
            xb.write("<width>837</width>")
            xb.write("<z>0</z>")
            xb.write("<height>979</height>")
            xb.write("<location_x>1075</location_x>")
            xb.write("<location_y>0</location_y>")
            xb.unindent()
            xb.write("</plugin>")

            xb.write("<plugin>")
            xb.indent()
            xb.write("org.contikios.cooja.plugins.Visualizer")
            xb.write("<plugin_config>")
            xb.indent()
            xb.write("<moterelations>true</moterelations>")
            xb.write("<skin>org.contikios.cooja.plugins.skins.TrafficVisualizerSkin</skin>")
            xb.write("<skin>org.contikios.cooja.plugins.skins.IDVisualizerSkin</skin>")
            if str(simulation.topology.radiomedium.get_type()) == str(UDGM):
                xb.write("<skin>org.contikios.cooja.plugins.skins.UDGMVisualizerSkin</skin>")
            xb.write("<skin>org.contikios.cooja.plugins.skins.MoteTypeVisualizerSkin</skin>")
            xb.unindent()
            xb.write("</plugin_config>")
            xb.write("<width>243</width>")
            xb.write("<z>2</z>")
            xb.write("<height>700</height>")
            xb.write("<location_x>0</location_x>")
            xb.write("<location_y>144</location_y>")
            xb.unindent()
            xb.write("</plugin>")

            xb.write("<plugin>")
            xb.indent()
            xb.write("org.contikios.cooja.plugins.SimControl")
            xb.write("<width>254</width>")
            xb.write("<z>3</z>")
            xb.write("<height>144</height>")
            xb.write("<location_x>-1</location_x>")
            xb.write("<location_y>1</location_y>")
            xb.unindent()
            xb.write("</plugin>")

        if not gui_enabled:
            if enable_pcap:
                xb.write("<plugin>")
                xb.indent()
                xb.write("org.contikios.cooja.plugins.PcapLogger")
                xb.write("<plugin_config>")
                xb.indent()
                xb.write("<destination_file>"+str(simulation.id)+".pcap"+"</destination_file>")
                xb.unindent()
                xb.write("</plugin_config>")
                xb.write("<width>500</width>")
                xb.write("<z>0</z>")
                xb.write("<height>100</height>")
                xb.write("<location_x>46</location_x>")
                xb.write("<location_y>48</location_y>")
                xb.unindent()
                xb.write("</plugin>")

        # print(simulation.topology.radiomedium.get_type())
        # print(type(simulation.topology.radiomedium.get_type()))
        # print(RadioMedium.RadioMediumType.DGRM)
        # print(RadioMedium.RadioMediumType.DGRM is RadioMedium.RadioMediumType.DGRM)
        # print(type(RadioMedium.RadioMediumType.DGRM))
        # print(simulation.topology.radiomedium.get_type() ==  RadioMedium.RadioMediumType.DGRM)
        # print(simulation.topology.radiomedium.get_type() is  RadioMedium.RadioMediumType.DGRM)

        # print(str(simulation.topology.radiomedium.get_type()) ==  str(RadioMedium.RadioMediumType.DGRM))
        if str(simulation.topology.radiomedium.get_type()) == str(DGRM):
            simulation.topology.radiomedium.event_to_xml(xb)

        xb.unindent()
        xb.write("</simconf>")
        xb.write("")

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

    def save(self, filename):
        f=open(filename,"w")
        for line in self.content:
            f.write(line)
        f.close()

    def __str__(self):
        return self.content
