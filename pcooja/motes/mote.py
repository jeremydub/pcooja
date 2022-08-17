import os
import shutil
import math
import uuid
from abc import ABC, abstractmethod

import logging
logger = logging.getLogger("pcooja")

class Mote:
    REGISTERED_PLATFORMS = []
    def __init__(self, id, x, y, mote_type=None, startup_delay=None, baseRSSI=-100.0):
        self.id = id
        
        self.x = x
        self.y = y
        self.z = 0

        self.nbr_count = 0

        self.mote_type = mote_type
        self.startup_delay = startup_delay
        self.baseRSSI = baseRSSI #Power Spectral Density of the noise

    def euclidian_distance(self, other):
        ''' Return the euclidian distance between the mote an an other mote. '''
        return math.sqrt(math.pow(self.x - other.x, 2) + \
                                         math.pow(self.y - other.y, 2) + \
                                         math.pow(self.z - other.z, 2))

    def to_xml(self, xb):
        xb.write('<mote>')
        xb.indent()
        #xb.write('<breakpoints />')
        self.interfaces_to_xml(xb)
        xb.write('<motetype_identifier>'+self.mote_type.identifier+'</motetype_identifier>')
        xb.unindent()
        xb.write('</mote>')

    @staticmethod
    def from_xml(xml, x, y, mote_type):
        for t in Mote.REGISTERED_PLATFORMS:
            mote = t.from_xml(xml, x, y, mote_type)
            if mote != None:
                return mote
        raise Exception("Unsupported Format for the mote " + xml.text)

    def interfaces_to_xml(self, xb):
        xb.write('<interface_config>')
        xb.indent()
        xb.write('org.contikios.cooja.interfaces.Position')
        xb.write('<x>'+str(self.x)+'</x>')
        xb.write('<y>'+str(self.y)+'</y>')
        xb.write('<z>'+str(self.z)+'</z>')
        xb.unindent()
        xb.write('</interface_config>')

    def basseRSSI_to_xml(self, xb):
        ''' write the base RSSI value (PSD of the noise) in the xml file '''
        if(self.baseRSSI != -100.0):
            xb.write('<BaseRSSIConfig Mote="'+str(self.id)+'">'+str(self.baseRSSI)+'</BaseRSSIConfig>')

    @staticmethod
    def basseRSSI_from_xml(xml, motes):
        """ 
            Return a list of mote with base RSSI
        """
        for baseRSSIConfig in xml.xpath("BaseRSSIConfig"):
                moteid = int(baseRSSIConfig.xpath("./@Mote")[0])
                baseRSSI = float(baseRSSIConfig.text)
                print("mote id" + str(moteid) + "baseRSSI" +str(baseRSSI))
                for mote in motes:
                    print("moteid " + str(mote.id))
                    if mote.id == moteid:
                        mote.baseRSSI = baseRSSI

    def __str__(self):
        return '[#'+str(self.id)+']('+str(self.x)+', '+str(self.y)+')'

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.nbr_count < other.nbr_count

    def __eq__(self, other):
        if type(self)==type(other):
            return self.x==other.x and self.y==other.y and self.z==other.z and self.id==other.id
        else:
            return False

