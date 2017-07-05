from utils.utils import log
import numpy as np


class Game:

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.command = None

        self.t = 0

        self.game_parameters = self.controller.parameters.param["game"]
        self.interface_parameters = self.controller.parameters.param["interface"]

        self.n_customers = self.game_parameters["n_customers"]
        self.n_firms = self.game_parameters["n_firms"]

        self.continue_game = True

        self.data = self.controller.data

        self.save = None

    def setup(self, parameters, new):

        self.save = parameters["save"]

        if new:
            self.data.roles = ["firm" for i in range(self.n_firms)] + \
                              ["customer" for i in range(self.n_customers)]

            np.random.shuffle(self.data.roles)

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
            to_client, to_controller = (
                "Command contained in request not understood.\n"
                "{}".format(e),
                None)

        log("Reply '{}' to request '{}'.".format(to_client, request), name=self.name)
        return to_client, to_controller

    def end_time_step(self):

        self.t += 1
        self.data.update_history()
        
        if not self.continue_game:
            self.controller.game_stop_game()

    def check_time_step(self, client_t):

        if not client_t == self.t:
            raise Exception("Time is not synchronized!")

    @staticmethod
    def reply(*args):
        return "reply/{}".format("/".join([str(a) for a in args]))

    def ask_init(self, android_id):

        game_id = self.controller.id_manager.get_game_id_from_android_id(android_id, max_n=len(self.data.roles))

        if game_id != -1:

            # pick role
            role = self.data.roles[game_id]

            if role == "firm":
                firm_id = len(self.data.firms_id) + 1 if len(self.data.firms_id) != 0 else 0
                self.data.firms_id[game_id] = firm_id
                position = self.data.current_state["firm_positions"][firm_id]
                price = self.data.current_state["firm_prices"][firm_id]

                return self.reply(game_id, self.t, role, position, price), None

            else:
                customer_id = len(self.data.firms_id) + 1 if len(self.data.firms_id) != 0 else 0
                self.data.customer_id[game_id] = customer_id
                position = customer_id + 1
                exploration_cost = self.interface_parameters["exploration_cost"]
                utility_consumption = self.interface_parameters["utility_consumption"]
                return self.reply(game_id, self.t, role, position, exploration_cost, utility_consumption), None

        else:
            return "Error", None

    def check_end_of_turn(self):

        current_state = self.data.current_state

        cond0 = all([len(current_state[k]) == self.n_clients
                for k in ["customer_extra_view_choices","customer_firm_choices"]])

        cond1 = all([len(current_state[k]) == self.n_firms
                for k in ["firm_positions","firm_prices"]])

        if cond0 and cond1:
            self.end_time_step()

#     def run(self, parameters, new):

        # self.setup(parameters, new)

    def stop_as_soon_as_possible(self):

        self.continue_game = False

    def end_game(self):

        self.controller.queue.put(("game_end_game", ))

    def customer_firm_choices(self, game_id, t):

        log("Customer {} asks for firms strategies.".format(game_id), name=self.name)

        self.check_time_step(t)

        x = self.data.current_state["firm_positions"]
        prices = self.data.current_state["firm_prices"]

        return self.reply(self.t, x[0], x[1], prices[0], prices[1]), None

    def firm_opponent_choice(self, game_id, t):

        assert self.n_firms == 2, "only works if firms are 2"

        log("Firm {} asks for opponent strategy.".format(game_id), name=self.name)

        self.check_time_step(t)

        opponent_id = (self.data.firms_id[game_id] + 1) % 2

        return (self.reply(self.t,
                           self.data.current_state["firm_positions"][opponent_id],
                           self.data.current_state["firm_prices"][opponent_id]),
                None)

    def firm_choice_recording(self, game_id, t, position, price):

        log("Firm {} asks to save its price and position.".format(game_id), name=self.name)

        self.check_time_step(t)
        
        self.data.write("firm_positions", game_id, position)
        self.data.write("firm_prices", game_id, price)

        return self.reply("Ok!"), None

    def customer_choice_recording(self, game_id, t, extra_view, firm):

        self.check_time_step(t)

        self.data.write("customer_extra_view_choice", game_id, extra_view)
        self.data.write("customer_firm_choices", game_id, firm)

        return self.reply("Ok!"), None

    def firm_n_clients(self, game_id, t):

        self.check_time_step(t)

        firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        cond = firm_choices == game_id

        n = len(firm_choices[cond])

        return self.reply(self.t, n), None
