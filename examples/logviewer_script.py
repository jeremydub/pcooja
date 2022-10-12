from pcooja import Log

def application_pdr(log):
    """
    List and Analyse PDR of nodes
    """
    messages = log.messages
    simulation_time = messages[-1][Log.TIME]
    print(simulation_time/1000000)

    send_requests = log.get_messages(contain="Sending request")
    received_requests = log.get_messages(contain="Received request")
    send_responses = log.get_messages(contain="Sending response")
    received_responses = log.get_messages(contain="Received response")

    print(f"Sent requests: {len(send_requests)}")
    print(f"Received requests: {len(received_requests)}")
    print(f"Sent responses: {len(send_responses)}")
    print(f"Received responses: {len(received_responses)}")

def example(log):
    """
    List, for each node, the count of serial messages containing "Received response"
    """

    for node_id in log.get_node_ids():
        count = log.get_messages(node_id=node_id, contain="Received response")
        print(f"Node #{node_id} : {len(count)} messages")

def view(log):
    """
    TSCH
    """
    print("")
    print("^Joined network")
    tsch_joined = log.get_messages(contain="minimal schedule")
    if len(tsch_joined) == 0:
        print("No node ...")
    else:
        print(tsch_joined)

    print("")
    print("^Schedules")
    tsch_schedules = log.get_messages(log_module="TSCH Sched")
    tsch_schedules.sort(key=lambda message: message[Log.NODE_ID])
    print(tsch_schedules)

    print("")
    print("^Queues")
    tsch_queues = log.get_messages(log_module="TSCH Queue")
    tsch_queues.sort(key=lambda message: message[Log.NODE_ID])
    print(tsch_queues)

    return True

def view_app(log):
    """
    App
    """
    for node_id in log.get_node_ids():
        print(f"^Node #{node_id}")
        if node_id == 1:
            app_messages = log.get_messages(log_module="App", node_id=node_id, contain="Received")
            app_messages2 = log.get_messages(log_module="App", node_id=node_id, contain="Sending")
            app_messages += app_messages2
            app_messages.sort(key=lambda message: message[Log.TIME])
            print(app_messages)
        else:
            app_messages = log.get_messages(log_module="App", node_id=node_id, contain="Sending")
            app_messages2 = log.get_messages(log_module="App", node_id=node_id, contain="Received")
            app_messages += app_messages2
            app_messages.sort(key=lambda message: message[Log.TIME])
            print(app_messages)


def view_errors(log):
    """
    Errors
    """
    messages = log.get_messages(log_level=Log.LEVEL_WARN)
    warning_messages = list(filter(lambda m:m[Log.LOG_LEVEL] == Log.LEVEL_WARN, messages))
    print("")
    print("^Warning Messages")
    if len(warning_messages) == 0:
        print("No warning message !")
    else:
        print(warning_messages)
    print("")
    print("^Error Messages")
    error_messages = list(filter(lambda m:m[Log.LOG_LEVEL] == Log.LEVEL_ERR, messages))
    if len(error_messages) == 0:
        print("No error message !")
    else:
        print(error_messages)