class MoteType(ABC):
    REGISTERED_PLATFORMS = []
    def __init__(self, firmware_path, source_path=None, identifier=None, make_target=None, makefile_variables=None, description=None, compile_command=None, interfaces=None, environment_variables=None, project_conf=None):
        
        self.unique_id = self._generate_uuid()
        
        filename = firmware_path.split('/')[-1]
        if identifier == None:
            identifier = filename.split(".")[0]

        if description == None:
            description="Mote #"+identifier

        if make_target == None:
            make_target = identifier

        if source_path == None and compile_command == None and firmware_path == None:
            raise Exception(f"MoteType should at least have a 'source' (or 'firmware') XML tag " )
        
        if source_path == None and compile_command != None:
            raise Exception(f"MoteType: 'source' XML tag is present but 'command' XML tag is missing" )
        
        if firmware_path.endswith(".c") and source_path == None:
            source_path = firmware_path
            parts = firmware_path.split(".")[:-1]
            parts[-1] += f"-{self.unique_id}"
            firmware_path = ".".join(parts+[self._get_platform_target()])
            if identifier == None:
                identifier = f"{identifier}-{self.unique_id}"

        if environment_variables == None:
            environment_variables = {}

        if type(firmware_path) == str and firmware_path[0] != "/" and os.path.exists(firmware_path):
            firmware_path = os.path.abspath(firmware_path)

        if project_conf != None:
            parts = firmware_path.split('/')
            folder = "/".join(parts[:-1])
            project_conf.set_folder(folder)

        if makefile_variables == None:
            makefile_variables = {}

        self.identifier=identifier
        self.firmware_path=firmware_path
        self.source_path = source_path
        self.description = description
        self.make_target = make_target #target file
        self.makefile_variables = makefile_variables
        self.compile_command = compile_command
        self.environment_variables = environment_variables
        self.project_conf = project_conf

        all_interfaces = self._get_default_interfaces()

        if interfaces != None:
            for interface in interfaces:
                if interface not in all_interfaces:
                    all_interfaces.append(interface)

        self.interfaces = all_interfaces

    @staticmethod
    def _get_default_interfaces():
        return ['org.contikios.cooja.interfaces.Position',\
            'org.contikios.cooja.interfaces.RimeAddress',\
            'org.contikios.cooja.interfaces.Mote2MoteRelations',\
            'org.contikios.cooja.interfaces.MoteAttributes']

    @staticmethod
    @abstractmethod
    def _get_platform_target():
        raise NotImplementedError("A Mote type should implement this method")

    @staticmethod
    @abstractmethod
    def _get_java_class(self):
        raise NotImplementedError("A Mote type should implement this method")
    
    @staticmethod
    def _generate_uuid():
        return str(uuid.uuid4()).replace("-","")


    def __str__(self):
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        filename = parts[-1]
        return f'[{self.make_target}: {filename}]'

    def __repr__(self):
        return self.__str__()

    def to_xml(self, xb):
        xb.write('<motetype>')
        xb.indent()
        xb.write(self._get_java_class())
        xb.write(f'<identifier>{self.identifier}</identifier>')
        xb.write(f'<description>{self.description}</description>')
        xb.write(f'<symbols>false</symbols>')
        xb.write(f'<firmware EXPORT="copy">{self.firmware_path}</firmware>')
        for interface in self.interfaces:
            xb.write(f'<moteinterface>{interface}</moteinterface>')
        xb.unindent()
        xb.write('</motetype>')

    @staticmethod
    def from_xml(xml, configdir_path=None):
        mote_interfaces = xml.xpath("moteinterface/text()")
        identifier = xml.xpath("identifier/text()")
        description = xml.xpath("description/text()")
        firmware_path = xml.xpath("firmware/text()")
        source_path = xml.xpath("source/text()")
        commands = xml.xpath("commands/text()")
        java_class = str(xml.text).strip()

        compile_command = str(commands[0]) if len(commands) > 0 else None
        source_path = str(source_path[0]) if len(source_path) > 0 else None

        motetype_class = None
        for registered_platform in MoteType.REGISTERED_PLATFORMS:
            if registered_platform._get_java_class() == java_class:
                motetype_class = registered_platform
                break
        if motetype_class == None:
            raise Exception(f"Unsupported MoteType '{java_class}' " )


        platform_target = motetype_class._get_platform_target()

        mote_interfaces = list(map(lambda x: str(x), mote_interfaces))
        
        if firmware_path == []:
            firmware_path = ".".join(source_path.split(".")[:-1])+f".{platform_target}"
        else:
            firmware_path = firmware_path[0]
            

        if identifier == [] or description == [] or java_class == []:
            raise Exception("Bad Format for motetype tag")

        if configdir_path != None:
            firmware_path = firmware_path.replace('[CONFIG_DIR]', configdir_path)
        firmware_path = firmware_path.replace('[CONTIKI_DIR]', os.environ["CONTIKI_PATH"])

        mote_type = motetype_class(identifier=str(identifier[0]), source_path=source_path,\
                    firmware_path=firmware_path, interfaces=mote_interfaces,\
                    description=str(description[0]), compile_command=compile_command)
        return mote_type
        

    def firmware_exists(self):
        return os.path.exists(self.firmware_path)

    def is_compilable(self):
        return self.source_path != None or self.compile_command != None

    def compile_firmware(self, clean=False):
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        filename = parts[-1]
        
        target_arg = f"TARGET={self._get_platform_target()}"
        
        if not self.is_compilable():
            return True

        logger.info(f"Compiling Firmware for Mote Type {repr(self)}")

        if clean:
            logger.debug(f"Cleaning before compiling for Mote Type {repr(self)}")
            subcommand = f"make {target_arg} clean"
            os.system(f"cd {folder} && {subcommand}")
            logger.debug(f"  (shell) cd {folder}")
            logger.debug(f"  (shell) {subcommand}")
            subcommand = f"rm -f {filename} && rm -rf build/{self._get_platform_target()}"
            os.system(f"cd {folder} && {subcommand}")
            logger.debug(f"  (shell) {subcommand}")
        
        if self.firmware_exists() and self.compile_command == None:
            logger.debug(f"Firmware already exists for Mote Type {repr(self)}")
            return True
        
        self.check_makefile()

        if self.project_conf != None:
            self.project_conf.update_file()

        error_file = f"error_{self.unique_id}.log"

        command = f"cd {folder}"

        env = ""
        for key,value in self.environment_variables.items():
            env += f"{key}=\"{value}\" "
        for key,value in self.makefile_variables.items():
            env += f"{key}=\"{value}\" "
        
        if len(self.environment_variables) > 0:
            logger.debug(f"Environment variables : {env}")
        if self.compile_command != None:
            for subcommand in self.compile_command.split("\n"):
                command += f"&& {env} {subcommand}"
                logger.debug(f"  (shell, from <command/>) {subcommand}")
            command = command.replace("$(CPUS)", "4")
        else:
            subcommand = f"make {self.make_target} -j8 {target_arg}"
            command += f"&& {env} {subcommand}"
            for subcommand in command.split("&&")[1:]:
                logger.debug(f"  (shell) {subcommand}")

        command += f" 2> {error_file} > /dev/null"
        code = os.system(command)
        if self.project_conf != None:
            self.project_conf.restore_file()
        
        if code != 0:
            if os.path.exists(f"{folder}/{error_file}"):
                
                f = open(f"{folder}/{error_file}", "r")
                for line in f:
                    line = line.strip()
                    if "error" in line or "undefined" in line or "overflowed by" in line:
                        print("\033[38;5;1m"+line+"\033[0m")
                    else:
                        print("\033[93m"+line+"\033[0m")

                f.close()
                os.remove(f"{folder}/{error_file}")
            raise CompilationError("An error occured during firmware compilation")

        expected_firmware_location = os.path.abspath(f"{folder}/{self.get_expected_filename()}")
        if expected_firmware_location != self.firmware_path:
            logger.debug(f"Moving new firmware '{expected_firmware_location}' to '{self.firmware_path}'")
            os.rename(expected_firmware_location, self.firmware_path)
        os.remove(f"{folder}/{error_file}")
        return True

    def get_expected_filename(self):
        return f"{self.make_target}.{self._get_platform_target()}"

    def check_makefile(self):
        """
        Check contiki path in makefile
        """
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        makefile_path = f"{folder}/Makefile"

        if not os.path.exists(makefile_path):
            raise Exception(f"No Makefile found in application folder")

        with open(makefile_path, 'r') as f:
            for line in f:
                if line.startswith("CONTIKI="):
                    contiki_path=line.split("=")[1].strip()
                    if contiki_path[-1] != "/":
                        contiki_path += "/"
                    if contiki_path[0] != "/":
                        contiki_path = folder+"/"+contiki_path
                    if not os.path.exists(f"{contiki_path}Makefile.include"):
                        raise Exception(f"Makefile: Contiki path '{contiki_path}' does not exists")

    def save_firmware_as(self, filepath):
        if not self.firmware_exists():
            logger.debug(f"Firmware {self} does not exist yet, compiling...")
            result=self.compile_firmware()
        shutil.copy2(self.firmware_path, filepath)
        firmware_filename = self.firmware_path.split("/")[-1]
        #self.firmware_path=f"[CONFIG_DIR]/{firmware_filename}"
        logger.debug(f"Saved firmware {self} to file '{filepath}'")
    
    def remove_firmware(self):
        if self.firmware_exists():
            os.remove(self.firmware_path)
            logger.debug(f"Removed firmware {self.firmware_path}")

class CompilationError(Exception):
    pass
