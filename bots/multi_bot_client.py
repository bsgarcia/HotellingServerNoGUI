import json
import socket
from threading import Thread, Event
from multiprocessing import Queue
import numpy as np

from utils.utils import Logger


class GenericBotClient(Thread, Logger):

    with open("hotelling_server/parameters/network.json") as file:
        network_parameters = json.load(file)
    ip_address, port = "localhost", network_parameters["port"]
    delay_socket_retry = 0.5
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

    def handle(self, what, params):

        self.log("Handle {} with params '{}'.".format(what, params))

        params = [int(x) if type(x) == str and x.isdigit() else x for x in params]

        command = eval("self.{}".format(what))

        try:
            command(*params)

        except Exception as e:
            self.log("Error when running '{}' method: {}".format(what, str(e)))

    def ask_server(self, message):

        self.server_demand = message

        while True:

            self.log("Ask the server: '{}'.".format(message))

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
            #     self.log("Timeout reached.")
            #     self.sock.close()
            #     self.sock = None

            except Exception as e:
                self.log("Exception: {}".format(e))
                if sock:
                    sock.close()

    def handle_server_response(self, response):

        if response != "":
            self.log("Received from server: '{}'.".format(response))
            parts = response.split("/")
            if self.treat_server_reply(parts):
                self.log("Server response handled.")
            else:
                self.retry_demand(response)
        else:
            self.retry_demand("No response.")

    def treat_server_reply(self, parts):

        if len(parts) > 1 and parts[0] == "reply" and parts[1]:
            self.handle(parts[1], parts[2:])
            return 1

        else:
            self.log("Error in treating server reply!")
            return 0

    def retry_demand(self, server_response):

        self.log("Server response is in bad shape: '{}'. Retry the same demand.".format(server_response))

        # noinspection PyCallByClass,PyTypeChecker
        Event().wait(self.delay_socket_retry)
        self.queue.put(("ask_server", self.server_demand))


