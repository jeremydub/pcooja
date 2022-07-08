from pcooja.motes.mote import MoteType, Mote
import os
import atexit
import fnmatch

class SkyMote(Mote):
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
        return "sky"

    @staticmethod
    def from_xml(xml, x, y, mote_type):
        if mote_type.java_class != self._get_java_class():
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
        return SkyMote(mote_id, x, y, mote_type=mote_type, startup_delay=startup_delay)


class SkyMoteType(MoteType):
    def __init__(self, firmware_path, **kwargs):
        super().__init__(firmware_path, **kwargs)
    
    @staticmethod
    def _get_platform_target():
        return "sky"

    @staticmethod
    def _get_default_interfaces():
        return MoteType._get_default_interfaces()+\
            ['org.contikios.cooja.mspmote.interfaces.MspClock',
            'org.contikios.cooja.mspmote.interfaces.MspMoteID',
            'org.contikios.cooja.interfaces.IPAddress',
            'org.contikios.cooja.mspmote.interfaces.SkyButton',
            'org.contikios.cooja.mspmote.interfaces.SkyFlash',
            'org.contikios.cooja.mspmote.interfaces.SkyCoffeeFilesystem',
            'org.contikios.cooja.mspmote.interfaces.Msp802154Radio',
            'org.contikios.cooja.mspmote.interfaces.MspSerial',
            'org.contikios.cooja.mspmote.interfaces.SkyLED',
            'org.contikios.cooja.mspmote.interfaces.MspDebugOutput',
            'org.contikios.cooja.mspmote.interfaces.SkyTemperature']

    @staticmethod
    def _get_java_class():
        return 'org.contikios.cooja.mspmote.SkyMoteType' 

    def compile_firmware(self, clean=False, verbose=False):
        return MoteType.compile_firmware(self, clean=clean, verbose=verbose)

Mote.platforms.append(SkyMote)
