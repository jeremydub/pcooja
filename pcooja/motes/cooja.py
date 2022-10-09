from pcooja.motes.mote import Mote, MoteType
import os
import shutil

import logging
logger = logging.getLogger("pcooja")

class CoojaMote(Mote):
    """ The biterate is in kbps """
    def __init__(self, id, x, y, mote_type=None, startup_delay=None, bitrate=250.0):
        Mote.__init__(self, id, x, y, mote_type, startup_delay)
        self.bitrate = bitrate

    def interfaces_to_xml(self, xb):
        Mote.interfaces_to_xml(self, xb)
        xb.write(f'''
        <interface_config>
            org.contikios.cooja.contikimote.interfaces.ContikiMoteID
            <id>{self.id}</id>
        </interface_config>''')
        if type(self.startup_delay) == int or type(self.startup_delay) == float :
            xb.write(f'''
            <interface_config>
                org.contikios.cooja.mspmote.interfaces.ContikiClock
                <startup_delay_ms>{int(self.startup_delay)}</startup_delay_ms>
            </interface_config>''')

        xb.write(f'''
        <interface_config>
            org.contikios.cooja.contikimote.interfaces.ContikiRadio
            <bitrate>{self.bitrate}</bitrate>
        </interface_config>
        <interface_config>
            org.contikios.cooja.contikimote.interfaces.ContikiEEPROM
            <eeprom>{'A'*1366}==</eeprom>
        </interface_config>''')

    @staticmethod
    def get_type():
        return "cooja"
        
    @staticmethod
    def from_xml(xml, x, y, mote_type):
        if mote_type._get_java_class() != CoojaMoteType._get_java_class():
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
    def __init__(self, firmware_path, **kwargs):
        kwargs["environment_variables"] = {
                'CC':'gcc',
                'LD':'ld',
                'OBJCOPY':'objcopy',
                'AR':'ar',
        }
        super().__init__(firmware_path, **kwargs)
            
        self.map_file = ".".join(self.firmware_path.split(".")[:-1]+["map"])

        if not self.is_compilable():
            if self.map_file == None or not os.path.exists(self.map_file):
                raise Exception("Cooja MoteType firmware is missing an associated MAP file")
        if self.firmware_exists():
            self.environment_variables["CLASSNAME"] = self._extract_classname_in_map_file()
        else:
            self.environment_variables["CLASSNAME"] = f"Lib{self.unique_id}"
        libname = f"mtype{self.unique_id}"
        self.environment_variables["CONTIKI_APP"] = self.make_target
        self.environment_variables["LIBNAME"] = f"build/cooja/{libname}.cooja"
        # TODO: retrieve version
        self.environment_variables["COOJA_VERSION"] = "2022052601"
    
    def _extract_classname_in_map_file(self):
        with open(self.map_file, "r") as f:
            for line in f:
                if "Java_org_contikios_cooja_corecomm_" in line:
                    classname = line.split("_")[-2]
                    break
        return classname

    
    def to_xml(self, xb):
        super().to_xml(xb)
        xb.undo()
        xb.indent()
        xb.write(f'''
        <mapfile>{self.map_file}</mapfile>
        <javaclassname>{self.environment_variables["CLASSNAME"]}</javaclassname>''')
        xb.unindent()
        xb.write('</motetype>')

    def compile_firmware(self, clean=False):
        success = MoteType.compile_firmware(self, clean=clean)    
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        built_map_file = f"{folder}/{self.environment_variables['LIBNAME'][:-6]}.map"
        if success and os.path.exists(built_map_file):
            source = built_map_file
            destination = self.map_file
            try:
                os.rename(source, destination)
            except OSError as e:
                shutil.copy2(source, destination)
                os.remove(source)
        return success

    def firmware_exists(self):
        return super().firmware_exists() and \
               self.map_file != None and \
               os.path.exists(self.map_file) 
 
    def save_firmware_as(self, filepath):
        super().save_firmware_as(filepath)
        dest_map_file = ".".join(filepath.split(".")[:-1]+["map"])
        map_filename = dest_map_file.split("/")[-1]
        if os.path.exists(filepath) and os.path.exists(self.map_file):
            source = self.map_file
            destination = dest_map_file
            try:
                os.rename(source, destination)
            except OSError as e:
                shutil.copy2(source, destination)
                os.remove(source)
            logger.debug(f"Saved associated MAP file to file '{dest_map_file}'")
            self.map_file = os.path.abspath(dest_map_file)
    
    def remove_firmware(self):
        super().remove_firmware()
        map_file = ".".join(self.firmware_path.split(".")[:-1]+["map"])
        if os.path.exists(map_file):
            os.remove(map_file)

    def get_expected_filename(self):
        return self.environment_variables['LIBNAME']
    
    @staticmethod
    def _get_platform_target():
        return "cooja"

    @staticmethod
    def _get_default_interfaces():
        return MoteType._get_default_interfaces()+\
            ['org.contikios.cooja.interfaces.Battery',
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

    @staticmethod
    def _get_java_class():
        return 'org.contikios.cooja.contikimote.ContikiMoteType' 

Mote.REGISTERED_PLATFORMS.append(CoojaMote)
MoteType.REGISTERED_PLATFORMS.append(CoojaMoteType)
