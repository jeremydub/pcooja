import random
import datetime
import os
import os.path
import shutil
from lxml import etree
import subprocess
import copy
import multiprocessing
import tempfile
import threading
import traceback
import glob

from .motes.mote import CompilationError
from .topology import Topology
from .script.runner import ScriptRunner
from .script.timeout import TimeoutScript
from .script.load import LoadScript
from .radio import *
from .parser.csc import CSCParser

import logging
logger = logging.getLogger("pcooja")

class CoojaSimulation:
    CONTIKI_PATH = None
    def __init__(self, topology, seed=None, title="Simulation",\
                 timeout=600, debug_info={}, clean_firmwares=False):
        if seed == None:
            self.seed=random.randint(0,10000000)
        else:
            self.seed=seed
        self.topology=copy.deepcopy(topology)
        self.title=title
        self.timeout=timeout
        now=datetime.datetime.now()
        self.id=now.strftime("%Y%d%m_%H%M%S_") + hex(id(self))[2:]

        mote_types=[]
        for mote in topology:
            if mote.mote_type != None and mote.mote_type not in mote_types:
                mote_types.append(mote.mote_type)
        self.mote_types=mote_types
        
        # User-defined dictionary used for debugging or for later analysis
        self.debug_info=debug_info
        self.return_value=-1
        self.clean_firmwares = clean_firmwares
        
        self.set_script(TimeoutScript(self.timeout, with_gui=False))

    @staticmethod
    def set_contiki_path(path):
        if path[-1] == "/":
            path = path[:-1]
        contiki_exists = os.path.exists(f"{path}/Makefile.include")
        if contiki_exists:
            CoojaSimulation.CONTIKI_PATH = path
            os.environ["CONTIKI_PATH"] = path
            misc_path = os.path.abspath(f"{__file__}/../misc")
            #os.system(f'CONTIKI_PATH="{path}" MODULE_PATH="{misc_path}" sh {misc_path}/fix_cooja.sh')
        else:
            raise SettingsError(f"Path '{path}' does not exist or is not a valid Contiki folder")

    @staticmethod
    def get_contiki_path():
        if CoojaSimulation.CONTIKI_PATH == None:
            contiki_path = "/home/user/contiki"
            contiki_exists = os.path.exists(f"{contiki_path}/Makefile.include")
            if contiki_exists:
                CoojaSimulation.CONTIKI_PATH = contiki_path
            else:
                raise SettingsError("Contiki Not Found")
        return CoojaSimulation.CONTIKI_PATH
            
    def set_script(self, script_runner):
        """ Change the default script file """
        self.script_runner = script_runner

    def run(self, log_file=None, pcap_file=None, filename_prefix=None, enable_log=True, \
                enable_pcap=True, remove_csc=True, folder="data"):
        code = -1
        segfault = False

        temp_dir = f"{tempfile.gettempdir()}/cooja_sim_{self.id}/"
        os.makedirs(temp_dir)

        try:
            csc_filepath = f"{temp_dir}{self.id}.csc"
            self.check_settings()
            CSCParser.export_simulation(self, csc_filepath, enable_log, enable_pcap)
            absolute_path=os.path.abspath(csc_filepath)

            contiki_path = self.get_contiki_path()

            command=f"cooja --args='-nogui=\"{absolute_path}\" -contiki=\"{contiki_path}\" -logdir=\"{temp_dir}\"'"

            origin_pcap_file = None
            test_failed = False

            logger.info("Starting Simulation")
            logger.debug(f" - Title : {self.title}")
            logger.debug(f" - Random seed : {self.seed}")
            logger.debug(f" - # nodes : {len(self.topology.motes)}")

            p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            if logger.level <= logging.INFO:
                time_remaining = ""
                progress = "Starting..."
                for line in iter(p.stdout.readline, ''):
                    if not line :
                        break
                    else:
                        line = line.decode().strip()
                        if "% completed, " in line:
                            parts = line.split("completed, ")
                            time_remaining = " | "+ parts[1].split()[0]+" sec"
                            progress = parts[0].split()[-1]
                        elif "Simulated time" in line:
                            progress = "100%"
                            time_remaining = ""
                            logger.info(f"{self.title}   [{progress}{time_remaining}]             \r")
                            break
                        elif "Script timeout in" in line:
                            progress = "0%"
                            time_remaining = ""
                        elif "Opened pcap file" in line:
                            origin_pcap_file = f"{contiki_path}/tools/cooja/{line.split()[-1]}"
                        elif "Segmentation fault" in line or "Java Result: 139" in line:
                            segfault = True
                        elif "TEST FAILED" in line:
                            test_failed = True
                    logger.info(f"{self.title}   [{progress}{time_remaining}]             \r")
                p.stdout.close()
                logger.info("")
            code=p.wait()
            self.return_value=code
            segfault = segfault or code == 139 or code == 134

            if self.has_suceed() or segfault or test_failed:
                if test_failed:
                    logger.warn("Simulator script resulted in FAILED TEST")
                if folder != None and folder != "":
                    if not os.path.exists(folder) and (log_file == None or pcap_file == None) :
                        os.makedirs(folder)
                    if folder[-1] != "/":
                        folder += "/"
                else:
                    folder = ""
                prefix = folder
                if filename_prefix != None:
                    prefix += str(filename_prefix)
                if enable_log:
                    if log_file == None:
                        log_file = f"{prefix}{self.id}.log"

                    self.log_file=log_file
                    log_file_folder = "/".join(log_file.split("/")[:-1])
                    if log_file_folder != '' and not os.path.exists(log_file_folder):
                        os.makedirs(log_file_folder)
                    shutil.copy(f"{temp_dir}COOJA.testlog",log_file)
                    logger.debug(f"Saved COOJA.testlog to {log_file}")

                if enable_pcap:
                    if pcap_file == None:
                        pcap_file = f"{prefix}{self.id}.pcap"
                    if origin_pcap_file != None and os.path.exists(origin_pcap_file):
                        self.pcap_file=pcap_file
                        pcap_file_folder = "/".join(pcap_file.split("/")[:-1])
                        if pcap_file_folder != '' and  not os.path.exists(pcap_file_folder):
                            os.makedirs(pcap_file_folder)
                        shutil.copy(origin_pcap_file,pcap_file)
                        logger.debug(f"Saved captured packets to {pcap_file}")
                    elif origin_pcap_file == None:
                        logger.warning(f"Pcap file was not provided by Cooja")
                    else:
                        logger.warning(f"Could not find {origin_pcap_file}")
            else:
                if os.path.exists(f"{temp_dir}/COOJA.log"):
                    print("\033[38;5;1m")
                    os.system(f"cat {temp_dir}/COOJA.log")
                    print("\033[0m")
        except CompilationError as e:
            print(e)
        except SettingsError as e:
            print(e)
        except Exception as e:
            traceback.print_exc()
        finally:
            if segfault:
                self.handle_segfault()
                segfault_folder = f"simulation-segfault-{hex(id(self))[2:]}"
                #print(f"\033[38;5;1mSegmentation Fault occured during simulation ! Simulation has been exported in './{segfault_folder}' for further analysis.\033[0m")
                #self.export(segfault_folder)
            if remove_csc and self.has_suceed():
                os.remove(csc_filepath)
            for mote_type in self.mote_types:
                if mote_type.is_compilable():
                    mote_type.remove_firmware()
            shutil.rmtree(temp_dir)

            return code

    def run_with_gui(self):
        
        if self.script_runner == None:
            self.script_runner = TimeoutScript(self.timeout, with_gui=False)

        temp_folder = f"{tempfile.gettempdir()}/cooja_sim_{hex(id(self))[2:]}/"
        try:
            self.export(temp_folder, gui_enabled=True)
            absolute_path=os.path.abspath(f"{temp_folder}/simulation.csc")

            contiki_path = self.get_contiki_path()
            command=f"cd {temp_folder} && cooja --args='-quickstart=\"{absolute_path}\" -contiki=\"{contiki_path}\"'"
            command +=" 2> /dev/null > /dev/null"
            os.system(command)
        except CompilationError as e:
            print(e)
        except SettingsError as e:
            print(e)
        finally:
            shutil.rmtree(temp_folder)

    def handle_segfault(self):
        logger.debug(f"Handling segmentation fault")
        try:
            with open("/proc/sys/kernel/core_pattern", "r") as f:
                content = f.read().strip()
        except Exception as e:
            content = ""
        
        if content == "":
            return
        
        now = datetime.datetime.now().timestamp()
        coredumps = glob.glob(f"{content}*")
        coredumps.sort(key=lambda path: now-os.path.getmtime(path))
        if len(coredumps) == 0:
            logger.warning(f"Did not find core dump")
            return

        creation_date = os.path.getmtime(coredumps[0])
        age = now-creation_date
        if age > 10:
            logger.warning(f"Core dump is too old. Probably not ours ..")
            return

        firmware = self.mote_types[0].firmware_path
        command = f"gdb -batch -ex bt {firmware} {coredumps[0]} | grep '#'"
        print("\033[33m")
        os.system(command)
        print("\033[0m")

    def check_settings(self):
        errors = []
        for mote in self.topology:
            if mote.mote_type == None:
                errors.append(f"Mote #{mote.id} has no mote type")

        if len(errors) > 0:
            raise SettingsError("\n".join(errors))

        # Check mote type and firmware
        for mote_type in self.mote_types:
            if not mote_type.firmware_exists() or mote_type.compile_command != None or self.clean_firmwares:
                if mote_type.is_compilable():
                    compiled = mote_type.compile_firmware(clean=self.clean_firmwares)
                    if not compiled:
                        errors.append(f"Firmware '{mote_type.firmware_path}' did not compile correctly")
                if not mote_type.firmware_exists():
                    errors.append(f"Firmware '{mote_type.firmware_path}' does not exist")

        if len(errors) > 0:
            raise SettingsError("\n".join(errors))

    def has_suceed(self):
        return self.return_value==0

    def get_log_filepath(self):
        if self.has_suceed:
            return self.log_file
        else:
            return None

    def get_pcap_filepath(self):
        if self.has_suceed:
            return self.pcap_file
        else:
            return None

    def set_pcap_log_file(self, file_name):
        """ Set the pcap and log file to overpass the run step
        The file name containt the folder for exemple:
        file_name should be like ""data/simulation_20171003_150539_7f99d23f3b48"
        """
        self.pcap_file = f"{file_name}.pcap"
        self.log_file = f"{file_name}.log"
        self.return_value = 0


    def export(self, folder=None, gui_enabled=False):
        if folder == None:
            folder = f"simulation_{self.id}"

        if folder[-1] == "/":
            folder = folder[:-1]

        if not os.path.exists(folder):
            os.makedirs(folder)

        self.check_settings()

        sim = copy.deepcopy(self)

        logger.info(f"Exporting simulation in '{folder}/' ...")

        i=0
        for i in range(len(self.mote_types)):
            firmware_filename = self.mote_types[i].firmware_path.split("/")[-1]
            new_path = f"{folder}/{firmware_filename}"
            self.mote_types[i].save_firmware_as(new_path)

        logger.info("Saving simulation as Cooja file (.csc)")
        CSCParser.export_simulation(sim, f"{folder}/simulation.csc", gui_enabled=gui_enabled)


    @staticmethod
    def from_csc(csc_path):
        """
        Parse a Cooja simulation configuration (.csc) file
        """
        
        if not os.path.exists(csc_path):
            raise OSError(f"File '{csc_path}' does not exist")
        tree = etree.parse(csc_path)
        simulation_tag=tree.xpath("/simconf/simulation")[0]

        # Details
        title = simulation_tag.xpath("title/text()")
        random_seed = simulation_tag.xpath("randomseed/text()")[0]
        if random_seed != "generated":
            random_seed = int(random_seed)
        motedelay_us = simulation_tag.xpath("motedelay_us/text()")

        topology = Topology.from_xml(tree, csc_path)
        
        plugin_tags=tree.xpath("/simconf/plugin")

        script = None
        for plugin_tag in plugin_tags:
            name = plugin_tag.xpath("text()")[0].strip()
            if name == "org.contikios.cooja.plugins.ScriptRunner":
                res = plugin_tag.xpath("plugin_config/script/text()")
                if len(res) > 0:
                    script_content = plugin_tag.xpath("plugin_config/script/text()")[0]
                    script = LoadScript(None, script=script_content)
                else:
                    script_file = plugin_tag.xpath("plugin_config/scriptfile/text()")[0]
                    parts = csc_path.split('/')
                    folder = "/".join(parts[:-1])
                    script_file = script_file.replace('[CONFIG_DIR]', folder)
                    script = LoadScript(None, script_file=script_file)
                break
        simulation = CoojaSimulation(topology=topology, seed=random_seed)
        if script != None:
            simulation.set_script(script)

        return simulation

    def __repr__(self):
        duration = str(self.timeout)
        if self.timeout / 60 == 0:
            duration += "sec"
        else :
            duration = f"{self.timeout/60}min"
        return f"\"{self.title}\" : {len(self.topology)} motes, duration={duration}"


