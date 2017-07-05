import json
import socket
from threading import Thread, Event
from multiprocessing import Queue
import numpy as np

from utils.utils import log


class FakeClient(Thread):

    with open("parameters/network.json") as file:
        network_parameters = json.load(file)

    ip_address, port = "localhost", network_parameters["port"]
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

        self.queue = Queue()

    def handle(self, what, *params):

        log("Handle {} with params '{}'.".format(what, params), self.name)

        params = [int(x) if x.isdigit() else x for x in params]

        eval("self.{}(params)".format(what))

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

        if len(parts) > 1 and parts[0] == "reply" and parts[1]:
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


class HotellingPlayer(FakeClient):

    with open("parameters/game.json") as f:
        game_parameters = json.load(f)

    def __init__(self):
        super().__init__()

        self.game_id = 0
        self.role = ""
        self.n_positions = 0
        self.position = 0
        self.t = 0

        self.customer_attributes = {}
        self.firm_attributes = {}

    def run(self):

        self.ask_init()
        self.queue.get()

        while self.continue_game:
            self.time_step()

        log("End of game.", self.name)

    def ask_init(self):

        fake_android_id = self.name
        self.ask_server("ask_init/{}".format(fake_android_id))

    def reply_init(self, *args):

        self.game_id, self.t, self.role, self.position = args[:4]

        if self.role == "firm":
            self.firm_attributes["price"] = args[4]
            self.firm_attributes["n_prices"] = self.game_parameters["n_prices"]

        self.n_positions = self.game_parameters["n_positions"]
        self.customer_attributes["extra_view_possibilities"] = np.arange(0, self.n_positions, 2)
        self.queue.put("Go")

    # ----------- Time step ---------------------- #

    def time_step(self):

        if self.role == "customer":
            self.customer_time_step()

        elif self.role == "firm":
            self.firm_time_step()

        self.ask_end_of_turn()

        self.t += 1

    def customer_time_step(self):

        self.ask_customer_firm_choices(self.t)
        positions, prices = self.queue.get()
        extra_view_choice = self.customer_extra_view_choice()
        firm_choice = self.customer_firm_choice(positions, prices)
        self.ask_customer_choice_recording(self.game_id, self.t, extra_view_choice, firm_choice)
        self.queue.get()

    def firm_time_step(self):

        self.ask_firm_opponent_choice(self.game_id, self.t)
        opp_position, opp_price = self.queue.get()
        pos, price = self.firm_choice(self.game_id, self.t, opp_position, opp_price)
        self.ask_firm_choice_recording(self.game_id, self.t, pos, price)
        self.queue.get()
        self.ask_firm_n_clients(self.game_id, self.t)
        n_clients = self.queue.get()

    def ask_end_of_turn(self):

        self.ask_server("check_end_of_turn/")

    # ----------- Customer choice functions ---------------------- #

    def customer_extra_view_choice(self):

        self.customer_attributes["extra_view_choice"] = \
            np.random.choice(self.customer_attributes["extra_view_possibilities"])
        return self.customer_attributes["extra_view_choice"]

    def customer_firm_choice(self, positions, prices):

        field_of_view = [
            self.position - self.customer_attributes["extra_view_choice"],
            self.position + self.customer_attributes["extra_view_choice"]
        ]

        cond0 = positions >= field_of_view[0]
        cond1 = positions <= field_of_view[1]

        available_prices = prices[cond0 * cond1]

        firm_idx = np.arange(len(positions))
        available_firm = firm_idx[cond0*cond1]

        if available_prices:
            self.customer_attributes["min_price"] = min(available_prices)
            firm_choice = np.random.choice(
                available_firm[np.where(available_prices == self.customer_attributes["min_price"])[0]]
            )

        else:
            self.customer_attributes["min_price"] = 0
            firm_choice = None

        return firm_choice

    # ------------------------- Firm choice functions --------------------------------- #

    def firm_choice(self, opp_position, opp_price):

        return (np.random.randint(1, self.firm_attributes["n_prices"]),
                np.random.randint(1, self.n_positions))

    # ------------------------- Customer communication -------------------------------- #

    def ask_customer_firm_choices(self, t):
        self.ask_server("customer_firm_choices/{}".format(t))

    def reply_customer_firm_choices(self, *args):
        positions, prices = args
        self.queue.put((positions, prices))

    def ask_customer_choice_recording(self, game_id, t, extra_view_choice, firm_choice):
        self.ask_server("customer_choice_recording/{}/{}/{}/{}".format(game_id, t, extra_view_choice, firm_choice))

    def reply_customer_choice_recording(self):
        self.queue.put("Go")

    # ------------------------- Firm communication ------------------------------------ #

    def ask_firm_opponent_choice(self, game_id, t):
        self.ask_server("firm_opponent_choice/{}/{}".format(game_id, t))

    def reply_firm_opponent_choice(self, position, price):
        self.queue.put((position, price))

    def ask_firm_choice_recording(self, game_id, t, position, price):
        self.ask_server("firm_choice_recording/{}/{}".format(game_id, t, position, price))

    def reply_firm_choice_recording(self):
        self.queue.put("Go")

    def ask_firm_n_clients(self, game_id, t):
        self.ask_server("firm_n_clients/{}".format(game_id, t)

    def reply_firm_n_clients(self, n):
        self.queue.put(n)
