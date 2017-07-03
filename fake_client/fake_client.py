import json
from threading import Thread, Event
import numpy as np

from utils.utils import log

import socket


class FakeClient(Thread):

    with open("parameters/network.json") as file:
        param = json.load(file)

    ip_address, port = "localhost", param["port"]
    delay_socket_retry = 0.5
    socket_timeout = 0.5

    def __init__(self):

        super().__init__()

        # Would be set after get init
        self.idx = None

        # Would be set at each new demand addressed to server
        self.server_demand = None

        # The following variables will be set following server responses
        self.in_hand = None
        self.t = None
        self.success = None
        self.wheat_amount_number = None
        self.initial_state = None
        self.desired_object = None
        self.continue_game = 1

    def run(self):

        self.get_init()

        while self.continue_game:
            self.make_a_choice()

        log("End of game.", self.name)

    def get_init(self):

        fake_android_id = self.name
        self.ask_server("get_init/{}".format(fake_android_id))

    def make_a_choice(self):

        # Delay choice
        Event().wait(0.1)

        if self.in_hand == "wood":
            self.desired_object = np.random.choice(["stone", "wheat"])
        else:
            self.desired_object = np.random.choice(["wheat", "wood"])
        self.ask_server("set_choice/{}/{}/{}".format(self.idx, self.desired_object, self.t))

    def handle_results(self):

        self.t += 1

        if self.in_hand == "wheat" and self.success:
            self.in_hand = "wood"

    def handle_init(self):

        if self.initial_state == "choice":
            pass
        else:
            self.ask_server("set_choice/{}/{}/{}".format(self.idx, self.desired_object, self.t))

    def ask_server(self, message):

        self.server_demand = message

        while True:

            log("Ask the server: '{}'.".format(message), self.name)

            sock = None
            try:

                # Create a socket (SOCK_STREAM means a TCP socket)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.socket_timeout)

                # Connect to server and send data
                sock.connect((self.ip_address, self.port))

                sock.sendall(bytes(message + "\n", "utf-8"))

                received = sock.recv(1024)
                while not received:
                    Event().wait(0.1)
                    sock.recv(1024)

                self.handle_server_response(received.decode())
                break
            #
            # except socket.timeout:
            #     log("Timeout reached.", self.name)
            #     self.sock.close()
            #     self.sock = None

            except Exception as e:
                log("Exception: {}".format(e), self.name)
                if sock:
                    sock.close()

    def handle_server_response(self, response):

        if response != "":
            log("Received from server: '{}'.".format(response), self.name)
            parts = response.split("/")
            if len(parts) > 1 and parts[0] == "reply":
                log("Server response is in correct shape.", self.name)
                self.treat_server_reply(parts)
            else:
                self.retry_demand(response)
        else:
            self.retry_demand("No response.")

    def treat_server_reply(self, parts):

        if parts[1] == "init":
            log("Got init information.", self.name)
            self.idx = parts[2]
            self.in_hand = parts[3]
            self.desired_object = parts[4]
            self.wheat_amount_number = int(parts[5])
            self.initial_state = parts[6]
            self.t = int(parts[7])
            self.handle_init()

        elif parts[1] == "result":
            log("Got result.", self.name)
            self.success = int(parts[2])
            self.continue_game = int(parts[3])  # Will have an impact in 'nextOnResult'
            self.handle_results()

        else:
            log("Error in treating server reply!", self.name)

    def retry_demand(self, server_response):

        log("Server response is in bad shape: '{}'. Retry the same demand.".format(server_response), self.name)

        # noinspection PyCallByClass,PyTypeChecker
        Event().wait(self.delay_socket_retry)
        self.ask_server(self.server_demand)
