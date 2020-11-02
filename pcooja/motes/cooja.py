from pcooja.motes.mote import Mote, MoteType

class CoojaMote(Mote):
    """ The biterate is in kbps """
    def __init__(self, id, x, y, mote_type=None, startup_delay=None, bitrate=250.0):
        Mote.__init__(self, id, x, y, mote_type, startup_delay)
        self.bitrate = bitrate

    def interfaces_to_xml(self, xb):
        Mote.interfaces_to_xml(self, xb)
        xb.write('<interface_config>')
        xb.indent()
        xb.write('org.contikios.cooja.contikimote.interfaces.ContikiMoteID')
        xb.write('<id>'+str(self.id)+'</id>')
        xb.unindent()
        xb.write('</interface_config>')
        if type(self.startup_delay) == int or type(self.startup_delay) == float :
            xb.write('<interface_config>')
            xb.indent()
            xb.write('org.contikios.cooja.mspmote.interfaces.ContikiClock')
            xb.write('<startup_delay_ms>'+str(int(self.startup_delay))+'</startup_delay_ms>')
            xb.unindent()
            xb.write('</interface_config>')

        xb.write('<interface_config>')
        xb.indent()
        xb.write('org.contikios.cooja.contikimote.interfaces.ContikiRadio')
        xb.write('<bitrate>'+str(self.bitrate)+'</bitrate>')
        xb.unindent()
        xb.write('</interface_config>')

        xb.write('<interface_config>')
        xb.indent()
        xb.write('org.contikios.cooja.contikimote.interfaces.ContikiEEPROM')
        xb.write('<eeprom>AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==</eeprom>')
        xb.unindent()
        xb.write('</interface_config>')

    @staticmethod
    def get_type():
        return "cooja"
        
    @staticmethod
    def from_xml(xml, x, y, mote_type):
        if mote_type.java_class != "org.contikios.cooja.contikimote.ContikiMoteType" :
            return None
        interface_config_tags = xml.xpath("interface_config")
        mote_id, startup_delay = (None, None)
        bitrate = 250.0
        for interface_config_tag in interface_config_tags:
            if "interfaces.ContikiMoteID" in interface_config_tag.text:
                mote_id = int(interface_config_tag.xpath("id/text()")[0])
            elif "interfaces.ContikiRadio" in interface_config_tag.text:
                bitrate = float(interface_config_tag.xpath("bitrate/text()")[0])
            elif "interfaces.ContikiClock" in interface_config_tag.text:
                if len(interface_config_tag.xpath("startup_delay_ms/text()")) == 1:
                    startup_delay = int(interface_config_tag.xpath("startup_delay_ms/text()")[0])
                else:
                    startup_delay = None

        return CoojaMote(mote_id, x, y, mote_type=mote_type, startup_delay=startup_delay, bitrate=bitrate)

class CoojaMoteType(MoteType):
    def __init__(self, firmware_path, identifier=None, make_target=None, interfaces=None, firmware_command=None, description=None, firmware_copy=False):
        default_interfaces=['org.contikios.cooja.interfaces.Battery',
        'org.contikios.cooja.contikimote.interfaces.ContikiVib',
        'org.contikios.cooja.contikimote.interfaces.ContikiMoteID',
        'org.contikios.cooja.contikimote.interfaces.ContikiRS232',
        'org.contikios.cooja.contikimote.interfaces.ContikiBeeper',
        'org.contikios.cooja.contikimote.interfaces.ContikiIPAddress',
        'org.contikios.cooja.contikimote.interfaces.ContikiRadio',
        'org.contikios.cooja.contikimote.interfaces.ContikiButton',
        'org.contikios.cooja.contikimote.interfaces.ContikiPIR',
        'org.contikios.cooja.contikimote.interfaces.ContikiClock',
        'org.contikios.cooja.contikimote.interfaces.ContikiLED',
        'org.contikios.cooja.contikimote.interfaces.ContikiCFS',
        'org.contikios.cooja.contikimote.interfaces.ContikiEEPROM',
        ]

        if interfaces != None:
            for interface in interfaces:
                if interface not in default_interfaces:
                    default_interfaces.append(interface)


        MoteType.__init__(self, firmware_path, identifier, 'org.contikios.cooja.contikimote.ContikiMoteType', firmware_command=firmware_command, platform_target="cooja", make_target=make_target, interfaces=default_interfaces, description=description, firmware_copy=firmware_copy, symbols=False)

    def compile_firmware(self, make_options="", clean=False, verbose=False):
        # We don't use firmware_copy, the firmware is compiled by cooja and not by a makefile
        pass

Mote.Types.append(CoojaMote)
