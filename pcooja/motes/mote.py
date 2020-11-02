import os
#import sys
#sys.path.insert(0, '../')
#from cooja_tools import *
#from Simulation import *
import shutil
import math



class Mote:
    Types = []
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
        for t in Mote.Types:
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

class MoteType:
    class_counter = 0
    def __init__(self, firmware_path, identifier, java_class, platform_target, make_target=None, interfaces=[], description=None, firmware_command=None, firmware_copy=True, symbols=True):
        filename = firmware_path.split('/')[-1]
        if identifier == None:
            identifier = filename.split(".")[0]

        if description == None:
            description="Mote #"+identifier

        if make_target == None:
            make_target = filename

        if type(firmware_path) == str and firmware_path[0] != "/" and os.path.exists(firmware_path):
            firmware_path = os.path.abspath(firmware_path)

        self.identifier=identifier
        self.java_class=java_class
        self.firmware_path=firmware_path
        self.description = description
        self.platform_target = platform_target #target platform
        self.make_target = make_target #target file
        self.firmware_command = firmware_command
        self.firmware_copy = firmware_copy
        self.symbols=symbols

        common_interfaces=['org.contikios.cooja.interfaces.Position',\
            'org.contikios.cooja.interfaces.RimeAddress',\
            'org.contikios.cooja.interfaces.Mote2MoteRelations',\
            'org.contikios.cooja.interfaces.MoteAttributes']

        self.interfaces=common_interfaces+interfaces

    def __str__(self):
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        filename = parts[-1]
        return '['+self.identifier+': '+filename+']'

    def __repr__(self):
        return self.__str__()

    def to_xml(self, xb):
        xb.write('<motetype>')
        xb.indent()
        xb.write(self.java_class)
        xb.write('<identifier>'+self.identifier+'</identifier>')
        xb.write('<description>'+self.description+'</description>')
        if self.firmware_copy:
            # xb.write('<source EXPORT="discard">'+self.firmware_path[0:-len(self.target)]+'c</source>')
            # xb.write('<commands EXPORT="discard">make '+self.make_target+' TARGET='+ self.target +'</commands>')
            xb.write('<firmware EXPORT="copy">'+self.firmware_path+'</firmware>')
        else:
            xb.write('<source>'+self.firmware_path[0:-len(self.platform_target)]+'c</source>')
            xb.write('<commands>make '+self.make_target+' TARGET='+ self.platform_target +'</commands>')
        for interface in self.interfaces:
            xb.write('<moteinterface>'+interface+'</moteinterface>')
        if not self.symbols:
            xb.write('<symbols>false</symbols>')
        xb.unindent()
        xb.write('</motetype>')

    def firmware_exists(self):
        return os.path.exists(self.firmware_path)

    def compile_firmware(self, make_options="", clean=False, verbose=False, target=None):
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        filename = parts[-1]

        target_command = ""
        if(self.platform_target != None):
            target_command = "TARGET="+self.platform_target+ " "

        if self.check_makefile():
            if clean:
                os.system("cd "+folder+" && rm -f "+filename+" && rm -r obj*/")
            
            error_file = "error_"+hex(id(self))[2:]+"_"+str(MoteType.class_counter)+".log"
            MoteType.class_counter += 1

            command = "cd "+folder+""
            if clean:
                #command+=" && make clean "+ target_command+ "2> /dev/null > /dev/null"
                command+=" && make clean 2> /dev/null > /dev/null"
            if verbose:
                print("Compiling Firmware for Mote Type "+repr(self))
            if self.firmware_command != None:
                command += " && " + self.firmware_command
            else:
                command += " && make "+self.make_target+" -j8 "+ target_command + make_options
            command = command + " 2> "+error_file+" > /dev/null"
            code = os.system(command)
            if code != 0:
                if os.path.exists(folder+"/"+error_file):
                    
                    f = open(folder+"/"+error_file, "r")
                    for line in f:
                        line = line.strip()
                        if "error" in line or "undefined" in line or "overflowed by" in line:
                            print("\033[38;5;1m"+line+"\033[0m")
                        else:
                            print("\033[93m"+line+"\033[0m")

                    f.close()
                    os.remove(folder+"/"+error_file)
                raise CompilationError("An error occured during firmware compilation")
            os.remove(folder+"/"+error_file)
            return code == 0

        return self.firmware_exists()

    def check_makefile(self):
        """
        Check contiki path in makefile
        """
        parts = self.firmware_path.split('/')
        folder = "/".join(parts[:-1])
        makefile_path = folder+"/Makefile"

        valid = True

        if os.path.exists(makefile_path):
            f = open(makefile_path,'r')
            
            #content = []

            for line in f:
                if line.startswith("CONTIKI="):
                    contiki_path=line.split("=")[1].strip()
                    if contiki_path[-1] != "/":
                        contiki_path += "/"
                    if contiki_path[0] != "/":
                        contiki_path = folder+"/"+contiki_path
                    if not os.path.exists(contiki_path+"Makefile.include"):
                        valid = False
            f.close()
        else:
            valid=False

        return valid

    def save_firmware_as(self, filepath, verbose=False):
        if not self.firmware_exists():
            result=self.compile_firmware(verbose=verbose)
            if result:
                shutil.copy2(self.firmware_path, filepath)
        else:
            shutil.copy2(self.firmware_path, filepath)

    def get_firmware_copy(self):
        """ Return if the firmware is compiled outside of cooja and after that copied inside the simulation or compiled by cooja based on the .csc file"""
        return self.firmware_copy

class CompilationError(Exception):
    pass
