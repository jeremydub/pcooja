from pcooja.motes.mote import *

class Z1Mote(Mote):
    def __init__(self, id, x, y, mote_type=None, startup_delay=None):
        Mote.__init__(self, id, x, y, mote_type, startup_delay)

    def interfaces_to_xml(self, xb):
        Mote.interfaces_to_xml(self, xb)
        xb.write('<interface_config>')
        xb.indent()
        xb.write('org.contikios.cooja.mspmote.interfaces.MspMoteID')
        xb.write('<id>'+str(self.id)+'</id>')
        xb.unindent()
        xb.write('</interface_config>')
        if type(self.startup_delay) == int or type(self.startup_delay) == float :
            xb.write('<interface_config>')
            xb.indent()
            xb.write('org.contikios.cooja.mspmote.interfaces.MspClock')
            xb.write('<startup_delay_ms>'+str(int(self.startup_delay))+'</startup_delay_ms>')
            xb.unindent()
            xb.write('</interface_config>')

    @staticmethod
    def get_type():
        return "z1"

    @staticmethod
    def from_xml(xml, x, y, mote_type):
        if mote_type.java_class != "org.contikios.cooja.mspmote.Z1MoteType" :
            return None
        interface_config_tags = xml.xpath("interface_config")
        mote_id, startup_delay = (None, None)
        for interface_config_tag in interface_config_tags:
            if "interfaces.MspMoteID" in interface_config_tag.text:
                mote_id = int(interface_config_tag.xpath("id/text()")[0])
            elif "interfaces.MspClock" in interface_config_tag.text:
                if len(interface_config_tag.xpath("startup_delay_ms/text()")) == 1:
                    startup_delay = int(interface_config_tag.xpath("startup_delay_ms/text()")[0])
                else:
                    startup_delay = None
        return Z1Mote(mote_id, x, y, mote_type=mote_type, startup_delay=startup_delay)


class Z1MoteType(MoteType):
    def __init__(self, firmware_path, identifier=None, make_target=None, interfaces=None, firmware_command=None, description=None, firmware_copy=True):
        default_interfaces=['org.contikios.cooja.interfaces.IPAddress',
        'org.contikios.cooja.mspmote.interfaces.MspClock',
        'org.contikios.cooja.mspmote.interfaces.MspMoteID',
        'org.contikios.cooja.mspmote.interfaces.MspButton',
        'org.contikios.cooja.mspmote.interfaces.Msp802154Radio',
        'org.contikios.cooja.mspmote.interfaces.MspDefaultSerial',
        'org.contikios.cooja.mspmote.interfaces.MspLED',
        'org.contikios.cooja.mspmote.interfaces.MspDebugOutput'
        ]

        if interfaces != None:
            for interface in interfaces:
                if interface not in default_interfaces:
                    default_interfaces.append(interface)

        MoteType.__init__(self, firmware_path, identifier, 'org.contikios.cooja.mspmote.Z1MoteType', firmware_command=firmware_command, platform_target="z1", make_target=make_target, interfaces=default_interfaces, description=description, firmware_copy=firmware_copy)

    def compile_firmware(self, make_options="", clean=False, verbose=False):
        return MoteType.compile_firmware(self, make_options=make_options, clean=clean, verbose=verbose)    

Mote.Types.append(Z1Mote)
