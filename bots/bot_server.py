from multiprocessing import Queue, Event
import json
import numpy as np

from utils.utils import Logger

from hotelling_server.control import server


class BotController(Logger):

    name = "BotController"

    def __init__(self, firm):

        self.role = firm

        self.parameters = {}
        self.shutdown = Event()
        self.queue = Queue()

        self.setup()

        self.server = server.Server(controller=self)
        self.game = BotGame(controller=self)

    def setup(self):

        for key in ["network", "game", "folders", "map_android_id_server_id", "interface"]:
            with open("hotelling_server/parameters/{}.json".format(key)) as file:
                self.parameters[key] = json.load(file)

    def run(self):

        self.server.start()

        self.server.queue.put(("Go", ))

        while not self.shutdown.is_set():

            try:
                self.log("Waiting for a message.")
                message = self.queue.get()
                if message == "break":
                    break
                else:
                    self.handle_message(message)

            except KeyboardInterrupt:

                self.game.end = self.game.t

                while True:
                    self.log("Game Over at t {}".format(self.game.end))
                    self.log("Waiting for a message.")
                    message = self.queue.get()
                    if message == "break":
                        break
                    else:
                        self.handle_message(message)

        self.close_program()

    def close_program(self):
        self.log("Close program.")
        self.server.shutdown()
        self.server.end()
        self.shutdown.set()

    def handle_message(self, message):

        command = message[0]
        args = message[1:]
        if len(args):
            eval("self.{}(*args)".format(command))
        else:
            eval("self.{}()".format(command))

    def server_running(self):
        self.log("Server running.")

    def server_error(self, arg):
        self.log("Server error: {}.".format(arg))
        self.queue.put("break")

    def server_request(self, server_data):
        response = self.game.handle_request(server_data)
        self.server.queue.put(("reply", response))

    def get_parameters(self, key):

        return self.parameters[key]


class BotGame(Logger):

    name = "BotGame"

    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.t = 0
        self.end = -1

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        # retrieve method
        command = eval("self.{}".format(whole[0]))

        # retrieve method arguments
        args = [int(a) if a.isdigit() else a for a in whole[1:]]

        # call method
        to_client = command(*args)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))
        return to_client

    def ask_init(self, android_id):

        self.log("Android id is: '{}'.".format(android_id))

        game_id = 0
        t = self.t
        role = self.controller.role
        if role == "firm":
            state = 'active'
            position = np.random.randint(1, 12)
            price = np.random.randint(1, 12)
            opp_position = np.random.randint(1, 12)
            opp_price = np.random.randint(1, 12)
            profits = np.random.randint(1000) 
            return "reply/reply_init/" + "/".join([str(i) for i in [
                game_id, t, role, position, state, price, opp_position, opp_price, profits
            ]])

        else:
            position = np.random.randint(1, 12)
            exploration_cost = 0
            utility_consumption = 0
            utility = np.random.randint(1000) 
            return "reply/reply_init/" + "/".join([str(i) for i in [
                game_id, t, role, position, exploration_cost, utility_consumption, utility
            ]])

    # ---------------- Firm questions ----------------------------------------- #

    def ask_firm_opponent_choice(self, game_id, t):

        assert self.t == t

        self.log("Firm {} asks firm opponent choice for t {}.".format(game_id, t))
        position, price = np.random.randint(1, 12, 2)
        n_clients = np.random.randint(0, 12)
        n_opp = np.random.randint(0, 12)

        end = int(t == self.end)

        # End of turn for passive firm
        self.t += 1

        return "reply/reply_firm_opponent_choice/" + "/".join([str(i) for i in [
            self.t - 1, position, price, n_clients, n_opp, end
        ]])

    def ask_firm_choice_recording(self, game_id, t, position, price):

        assert self.t == t

        self.log("Firm {} make choice for t {}: {} for position and {} for price.".format(game_id, t, position, price))
        return "reply/reply_firm_choice_recording/" + "/".join([str(i) for i in [
            self.t
        ]])

    def ask_firm_n_clients(self, game_id, t):

        assert self.t == t

        self.log("Firm {} asks for number of clients as t {}.".format(game_id, t))
        n_clients = np.random.randint(0, 12)
        n_opp = np.random.randint(0, 12)

        end = int(self.end == t)

        # End of turn for active firm
        self.t += 1

        return "reply/reply_firm_n_clients/" + "/".join([str(i) for i in [
            self.t - 1, n_clients, n_opp, end
        ]])

    # --------------- Customer questions --------------------------------------- #

    def ask_customer_firm_choices(self, game_id, t):

        assert self.t == t

        self.log("Customer {} asks for recording his choice as t {}.".format(game_id, t))
        position_0, position_1, price_0, price_1 = np.random.randint(1, 12, size=4)
        return "reply/reply_customer_firm_choices/" + "/".join([str(i) for i in [
            self.t, position_0, position_1, price_0, price_1
        ]])

    def ask_customer_choice_recording(self, game_id, t, extra_view, firm):

        assert self.t == t

        self.log("Customer {} asks for recording his choice as t {}: "
                 "{} for extra view, {} for firm.".format(game_id, t, extra_view, firm))

        # End of turn for customer
        self.t += 1

        return "reply/reply_customer_choice_recording/" + "/".join([str(i) for i in [
            self.t - 1, int(self.end == t)
        ]])


def main(role):

    bot_c = BotController(role)
    bot_c.run()
