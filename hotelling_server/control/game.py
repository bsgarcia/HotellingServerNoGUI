from utils.utils import log
from data import Data
import numpy as np


class Game:

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.command = None

        self.t = 0
        self.n_agents = 13

        self.uc = 5
        self.ce = 5

        self.roles = (["firm" for n in range(2)]
                      + ["customer" for n in range(self.n_agents - 2)])

        self.firms = []

        self.positions = np.arange(len(self.n_agents))

        self.data = Data()

    def setup(self, parameters):

        pass

    def handle_request(self, request):

        log("Got request: '{}'.".format(request), self.name)

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]
   
        try:
            # retrieve method
            self.command = eval("self.{}".format(whole[0]))

            # retrieve method arguments
            args = [int(a) if a.isdigit() else a for a in whole[1:]]
   
            # call method
            to_client, to_controller = self.command(*args)

        except Exception as e:
            to_client, to_controller = ("Command contained in request not understood.\n"
                                        "{}".format(e),
                                        None,
                                        None)

        log("Reply '{}' to request '{}'.".format(to_client, request), name=self.name)
        return to_client, to_controller

    def end_timestep(self):

        self.t += 1
        self.data.update_history()

    def check_timestep(self, client_t):

        if not client_t == self.t:
            raise Exception("Time is not synchronized!")

    def reply(self, *args):
        return "reply{}".format("/".join([str(a) for a in args]))

    def ask_init(self, *args):

        android_id = args[0]

        game_id = self.controller.id_manager.get_game_id_from_android_id(android_id)
        
        # pick role 
        idx = np.random.randint(len(self.n_roles))
        role = self.roles.pop(idx)

        if role == "firm":
            self.firm.append(game_id)

        # retrieve position
        idx = np.random.randint(len(self.positions))
        position = self.positions.pop(idx)

        return self.reply(game_id, self.t, role, position, self.uc, self.ce), None

    def customer_firm_choices(self, *args):
        
        self.check_timestep(args[1])

        x = [x for x in self.data.current_state["firm_positions"]]
        prices = [x for x in self.data.current_state["firm_prices"]]

        return self.reply(self.t, x[0], x[1], prices[0], prices[1]), None

    def firm_opponent_choice(self, *args):
        
        self.check_timestep(args[1])

        opponent_id = (self.firms.index(game_id) + 1) % 2

        return (self.reply(self.t,
                           self.data.current_state["firm_positions"][opponent_id],
                           self.data.current_state["firm_prices"][opponent_id]),
                None)

    def firm_choice_recording(self, *args):

        self.check_timestep(args[1])
        
        self.data.write("firm_positions", args[3]) 
        self.data.write("firm_prices", arg[4]) 

        return self.reply("Ok!"), None

    def customer_choice_recording(self, *args):

        self.check_timestep(args[1])

        self.data.write("customer_extra_view_choice", args[3])
        self.data.write("customer_firm_choices", args[4])

        return self.reply("Ok!"), None

    def firm_n_clients(self, *args):

        self.check_timestep(args[1])

        firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        cond = firm_choices == args[0]

        n = len(firm_choices[cond])

        self.end_time_step()

        return self.reply(self.t, n), None
