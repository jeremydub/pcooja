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

from .motes.mote import CompilationError
from .topology import Topology
from .script.runner import ScriptRunner
from .script.timeout import TimeoutScript
from .radio import *
from .parser.csc import CSCParser

class CoojaSimulation:
    CONTIKI_PATH = None
    def __init__(self, topology, seed=None, title="Simulation",\
                 timeout=60, debug_info={}):
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
            raise SettingsError("Contiki Not Found")

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
                enable_pcap=True, remove_csc=True, verbose=False, folder="data"):
        code = -1

        temp_dir = f"{tempfile.gettempdir()}/cooja_sim_{hex(id(self))[2:]}/"
        os.makedirs(temp_dir)

        try:
            csc_filepath = f"{temp_dir}{self.id}.csc"
            self.check_settings(verbose)
            CSCParser.export_simulation(self, csc_filepath, enable_log, enable_pcap)
            absolute_path=os.path.abspath(csc_filepath)

            contiki_path = self.get_contiki_path()

            jar_location = f"{contiki_path}/tools/cooja/dist/"

            # -Xshare:on is add for the CoojaMote support 
            # https://github.com/contiki-os/contiki/issues/2324
            command=f"cd {temp_dir} && java -Xshare:on -Dnashorn.args=--no-deprecation-warning -mx512m -jar {jar_location}cooja.jar -nogui={absolute_path}  -contiki={contiki_path}"

            origin_pcap_file = None
            segfault = False

            p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            if verbose:
                terminal_width = int(subprocess.check_output(['stty', 'size']).split()[1])
                time_remaining = ""
                progress = "Starting..."
                for line in iter(p.stdout.readline, ''):
                    if not line :
                        break
                    else:
                        line = line.decode().strip()
                        if "%, done in " in line:
                            parts = line.split(", done in ")
                            time_remaining = " | "+ parts[1]
                            progress = parts[0].split()[-1]
                        elif "Test script finished" in line:
                            progress = "100%"
                            time_remaining = ""
                        elif "Test script activated" in line:
                            progress = "0%"
                            time_remaining = ""
                        elif "Opened pcap file" in line:
                            origin_pcap_file = f"{temp_dir}{line.split()[-1]}"
                        elif "Segmentation fault" in line or "Java Result: 139":
                            segfault = True
                    print((f"{self.title}   [{progress}{time_remaining}]").ljust(terminal_width), end="\r")
                p.stdout.close()
                print("")
            code=p.wait()
            self.return_value=code

            if self.has_suceed() or segfault or code == 139:
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

                if enable_pcap:
                    if pcap_file == None:
                        pcap_file = f"{prefix}{self.id}.pcap"
                    if os.path.exists(origin_pcap_file):
                        self.pcap_file=pcap_file
                        pcap_file_folder = "/".join(pcap_file.split("/")[:-1])
                        if pcap_file_folder != '' and  not os.path.exists(pcap_file_folder):
                            os.makedirs(pcap_file_folder)
                        shutil.copy(origin_pcap_file,pcap_file)
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
            if remove_csc and self.has_suceed():
                os.remove(csc_filepath)
            for mote_type in self.mote_types:
                if mote_type.from_source:
                    mote_type.remove_firmware()
            shutil.rmtree(temp_dir)

            return code

    def run_with_gui(self, verbose=False):
        
        if self.script_runner == None:
            self.script_runner = TimeoutScript(self.timeout, with_gui=False)

        temp_folder = f"{tempfile.gettempdir()}/cooja_sim_{hex(id(self))[2:]}/"
        try:
            self.export(temp_folder, gui_enabled=True, verbose=True)
            absolute_path=os.path.abspath(f"{temp_folder}/simulation.csc")

            contiki_path = self.get_contiki_path()
            jar_location = f"{contiki_path}/tools/cooja/dist/"
            command=f"cd {temp_folder} && java -Xshare:on -Dnashorn.args=--no-deprecation-warning -mx512m -jar {jar_location}cooja.jar -quickstart={absolute_path} -contiki={contiki_path}"
            if not verbose:
                command +=" 2> /dev/null > /dev/null"
            os.system(command)
        except CompilationError as e:
            print(e)
        except SettingsError as e:
            print(e)
        finally:
            shutil.rmtree(temp_folder)

    def check_settings(self,verbose=False):
        errors = []
        for mote in self.topology:
            if mote.mote_type == None:
                errors.append(f"Mote #{mote.id} has no mote type")

        if len(errors) > 0:
            raise SettingsError("\n".join(errors))

        # Check mote type and firmware
        for mote_type in self.mote_types:
            if not mote_type.firmware_exists():
                compiled = mote_type.compile_firmware(verbose=verbose, clean=True)
                if not compiled:
                    errors.append(f"Firmware '{mote_type.firmware_path}' did not compile correctly")
                # If compiling did not work
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


    def export(self, folder=None, gui_enabled=False, verbose=False):
        if folder == None:
            folder = f"simulation_{self.id}"

        if folder[-1] == "/":
            folder = folder[:-1]

        if not os.path.exists(folder):
            os.makedirs(folder)

        self.check_settings(verbose=verbose)

        sim = copy.deepcopy(self)

        if verbose:
            print(f"Exporting simulation in '{folder}/' ...")

        i=0
        for i in range(len(self.mote_types)):
            firmware_filename = self.mote_types[i].firmware_path.split("/")[-1]
            new_path = f"{folder}/{firmware_filename}"
            self.mote_types[i].save_firmware_as(new_path, verbose=verbose)

        print("Saving simulation as Cooja file (.csc)")
        CSCParser.export_simulation(sim, f"{folder}/simulation.csc", gui_enabled=gui_enabled)


    @staticmethod
    def from_csc(file_path, timeout=60):
        """
        Simple .csc file parser.
        """
        folder = "/".join(file_path.split('/')[:-1])
        mote_types = []
        motes = []

        tree = etree.parse(file_path)

        # Parsing general simulation and radio settings
        simulation_tag=tree.xpath("/simconf/simulation")[0]
        title = str(simulation_tag.xpath("title/text()")[0])
        seed = str(simulation_tag.xpath("randomseed/text()")[0])

        # Creating topology
        topology = Topology.from_csc(file_path)

        # Creating simulation
        simulation = CoojaSimulation(topology=topology, seed=seed,title=title,\
                        timeout=timeout)
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

    def run(self, verbose=True):

        # Check settings and compile firmware before threads start
        for simulation in self.simulations:
            simulation.check_settings(verbose=verbose)

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
                simulation.run(verbose=False, **kwargs)
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
