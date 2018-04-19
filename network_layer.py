import zmq
import threading
import queue  # I am not sure if we need a queue or not.
import pickle
import sys

from collections import namedtuple

packet = namedtuple("packet", ["type", "source", "destination", "next_hop", "position", "message"])

routing_table_mutex = threading.Lock()
# this is a dictionary that we can keep names to corresponding IPs, also necessary routing information.

routing_table = {}

position_self = None  # some position

link_layer_message_queue = queue.Queue()  # queue holds messages in original format.

link_layer_address = "tcp://link_layer:5554"

network_layer_up_stream_address = "tcp://network_layer:5555"

network_layer_down_stream_address = "tcp://network_layer:5556"

app_layer_address = "tcp://app_layer:5557"


# here define rooting algorithm

# here we need atomic data structure for rooting algorithm


def periodic_update_location():
    pass


def find_routing(destination):
    # check routing table to find the next hop.
    with routing_table_mutex:
        next_hop = routing_table[destination]
        return next_hop


def query_address():
    pass


def update_routing_table(message):
    # here we need to to update routing table based on the algorithm we use.
    with routing_table_mutex:
        pass
    pass


def _is_control_message(message_type):
    return message_type == "broad" or message_type == "update"


def _is_destination_self(destination):
    return destination[0] == position_self[0] and destination[1] == position_self[1]


def link_layer_listener():
    server_socket = context.socket(zmq.REP)
    server_socket.bind(network_layer_down_stream_address)

    client_socket = context.socket(zmq.REQ)
    client_socket.connect(app_layer_address)

    while True:
        message_raw = server_socket.recv()
        message = pickle.loads(message_raw)

        if _is_control_message(message.type):
            update_routing_table(message)
        elif _is_destination_self(message.destination):
            client_socket.send(message_raw)
        else:
            link_layer_message_queue.put(message)


def app_layer_listener():
    # if the message contains control type flag, we should update the routing table we have.
    server_socket = context.socket(zmq.REP)
    server_socket.bind(network_layer_up_stream_address)

    while True:
        message = server_socket.recv()
        link_layer_message_queue.put(pickle.loads(message))


def link_layer_client():
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(link_layer_address)
    while True:
        message = link_layer_message_queue.get()

        message.destination = find_routing(message.destination)

        client_socket.send(pickle.dumps(message))

    pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Arguments are not valid. Usage: Pos.x Pos.y")
        exit(-1)

    position_self = (sys.argv[1], sys.argv[2])
    context = zmq.Context()

    network_layer_up_thread = threading.Thread(target=app_layer_listener, args=())
    network_layer_down_thread = threading.Thread(target=link_layer_listener, args=())
    link_layer_client_thread = threading.Thread(target=link_layer_client, args=())

    network_layer_up_thread.start()
    network_layer_down_thread.start()
    link_layer_client_thread.start()

    network_layer_down_thread.join()
    network_layer_up_thread.join()
    link_layer_client_thread.join()
