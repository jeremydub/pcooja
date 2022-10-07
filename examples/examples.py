from pcooja import *
import random
import os
import datetime
import glob
#from custommotes import *

CoojaSimulation.set_contiki_path("/home/user/contiki-ng")

folder = CoojaSimulation.get_contiki_path()+"/examples"

import logging
logger.setLevel(logging.INFO)

def simulation_example1():
    csc_filepath=f"{folder}/rpl-udp/rpl-udp-cooja.csc"

    # Create a simulation object from an existing .csc file.
    simulation = CoojaSimulation.from_csc(csc_filepath)
    simulation.timeout = 10
    # Edit some settings (optional)
    simulation.success_ratio_rx = 1.0

    # Run the simulation and store the log and radio data in files
    simulation.run()

def simulation_example2():
    # Defining cooja mote types and firmware
    server = Z1MoteType(f"{folder}/rpl-udp/udp-server.c")
    client = Z1MoteType(f"{folder}/rpl-udp/udp-client.c")

    # Use a predefined topology that creates 1 server mote and 24 client motes
    topology = Topology.get_tree25_topology(Z1Mote, server, client)

    # Create a simulation with default RX/TX success ratio, seed and timeout values
    simulation = CoojaSimulation(topology, timeout=30)

    # Run the simulation and store the log and radio data in specific files
    simulation.run_with_gui()

def simulation_example3():
    csc_filepath=f"{folder}/rpl-udp/rpl-udp-sky.csc"

    # Defining cooja mote types and firmware
    server = SkyMoteType(f"{folder}/rpl-udp/udp-server.c")
    client = SkyMoteType(f"{folder}/rpl-udp/udp-client.c")

    # Use topology found in .csc file, mote types are not preserved
    topology = Topology.from_csc(csc_filepath)

    # Set mote types
    topology.set_mote_type(1,server)
    topology.set_mote_type([2,3,4,5,6,7,8], client)

    # Create a simulation with default RX/TX success ratio, seed and timeout values
    simulation = CoojaSimulation(topology, timeout=120)
    
    # Just for information, it is possible to compile a firmware
    # Compile Server firmware, if it does not exist
    server.compile_firmware()


    logger.setLevel(logging.DEBUG)

    # Compile (and override) Client firmware
    client.compile_firmware(clean=True)

    # Run the simulation and store the log in specific file
    simulation.run(log_file="output.log")

def simulation_example4():
    # Defining cooja mote types and firmware
    server = SkyMoteType(f"{folder}/rpl-udp/udp-server.c")
    client = SkyMoteType(f"{folder}/rpl-udp/udp-client.c")

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

    # Run the simulation
    simulation.run_with_gui()

def simulation_example5():
    """
    Export simulation.
    """
    csc_filepath=f"{folder}/rpl-udp/rpl-udp-sky.csc"

    # Create a simulation object from an existing .csc file.
    simulation = CoojaSimulation.from_csc(csc_filepath)

    # Run simulation in Cooja with GUI.
    simulation.export()

def simulation_example6():
    # Defining/overriding project configuration in 'project-conf.h'
    project_conf = ProjectConf(RPL_CONF_MAX_INSTANCES=1,
                                NBR_TABLE_CONF_MAX_NEIGHBORS=8,
                                IEEE802154_CONF_PANID=0x42,
                                LOG_CONF_LEVEL_IPV6="LOG_LEVEL_DBG")
    
    makefile_variables = {"MAKE_ROUTING":"MAKE_ROUTING_RPL_LITE", 
                          "MAKE_MAC":"MAKE_MAC_CSMA"}

    # Firmwares
    server = Z1MoteType(f"{folder}/rpl-udp/udp-server.c", 
                           project_conf=project_conf, 
                           makefile_variables=makefile_variables)
    client = Z1MoteType(f"{folder}/rpl-udp/udp-client.c", 
                           project_conf=project_conf, 
                           makefile_variables=makefile_variables)

    # Use a predefined topology that creates 1 server mote and 24 client motes
    topology = Topology.get_tree25_topology(Z1Mote, server, client)

    # Create a simulation with default RX/TX success ratio, seed and timeout values
    simulation = CoojaSimulation(topology, timeout=30)

    # Run the simulation and store the log and radio data in specific files
    simulation.run_with_gui()

def simulation_example7():
    # Defining/overriding project configuration in 'project-conf.h'
    project_conf = ProjectConf(RPL_CONF_MAX_INSTANCES=1,
                                NBR_TABLE_CONF_MAX_NEIGHBORS=8,
                                IEEE802154_CONF_PANID=0x42,
                                LOG_CONF_LEVEL_RPL="LOG_LEVEL_DBG")

    # Firmwares
    server = CoojaMoteType(f"{folder}/rpl-udp/udp-server.c", 
                           project_conf=project_conf) 
    client = CoojaMoteType(f"{folder}/rpl-udp/udp-client.c", 
                           project_conf=project_conf)

    topology = Topology.get_tree25_topology(CoojaMote, server, client)
    simulation = CoojaSimulation(topology, timeout=100)

    simulation.run()

    
    log = Log(simulation.get_log_filepath())
    messages = log.get_messages()

    send_requests = log.get_messages(contain="Sending request")
    received_requests = log.get_messages(contain="Received request")
    send_responses = log.get_messages(contain="Sending response")
    received_responses = log.get_messages(contain="Received response")

    print(f"requests sent: {len(send_requests)}")
    print(f"requests received: {len(received_requests)}")
    print(f"responses sent: {len(send_responses)}")
    print(f"responses received: {len(received_responses)}")
    
    print("")

    app_log = log.get_messages(log_module="App", node_id=4)
    for message in app_log[:5]:
        Log.print_message(message)
    
    print("")

    errors_log = log.get_messages(log_level=Log.LEVEL_ERR, node_id=5)
    for message in errors_log:
        Log.print_message(message)

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

if __name__ == "__main__":
    simulation_example7()
