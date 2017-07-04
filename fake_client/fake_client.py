import json
import socket
from threading import Thread, Event
import numpy as np

from utils.utils import log


class FakeClient(Thread):

    with open("parameters/network.json") as file:
        param = json.load(file)

    ip_address, port = "localhost", param["port"]
    delay_socket_retry = 0.1
    socket_timeout = 0.5

    def __init__(self):

        super().__init__()

        # Would be set after get init
        self.idx = None

        # Would be set at each new demand addressed to server
        self.server_demand = None

        # The following variables will be set following server responses
        self.continue_game = 1

        self.command = {}

    @property
    def able_to_handle(self):
        return list(self.command.keys())

    def get_init(self):

        fake_android_id = self.name
        self.ask_server("get_init/{}".format(fake_android_id))

    def time_step(self):

        pass

    def handle(self, what, *params):

        log("Handle {} with params '{}'.".format(what, params), self.name)

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
                    Event().wait(self.delay_socket_retry)
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
            if self.treat_server_reply(parts):
                log("Server response handled.", self.name)
            else:
                self.retry_demand(response)
        else:
            self.retry_demand("No response.")

    def treat_server_reply(self, parts):

        if len(parts) > 1 and parts[0] == "reply" and parts[1] in self.able_to_handle:
            self.handle(what=parts[1], *parts[2:])
            return 1

        else:
            log("Error in treating server reply!", self.name)
            return 0

    def retry_demand(self, server_response):

        log("Server response is in bad shape: '{}'. Retry the same demand.".format(server_response), self.name)

        # noinspection PyCallByClass,PyTypeChecker
        Event().wait(self.delay_socket_retry)
        self.ask_server(self.server_demand)

    def run(self):

        self.get_init()

        while self.continue_game:
            self.time_step()

        log("End of game.", self.name)


class HotellingPlayer(FakeClient):

    def __init__(self):
        super().__init__()

        self.game_id = 0
        self.role = ""
        self.n_positions = 0
        self.extra_view_possibilities = None
        self.command = {
            "init": self.reply_init
        }

    def reply_init(self, *args):

        self.game_id = args[0]
        self.role = args[1]
        self.n_positions = 0
        self.extra_view_possibilities = np.arange(0, self.n_positions, 2)

    def time_step(self):

        if self.role == "customer":
            self.customer_extra_view_choice()

    def customer_extra_view_choice(self):

        np.random.choice(self.extra_view_possibilities)


