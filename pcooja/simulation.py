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
import time
import queue
from rich.progress import Progress

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
    COUNTER = 0
    def __init__(self, topology, title=None, seed=None,\
                 timeout=600, debug_info={}):
        if seed == None:
            self.seed=random.randint(0,10000000)
        else:
            self.seed=seed

        self.topology=copy.deepcopy(topology)
        self.timeout=timeout
        self._generate_id()
        if title == None:
            title = self.id
        self.title=title

        # Temporary directory used for exporting configuration file and firmwares
        self.temp_dir = f"{tempfile.gettempdir()}/cooja_sim_{self.id}/"

        mote_types=[]
        for mote in topology:
            if mote.mote_type != None and mote.mote_type not in mote_types:
                mote_types.append(mote.mote_type)
        self.mote_types=mote_types
        
        # User-defined dictionary used for debugging or for later analysis
        self.debug_info=debug_info
        
        self.set_script(TimeoutScript(self.timeout, with_gui=False))
        
        self.log_filepath = None
        self.pcap_filepath = None
        self.test_failed = False
        self.segfaulted = False
        self.return_value=-1


        self.progress_bar_handler = None
        self.progress_bar_task = None

    def _generate_id(self):
        CoojaSimulation.COUNTER += 1
        now=datetime.datetime.now()
        self.id=f"{now.strftime('%Y%d%m_%H%M%S')}-{CoojaSimulation.COUNTER}"
            
    def set_script(self, script_runner):
        """ Change the default script file """
        self.script_runner = script_runner

    def run(self, log_file=None, pcap_file=None, enable_log=True, 
            enable_pcap=False, with_gui=False, export=True):
        if self.script_runner == None:
            self.script_runner = TimeoutScript(self.timeout, with_gui=with_gui)
        if log_file == None:
            log_file = f"{self.title}.log"
        if pcap_file == None:
            pcap_file = f"{self.title}.pcap"
        try:
            if export:
                self.export(self.temp_dir, gui_enabled=with_gui, 
                            enable_log=enable_log, enable_pcap=enable_pcap)
            
            if self.progress_bar_handler == None:
                logger.info("Starting Simulation")
                logger.debug(f" - Title : {self.title}")
                logger.debug(f" - Random seed : {self.seed}")
                logger.debug(f" - # nodes : {len(self.topology.motes)}")

                with Progress(refresh_per_second=2) as progress:
                    self.progress_bar_handler = progress
                    self.progress_bar_task = progress.add_task(f"[orange]{self.title} : Waiting", total=100)
                    self._run_command(with_gui=with_gui)
            else:
                self._run_command(with_gui=with_gui)

            if self.has_succeeded() or self.segfaulted or self.test_failed:
                if self.test_failed:
                    logger.warn("Simulator script resulted in FAILED TEST")
                if enable_log:
                    self.log_filepath=log_file
                    log_file_folder = "/".join(log_file.split("/")[:-1])
                    if log_file_folder != '' and not os.path.exists(log_file_folder):
                        os.makedirs(log_file_folder)
                    source = f"{self.temp_dir}COOJA.testlog"
                    if os.path.exists(source):
                        destination = log_file
                        try:
                            os.rename(source, destination)
                        except OSError as e:
                            shutil.copy2(source, destination)
                            os.remove(source)
                        logger.debug(f"Saved COOJA.testlog to {log_file}")
                if enable_pcap:
                    if self.pcap_filepath != None and os.path.exists(self.pcap_filepath):
                        pcap_file_folder = "/".join(pcap_file.split("/")[:-1])
                        if pcap_file_folder != '' and  not os.path.exists(pcap_file_folder):
                            os.makedirs(pcap_file_folder)
                        source = self.pcap_filepath
                        destination = pcap_file
                        try:
                            os.rename(source, destination)
                        except OSError as e:
                            shutil.copy2(source, destination)
                            os.remove(source)
                        logger.debug(f"Saved captured packets to {pcap_file}")
                    elif self.pcap_filepath == None:
                        logger.warning(f"Pcap file was not provided by Cooja")
                    else:
                        logger.warning(f"Could not find {self.pcap_filepath}")
            else:
                if os.path.exists(f"{self.temp_dir}/COOJA.log"):
                    print("\033[38;5;1m")
                    os.system(f"cat {self.temp_dir}/COOJA.log")
                    print("\033[0m")
        except CompilationError as e:
            print(e)
        except SettingsError as e:
            print(e)
        except Exception as e:
            traceback.print_exc()
        finally:
            self._handle_segfault()
            for mote_type in self.mote_types:
                if mote_type.is_compilable():
                    mote_type.remove_firmware()
            shutil.rmtree(self.temp_dir)

            return self.return_value

    def _run_command(self, with_gui=False):
        contiki_path = self.get_contiki_path()
        cooja_mode = "quickstart" if with_gui else "nogui"
        command=f"cooja --args='-{cooja_mode}=\"{self.csc_filepath}\" -contiki=\"{contiki_path}\" -logdir=\"{self.temp_dir}\"'"

        self.progress_bar_handler.update(self.progress_bar_task,
                                         description = f"{self.title} | [yellow]Starting")

        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)

        for line in iter(p.stdout.readline, ''):
            if not line :
                break
            else:
                line = line.decode().strip()
                if "% completed, " in line:
                    parts = line.split("completed, ")
                    time_remaining = parts[1].split()[0]
                    progress = int(parts[0].split()[-1][:-1])
                    self.progress_bar_handler.update(self.progress_bar_task, completed=progress,
                                                     description = f"{self.title} | [cyan]Running")
                elif "Script timeout in" in line:
                    progress = 0
                    self.progress_bar_handler.update(self.progress_bar_task, completed=progress,
                                                     description = f"{self.title} | [cyan]Running")
                elif "Opened pcap file" in line:
                    self.pcap_filepath = f"{contiki_path}/tools/cooja/{line.split()[-1]}"
                elif "Segmentation fault" in line or "Java Result: 139" in line:
                    self.segfaulted = True
                elif "TEST FAILED" in line:
                    progress = 100
                    self.test_failed = True
                elif "TEST OK" in line:
                    progress = 100
                    break
                elif "BUILD SUCCESSFUL" in line:
                    break
        p.stdout.close()

        description = f"{self.title}"
        if progress == 100:
            description += " | [green]Completed" 
        else:
            description += " | [yellow]Aborted" 
        self.progress_bar_handler.update(self.progress_bar_task, completed=progress,
                                         description = description)

        self.return_value=p.wait()
        self.segfaulted = self.segfaulted or self.return_value == 139 or self.return_value == 134
        self.progress_bar_handler.update(self.progress_bar_task, completed=100)

        if self.segfaulted:
            description = f"{self.title} | [red]SEGFAULT"
            self.progress_bar_handler.update(self.progress_bar_task, description=description)
        elif self.test_failed:
            description = f"{self.title} | [red]Test failed"
            self.progress_bar_handler.update(self.progress_bar_task, description=description)

    def _handle_segfault(self):
        if not self.segfaulted:
            return
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

        segfault_folder = f"simulation-segfault-{hex(id(self))[2:]}"
        #print(f"\033[38;5;1mSegmentation Fault occured during simulation ! Simulation has been exported in './{segfault_folder}' for further analysis.\033[0m")
        #self.export(segfault_folder)

    def check_settings(self):
        errors = []
        for mote in self.topology:
            if mote.mote_type == None:
                errors.append(f"Mote #{mote.id} has no mote type")
        # Check that firmwares exist
        for mote_type in self.mote_types:
            if not mote_type.firmware_exists():
                errors.append(f"Firmware '{mote_type.firmware_path}' does not exist")
        if len(errors) > 0:
            for error in errors:
                logger.error(error)
            raise SettingsError("\n".join(errors))

    def has_succeeded(self):
        return self.return_value==0

    def get_log_filepath(self):
        if self.has_succeeded:
            return self.log_filepath
        else:
            return None

    def get_pcap_filepath(self):
        if self.has_succeeded:
            return self.pcap_filepath
        else:
            return None

    def export(self, folder=None, gui_enabled=False, enable_log=True, enable_pcap=False):
        if folder == None:
            folder = self.temp_dir

        logger.info(f"Exporting simulation in '{folder}/' ...")

        if not os.path.exists(folder):
            os.makedirs(folder)

        errors = []
        for mote_type in self.mote_types:
            if mote_type.is_compilable():
                compiled = mote_type.compile_firmware(clean=True)
                if compiled:
                    firmware_filename = mote_type.firmware_path.split("/")[-1]
                    new_path = f"{folder}/{firmware_filename}"
                    mote_type.save_firmware_as(new_path)
                else:
                    errors.append(f"Firmware '{mote_type.firmware_path}' did not compile correctly")
        if len(errors) > 0:
            for error in errors:
                logger.error(error)
            raise SettingsError("\n".join(errors))

        self.check_settings()
        logger.debug("Saving simulation as Cooja file (.csc)")
        self.csc_filepath = os.path.abspath(f"{folder}/simulation.csc")
        CSCParser.export_simulation(self, self.csc_filepath, 
                                    gui_enabled=gui_enabled, 
                                    enable_log=enable_log, 
                                    enable_pcap=enable_pcap)

    def __repr__(self):
        duration = str(self.timeout)
        if self.timeout / 60 == 0:
            duration += "sec"
        else :
            duration = f"{self.timeout/60}min"
        return f"\"{self.title}\" : {len(self.topology)} motes, duration={duration}"

    @staticmethod
    def from_csc(csc_filepath):
        """
        Parse a Cooja simulation configuration (.csc) file
        """
        
        if not os.path.exists(csc_filepath):
            raise OSError(f"File '{csc_filepath}' does not exist")
        tree = etree.parse(csc_filepath)
        simulation_tag=tree.xpath("/simconf/simulation")[0]

        # Details
        title = simulation_tag.xpath("title/text()")
        random_seed = simulation_tag.xpath("randomseed/text()")[0]
        if random_seed != "generated":
            random_seed = int(random_seed)
        motedelay_us = simulation_tag.xpath("motedelay_us/text()")

        topology = Topology.from_xml(tree, csc_filepath)
        
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
                    parts = csc_filepath.split('/')
                    folder = "/".join(parts[:-1])
                    script_file = script_file.replace('[CONFIG_DIR]', folder)
                    script = LoadScript(None, script_file=script_file)
                break
        simulation = CoojaSimulation(topology=topology, seed=random_seed)
        if script != None:
            simulation.set_script(script)
        simulation.csc_filepath = os.path.abspath(csc_filepath)

        return simulation

    @staticmethod
    def set_contiki_path(path):
        if path[-1] == "/":
            path = path[:-1]
        contiki_exists = os.path.exists(f"{path}/Makefile.include")
        if contiki_exists:
            CoojaSimulation.CONTIKI_PATH = path
            os.environ["CONTIKI_PATH"] = path
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

            # Do not export (and compile firmwares) again since
            # we already export before running when using worker
            run_args["export"] = False

            self.id_to_args[id(simulation)] = run_args

    def run(self):

        for simulation in self.simulations:
            simulation.export()

        self.simulations.sort(key=lambda x : int(10.**6*len(x.topology)/x.timeout))

        simulations_queue = queue.Queue()

        for simulation in self.simulations:
            simulations_queue.put(simulation)

        threads=[]

        def target(thread_number):
            try:
                while True:
                    simulation = simulations_queue.get_nowait()
                    kwargs=self.id_to_args[id(simulation)]
                    simulation.run(**kwargs)
                    if self.callback != None:
                        self.callback(simulation)
            except queue.Empty as e:
                pass

        for i in range(self.n_thread):
            thread = threading.Thread(target=target, args=(i,))
            threads.append(thread)
    
        with Progress(refresh_per_second=2) as progress:
            for simulation in self.simulations:
                simulation.progress_bar_handler = progress
                simulation.progress_bar_task = progress.add_task(f"{simulation.title}", total=100)
            for thread in threads:
                thread.start()
                time.sleep(0.1)
            while not progress.finished:
                time.sleep(1)

        for thread in threads:
            thread.join()

class SettingsError(Exception):
    pass
