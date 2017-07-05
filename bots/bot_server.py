from multiprocessing import Queue, Event
import json

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

    def server_error(self):
        self.log("Server error.")
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

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        try:
            # retrieve method
            command = eval("self.{}".format(whole[0]))

            # retrieve method arguments
            args = [int(a) if a.isdigit() else a for a in whole[1:]]

            # call method
            to_client = command(*args)

        except Exception as e:
            to_client, to_controller = (
                "Command contained in request not understood.\n"
                "{}".format(e),
                None)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))
        return to_client

    def ask_init(self, android_id):

        self.log("Android id is: '{}'.".format(android_id))

        game_id = 0
        t = 0
        role = self.controller.role
        if role == "firm":
            position = 0
            price = 0
            return "reply/reply_init/" + "/".join([str(i) for i in [game_id, t, role, position, price]])

        else:
            position = 0
            exploration_cost = 0
            utility_consumption = 0
            return "reply/reply_init" + "/".join([str(i) for i in [game_id, t, role, position, exploration_cost, utility_consumption]])

    def ask_firm_opponent_choice(self, game_id, t):

        self.log("Firm {} ask firm opponent choice for t {}.".format(game_id, t))
        position, price = 0, 0
        n_clients = 2
        return "reply/reply_firm_opponent_choice/" + "/".join([str(i) for i in [position, price, n_clients]])

    def ask_firm_choice_recording(self, game_id, t, position, price):

        self.log("Firm {} make choice for t {}: {} for position and {} for price.".format(game_id, t, position, price))
        return "reply/reply_firm_choice_recording"

    def ask_firm_n_clients(self, game_id, t):

        self.log("Firm {} ask for number of clients as t {}.".format(game_id, t))
        n_clients = 4
        return "reply/reply_firm_n_clients/{}".format(n_clients)


def main():

    bot_c = BotController("firm")
    bot_c.run()
