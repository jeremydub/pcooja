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

def compute_metric(log):
    """
    Compute a specific metric
    """
    result = []

    for i in range(1,10):
        result.append(f"Node #{1} : ??? %")
    
    return "\n".join(result)
