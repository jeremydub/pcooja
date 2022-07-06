from pcooja import *
from pcooja.pcap import *
import random
import os
#from custommotes import *

CoojaSimulation.set_contiki_path("/home/user/contiki")

folder = CoojaSimulation.get_contiki_path()+"/examples/ipv6"

def simulation_example1():
    """
    load a simulation from a .csc file
    """
    filepath=folder+"/rpl-udp/rpl-udp.csc"

    # Create a simulation object from an existing .csc file.
    simulation = CoojaSimulation.from_csc(filepath)
    simulation.timeout = 10
    # Edit some settings (optional)
    simulation.success_ratio_rx = 1.0

    # Run the simulation and store the log and radio data in files
    simulation.run(verbose=True)

def simulation_example2():
    # Defining cooja mote types and firmware
    server = Z1MoteType(folder+"/rpl-udp/udp-server.z1")
    client = Z1MoteType(folder+"/rpl-udp/udp-client.z1")

    # Use a predefined topology that contains 2 types of mote (server,client)
    topology = Topology.get_tree25_topology(Z1Mote, server, client)

    # Create a simulation with default RX/TX success ratio, seed and timeout values
    simulation = CoojaSimulation(topology, timeout=30)

    # Run the simulation and store the log and radio data in specific files
    simulation.run_with_gui(verbose=True)

def simulation_example3():
    csc_filepath=folder+"/simple-udp-rpl/unicast-example.csc"

    # Defining cooja mote types and firmware
    server = SkyMoteType(folder+"/rpl-udp/udp-server.sky")
    client = SkyMoteType(folder+"/rpl-udp/udp-client.sky")

    # Use topology found in .csc file, mote types are not preserved
    topology = Topology.from_csc(csc_filepath)

    # Set mote types
    topology.set_mote_type(1,server)
    topology.set_mote_type([2,3,4,5,6,7,8,9,10,11], client)

    # Create a simulation with default RX/TX success ratio, seed and timeout values
    simulation = CoojaSimulation(topology, timeout=120)

    # Just for information, it is possible to compile a firmware
    # Compile Server firmware, if it does not exist
    server.compile_firmware()
    # Compile (and override) Client firmware
    client.compile_firmware(clean=True, verbose=True)

    # Run the simulation and store the log and radio data in files
    simulation.run(verbose=True)

def simulation_example4():
    # Defining cooja mote types and firmware
    server = SkyMoteType(folder+"/rpl-udp/udp-server.sky")
    client = SkyMoteType(folder+"/rpl-udp/udp-client.sky")

    # Create a random topology
    n = 10
    width=200
    height=200

    motes=[]
    current_mote_id=1
    for i in range(n):
        x = random.random()*width-width/2
        y = random.random()*height-height/2

        if current_mote_id == 1:
            mote_type = server
        else:
            mote_type = client

        new_mote = SkyMote(current_mote_id,x,y, mote_type)
        motes.append(new_mote)
        current_mote_id += 1

    medium = radio.UDGM(transmitting_range=50, interference_range=70)
    topology = Topology(motes, radiomedium=medium)

    # Create a simulation
    simulation = CoojaSimulation(topology, seed=15468, timeout=100)

    # Run the simulation and store the log and radio data in specific files
    simulation.run(filename_prefix="simulation_", verbose=True)

def simulation_example6():
    """
    Running a simulation in Cooja with GUI.
    """
    csc_filepath=folder+"/rpl-udp/rpl-udp.csc"

    # Create a simulation object from an existing .csc file.
    simulation = CoojaSimulation.from_csc(csc_filepath)

    # Run simulation in Cooja with GUI.
    simulation.export()

def simulation_example8():
    """
    Run simulations on multiple threads
    """
    filepath=folder+"/simple-udp-rpl/unicast-example.csc"

    # Thread dispatcher
    simulation_worker = CoojaSimulationWorker()

    rx_list = [0.4,0.6,0.8,1.0]
    for rx in rx_list:
        # Create a simulation object from an existing .csc file.
        simulation = CoojaSimulation.from_csc(filepath)
        simulation.success_ratio_rx = rx
        simulation.timeout = 60

        # arguments that would normally be passed to simulation.run()
        args={'pcap_file':'simulation_'+str(rx)+".pcap", 'log_file':'simulation_'+str(rx)+".log"}

        # Add simulation to worker that dispatchs to a thread
        simulation_worker.add_simulation(simulation, run_args=args)

    # Run simulations on multiple threads
    simulation_worker.run()

def simulation_example9():
    """
    Setting startup delay for each mote
    """
    filepath=folder+"/rpl-udp/rpl-udp.csc"

    # Create a simulation object from an existing .csc file.
    simulation = CoojaSimulation.from_csc(filepath)

    for mote in simulation.topology:
        # Generate random delay between 5000 and 10000 milliseconds
        delay = 5000 + random.random()*(10000-5000)
        mote.startup_delay = delay

    # Run the simulation and store the log and radio data in files
    simulation.run_with_gui()

def simulation_example10():
    # Defining cooja mote types and firmware
    server = CoojaMoteType(folder+"/hello-world/hello-world.cooja")

    client.compile_firmware(clean=True, verbose=True)


"""
functions=[simulation_example6,\
           simulation_example8,simulation_example9,\
           pcap_example1,pcap_example2,pcap_example3]
"""
functions=[simulation_example10]

for function in functions:
    os.system("clear")
    print("#"*80)
    print("### Calling demo function : "+function.__name__)
    print("#"*80)
    function()
    input("\n# Press ENTER to call next demo function")