class HotellingPlayer(GenericBotClient):

    def __init__(self, parameters):
        super().__init__()
        
        self.game_parameters = parameters
        self.name = parameters["name"]
        self.game_id = None
        self.role = ""
        self.n_positions = parameters["n_positions"]
        self.position = 0
        self.t = 0
        self.game_started = False

        self.customer_attributes = {}
        self.firm_attributes = {}

    def run(self):

        self.ask_init()

        while self.continue_game:

            to_do = self.queue.get()
           
            self.handle(to_do[0], to_do[1:])
            
            # Event().wait(0.1)

        self.log("End of game.")

    def wait(self, *args):
        self.log("Waits 2 seconds then run {} with params {}".format(args[0], args[1:]))
        Event().wait(2)
        self.queue.put((args[0], *args[1:]))

    def ask_init(self):

        fake_android_id = self.name
        self.ask_server("ask_init/{}".format(fake_android_id))

    def reply_init(self, *args):

        self.game_id, self.t, self.role, self.position = args[:4]

        if "firm" in self.role:
            self.firm_attributes["price"] = args[4]
            self.firm_attributes["n_prices"] = self.game_parameters["n_prices"]

        self.n_positions = self.game_parameters["n_positions"]
        self.customer_attributes["extra_view_possibilities"] = np.arange(0, self.n_positions, 2)
        
        self.wait(*("ask_end_of_init", self.t, self.game_id, self.role, self.game_started))

    def new_turn(self, server_t):
        self.queue.empty()
        self.game_started = True
        self.t = server_t

        if "firm" in self.role:
            self.queue.put(("ask_role", self.game_id, self.role))

        elif self.role == "customer":
            self.queue.put(("ask_customer_firm_choices", ))

    # ------------------------- Customer choice functions --------------------------------- #

    def customer_choice(self, position_0, position_1, price_0, price_1):

        extra_view = self.customer_extra_view_choices()
        firm = self.customer_firm_choices(np.array([position_0, position_1]),
                                         np.array([price_0, price_1]))
        self.ask_customer_choice_recording(extra_view, firm)

    def customer_extra_view_choices(self):

        self.customer_attributes["extra_view_choice"] = \
            np.random.choice(self.customer_attributes["extra_view_possibilities"])
        return self.customer_attributes["extra_view_choice"]

    def customer_firm_choices(self, positions, prices):

        field_of_view = [
            self.position - self.customer_attributes["extra_view_choice"],
            self.position + self.customer_attributes["extra_view_choice"]
        ]

        cond0 = positions >= field_of_view[0]
        cond1 = positions <= field_of_view[1]

        available_prices = prices[cond0 * cond1]

        firm_idx = np.arange(len(positions))
        available_firm = firm_idx[cond0*cond1]

        if len(available_prices):
            self.customer_attributes["min_price"] = min(available_prices)
            firm_choice = np.random.choice(
                available_firm[np.where(available_prices == self.customer_attributes["min_price"])[0]]
            )

        else:
            self.customer_attributes["min_price"] = 0
            firm_choice = None

        return firm_choice

    def customer_end_of_turn(self):

        self.ask_end_of_turn(self.t, self.game_id, self.role)
        # self.ask_customer_firm_choices()

    # ------------------------- Firm choice functions --------------------------------- #

    def firm_passive_turn(self, opp_position, opp_price):

        self.ask_firm_n_clients()
        self.log("I am passive and I got {} clients.".format(self.n_clients))
        self.ask_end_of_turn(self.t, self.game_id, self.role)

    def firm_active_turn(self, opp_position, opp_price):

        self.log("Opp position and price are {} and {}.".format(opp_position, opp_price))
        own_position = np.random.randint(1, self.n_positions)
        own_price = np.random.randint(1, self.firm_attributes["n_prices"])
        self.ask_firm_choice_recording(own_position, own_price)
        self.log("I am active and I got {} clients.".format(self.n_client))
        self.ask_end_of_turn(self.t, self.game_id, self.role)

    def firm_set_n_client(self, n_client):
        self.n_client = n_client

    def firm_set_role(self, role):
        self.role = role

    # ------------------------- Customer communication -------------------------------- #

    def ask_customer_firm_choices(self):
        self.ask_server("ask_customer_firm_choices/{}/{}".format(self.game_id, self.t))

    def reply_customer_firm_choices(self, position_0, position_1, price_0, price_1):
        self.queue.put(("customer_choice", position_0, position_1, price_0, price_1))

    def ask_customer_choice_recording(self, extra_view_choice, firm_choice):
        self.ask_server("ask_customer_choice_recording/{}/{}/{}/{}".format(self.game_id, self.t, extra_view_choice, firm_choice))

    def reply_customer_choice_recording(self):
        self.queue.put(("customer_end_of_turn", ))

    # ------------------------- Firm communication ------------------------------------ #

    def ask_firm_opponent_choice(self):
        self.ask_server("ask_firm_opponent_choice/{}/{}".format(self.game_id, self.t))

    def reply_firm_opponent_choice(self, position, price):
        self.queue.put(("{}_turn".format(self.role), position, price))

    def ask_firm_choice_recording(self, position, price):
        self.ask_server("ask_firm_choice_recording/" + "/".join([str(i) for i in [self.game_id, self.t, position, price]]))

    def reply_firm_choice_recording(self):
        self.queue.put(("ask_firm_n_clients", ))

    def ask_firm_n_clients(self):
        self.ask_server("ask_firm_n_clients/" + "/".join([str(i) for i in [self.game_id, self.t]]))

    def reply_firm_n_clients(self, n):
        self.queue.put(("firm_set_n_client", n, ))

    def ask_role(self, game_id, t):
        self.ask_server("ask_role/{}/{}".format(game_id, t))

    def reply_role(self, t, role):
        self.firm_set_role(role)
        self.queue.put(("ask_firm_opponent_choice",))

    # ------------------------- all agents communication ------------------------------------ #
    def ask_end_of_init(self, t, game_id, role, game_started):
        if not self.game_started:
            self.ask_server("ask_end_of_init/{}/{}/{}/{}".format(t, game_id, role, game_started))

    def reply_end_of_init(self, t, game_id, role, game_started):
        if not self.game_started:
            self.wait(*("ask_end_of_init", t, game_id, role, game_started))

    def ask_end_of_turn(self, t, game_id, role):
        self.ask_server("ask_end_of_turn/{}/{}/{}".format(t, game_id, role))

    def reply_end_of_turn(self, t, game_id, role):
        self.wait(*("ask_end_of_turn", t, game_id, role))


def main():

    with open("hotelling_server/parameters/game.json") as f:
        game_parameters = json.load(f)

    n_agents = game_parameters["n_customers"] + game_parameters["n_firms"]

    for i in range(n_agents):
        game_parameters["name"] = "HotellingPlayer{}".format(i)
        bc = HotellingPlayer(game_parameters)
        bc.start()