class CoojaSimulationWorker:
    def __init__(self, n_thread=None, callback=None):
        if n_thread == None:
            n_thread = multiprocessing.cpu_count()
        self.n_thread = n_thread
        self.callback = callback
        self.simulations = []

        # dictionary that associate a simulation id to its run() arguments
        self.id_to_args={}

    def add_simulation(self,simulation, run_args={}):
        if isinstance(simulation,CoojaSimulation):
            self.simulations.append(simulation)

            self.id_to_args[id(simulation)] = run_args

    def run(self):

        # Check settings and compile firmware before threads start
        for simulation in self.simulations:
            simulation.check_settings()

        self.simulations.sort(key=lambda x : int(10.**6*len(x.topology)/x.timeout))

        simulations_per_thread = []
        for i in range(self.n_thread):
            simulations_per_thread.append([])

        i = 0
        for simulation in self.simulations:
            simulations_per_thread[i%self.n_thread].append(simulation)
            i += 1

        threads=[]

        def target(thread_number):
            for simulation in simulations_per_thread[thread_number]:
                kwargs=self.id_to_args[id(simulation)]
                simulation.run(**kwargs)
                if self.callback != None:
                    self.callback(simulation)

        for i in range(self.n_thread):
            thread = threading.Thread(target=target, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.simulations = []

class SettingsError(Exception):
    pass
