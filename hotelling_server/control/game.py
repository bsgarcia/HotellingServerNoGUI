import numpy as np
from bots.local_bot_client import HotellingLocalBots


from utils.utils import Logger, function_name


class Game(Logger):

    name = "Game"

    def __init__(self, controller):

        # get controller attributes
        self.controller = controller
        self.data = self.controller.data
        self.time_manager = self.controller.time_manager

        # get parameters from interface and json files
        self.game_parameters = self.controller.data.param["game"]
        self.parametrization = self.controller.data.param["parametrization"]
        self.assignement = self.controller.data.param["assignement"]

        # set number of type of players
        self.n_customers = self.game_parameters["n_customers"]
        self.n_firms = self.game_parameters["n_firms"]
        self.n_agents = self.n_firms + self.n_customers

    # ----------------------------------- sides methods --------------------------------------#
    def new(self, parameters):
        """called if new game is launched"""

        # parameters coming from interface
        self.data.parametrization = parameters["parametrization"]
        self.data.assignement = parameters["assignement"]
        
        self.interface_parameters = self.data.parametrization
        self.assignement = self.data.assignement

        self.data.roles = ["" for i in range(self.n_agents)]
        self.data.time_manager_t = 0
        
        # reset data in case a game was previously launched during the same session
        self.data.current_state = {s: [] for s in self.data.entries}

        self.data.current_state["connected_firms"] = ["" for i in range(self.n_firms)]
        self.data.current_state["connected_customers"] = ["" for i in range(self.n_customers)]

        self.data.current_state["firm_states"] = ["active", "passive"]
        self.data.current_state["n_client"] = [0, 0]
        self.data.current_state["firm_profits"] = [0, 0]
        self.data.current_state["firm_cumulative_profits"] = [0, 0]

        self.data.current_state["firm_positions"] = np.random.randint(1, self.game_parameters["n_positions"], size=2)
        self.data.current_state["firm_prices"] = np.random.randint(1, self.game_parameters["n_prices"], size=2)

        self.data.current_state["customer_extra_view_choices"] = np.zeros(self.game_parameters["n_customers"], dtype=int)
        self.data.current_state["customer_firm_choices"] = np.zeros(self.game_parameters["n_customers"], dtype=int)
        self.data.current_state["customer_utility"] = np.zeros(self.game_parameters["n_customers"], dtype=int)
        self.data.current_state["customer_replies"] = np.zeros(self.game_parameters["n_customers"], dtype=int)

        self.launch_bots()

    def load(self):
        """called if a previous game is loaded"""

        self.data.setup()
        self.interface_parameters = self.data.parametrization
        self.assignement = self.data.assignement

        self.launch_bots()

    def launch_bots(self):
        """launch bots based on assignement settings"""

        n_firms = 0
        n_customers = 0
        n_agents_to_wait = 0

        for server_id, role, bot in self.assignement:
            if bot:
                n_firms += role == "firm"
                n_customers += role == "customer"
            else:
                n_agents_to_wait += 1

        if n_firms > 0 or n_customers > 0:
            bots = HotellingLocalBots(self.controller, n_firms, n_customers, n_agents_to_wait)
            bots.start()

    # ------------------------------- network related method ----------------------------------------- #

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))
        self.log("CURRENT STATE: {}".format(self.time_manager.state))

        # save data in case server shuts down
        self.data.save()

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        # retrieve method
        command = eval("self.{}".format(whole[0]))

        # retrieve method arguments
        args = [int(a) if a.isdigit() else a for a in whole[1:]]

        # don't launch methods if init is not done
        if not self.data.current_state["init_done"] and command != self.ask_init:
            to_client = "error/wait_init"

        # regular launch method
        else:
            to_client = command(*args)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))

        # save in case server shuts down
        self.data.save()

        return to_client

    # ----------------------- game sides methods ------------------------------------------- #

    def compute_utility(self):

        uc = self.interface_parameters["utility_consumption"]
        ec = self.interface_parameters["exploration_cost"]
        firm_choices = self.data.current_state["customer_firm_choices"]
        view_choices = self.data.current_state["customer_extra_view_choices"]
        prices = self.data.current_state["firm_prices"]

        utility = [int(firm_choices[i] >= 0) * uc - ((ec * view_choices[i]) + prices[firm_choices[i]])
                  for i in self.data.customers_id.values()]

        self.data.current_state["customer_utility"] = utility

    def get_role(self, server_id):

        for idx, role, bot in self.assignement:
            if idx == str(server_id):
                return role

        self.log("Error: no server_id found for asking client!")
        self.log("Reason: Perhaps server ids set in assignement menu were not the right ones!")

    def get_opponent_choices(self, opponent_id):

        if self.time_manager.t == 0:
            opponent_choices = [
                self.data.current_state[key][opponent_id]
                for key in ["firm_positions", "firm_prices"]
            ]
        else:
            opponent_choices = [
                self.data.history[key][self.time_manager.t - 1][opponent_id]
                for key in ["firm_positions", "firm_prices"]
            ]

        return opponent_choices[0], opponent_choices[1]

    def get_nb_of_clients(self, firm_id, opponent_id, t):
        """get own and opponent number of clients"""

        if self.time_manager.t == t:
            firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        else:
            firm_choices = np.asarray(self.data.history["customer_firm_choices"][t])

        cond = firm_choices == firm_id
        n = sum(cond)

        cond = firm_choices == opponent_id
        n_opp = sum(cond)

        return n, n_opp

    # -------------------------------- one liner methods ------------------------------------------ #
    def check_end(self, client_t):
        return int(client_t == self.time_manager.ending_t) if self.time_manager.ending_t else 0

    @staticmethod
    def reply(*args):
        return "reply/{}".format("/".join(
            [str(a) if type(a) in (int, np.int64) else a.replace("ask", "reply") for a in args]
        ))

    # ----------------------------------- all devices demands --------------------------------------#

    def ask_init(self, android_id):

        server_id, game_id = self.controller.id_manager.get_ids_from_android_id(android_id, max_n=len(self.data.roles))

        if game_id != -1:

            role = self.get_role(server_id)

            if not role:
                return "Unknown server id: {}".format(server_id)

            self.data.roles[game_id] = role
            
            if role == "firm":
                return self.init_firms(function_name(), game_id, role)

            else:
                return self.init_customers(function_name(), game_id, role)

        else:
            return "Error with ID manager. Maybe not authorized to participate."

    def init_customers(self, func_name, game_id, role):

        if game_id not in self.data.customers_id.keys():
            customer_id = len(self.data.customers_id)
            self.data.customers_id[game_id] = customer_id

        else:
            customer_id = self.data.customers_id[game_id]

        position = customer_id + 1
        exploration_cost = self.interface_parameters["exploration_cost"]
        utility_consumption = self.interface_parameters["utility_consumption"]
        utility = self.data.current_state["customer_utility"][customer_id]

        # self.data.current_state["connected_customers"][customer_id] = " ✔ "

        self.check_remaining_agents()

        return self.reply(func_name, game_id, self.time_manager.t, role, position, exploration_cost,
                utility_consumption, utility)

    def init_firms(self, func_name, game_id, role):

        if game_id not in self.data.firms_id.keys():
            firm_id = len(self.data.firms_id)
            self.data.firms_id[game_id] = firm_id

        # if device already asked for init, get id
        else:
            firm_id = self.data.firms_id[game_id]

        opponent_id = (firm_id + 1) % 2

        state = self.data.current_state["firm_states"][firm_id]

        position = self.data.current_state["firm_positions"][firm_id]
        price = self.data.current_state["firm_prices"][firm_id]
        opp_position = self.data.current_state["firm_positions"][opponent_id]
        opp_price = self.data.current_state["firm_prices"][opponent_id]
        profits = self.data.current_state["firm_cumulative_profits"][firm_id]

        # self.data.current_state["connected_firms"][firm_id] = " ✔ "

        self.check_remaining_agents()

        return self.reply(func_name, game_id, self.time_manager.t, role, position, state, price,
                          opp_position, opp_price, profits)

    def check_remaining_agents(self):

        remaining = self.n_agents - (len(self.data.firms_id) + len(self.data.customers_id))

        self.log("Number of missing agents: {}".format(remaining))

        if not remaining:
            self.data.current_state["init_done"] = True
            self.time_manager.check_state()

    # ----------------------------------- customer demands --------------------------------------#

    def ask_customer_firm_choices(self, game_id, t):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks for firm choices as t {}.".format(customer_id, t))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:
            if self.time_manager.state == "active_has_played":

                x = self.data.current_state["firm_positions"]
                prices = self.data.current_state["firm_prices"]

                return self.reply(function_name(), self.time_manager.t, x[0], x[1], prices[0], prices[1])
            else:
                return "error/wait"

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:
            x = self.data.history["firm_positions"][t]
            prices = self.data.history["firm_prices"][t]

            return self.reply(function_name(), t, x[0], x[1], prices[0], prices[1])

    def ask_customer_choice_recording(self, game_id, t, extra_view, firm):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks for recording his choice as t {}: "
                 "{} for extra view, {} for firm.".format(game_id, t, extra_view, firm))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            if not self.data.current_state["customer_replies"][customer_id]:

                self.data.current_state["customer_replies"][customer_id] = 1

                self.data.current_state["customer_extra_view_choices"][customer_id] = extra_view

                if firm != '-1':
                    self.data.current_state["customer_firm_choices"][customer_id] = firm
                else:
                    self.data.current_state["customer_firm_choices"][customer_id] = -1

                self.compute_utility()

                self.time_manager.check_state()

            else:
                self.log("Customer {} asks for recording his choice as t {} but already replied"
                         .format(game_id, t, extra_view, firm))

            return self.reply(function_name(), self.time_manager.t, self.check_end(t))

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:
            return self.reply(function_name(), t, self.check_end(t))

    # ----------------------------------- passive firm demands -------------------------------------- #
    
    def ask_firm_passive_opponent_choice(self, game_id, t):
        """called by a passive firm"""

        firm_id = self.data.firms_id[game_id]
        opponent_id = (firm_id + 1) % 2
        self.log("Firm passive {} asks for opponent strategy.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played" or \
            self.time_manager.state == "active_has_played_and_all_customers_replied":

                out = self.reply(
                    function_name(),
                    self.time_manager.t,
                    self.data.current_state["firm_positions"][opponent_id],
                    self.data.current_state["firm_prices"][opponent_id],
                )

                self.time_manager.check_state()
                return out

            else:
                return "error/wait"

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:

            return self.reply(
                    function_name(),
                    t,
                    self.data.history["firm_positions"][t][opponent_id],
                    self.data.history["firm_prices"][t][opponent_id],
                )

    def ask_firm_passive_n_clients(self, game_id, t):

        firm_id = self.data.firms_id[game_id]
        opponent_id = (firm_id + 1) % 2

        self.log("Firm passive {} asks for its number of clients.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:
            if self.time_manager.state == "active_has_played_and_all_customers_replied":
                if not self.data.current_state["passive_gets_results"]:

                    price = self.data.current_state["firm_prices"][firm_id]

                    n, n_opp = self.get_nb_of_clients(firm_id, opponent_id, t)

                    out = self.reply(function_name(), self.time_manager.t, n, n_opp, self.check_end(t))

                    self.data.current_state["firm_cumulative_profits"][firm_id] += n * price
                    self.data.current_state["firm_profits"][firm_id] = n * price
                    self.data.current_state["n_client"][firm_id] = n
                    self.data.current_state["passive_gets_results"] = True

                    self.time_manager.check_state()

                    return out

            else:
                return "error/wait"

        elif t > self.time_manager.t:
            return "error/time_is_superior"
        
        else:
            n, n_opp = self.get_nb_of_clients(firm_id, opponent_id, t)
            return self.reply(function_name(), t, n, n_opp, self.check_end(t))

    # ----------------------------------- active firm demands -------------------------------------- #
    def ask_firm_active_choice_recording(self, game_id, t, position, price):
        """called by active firm"""

        firm_id = self.data.firms_id[game_id]

        self.log("Firm active {} asks to save its price and position.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            out = self.reply(function_name(), self.time_manager.t)

            if not self.data.current_state["active_replied"]:

                # Register choice
                opponent_id = (firm_id + 1) % 2
                opponent_pos, opponent_price = self.get_opponent_choices(opponent_id)
                

                for ids, pos, px in [(firm_id, position, price), (opponent_id, opponent_pos, opponent_price)]:
                    self.data.current_state["firm_positions"][int(ids)] = pos
                    self.data.current_state["firm_prices"][int(ids)] = px

                # check state
                self.data.current_state["active_replied"] = True
                self.time_manager.check_state()

            return out

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:
            return self.reply(function_name(), t)

    def ask_firm_active_n_clients(self, game_id, t):
        """called by active firm"""

        firm_id = self.data.firms_id[game_id]
        opponent_id = (firm_id + 1) % 2

        self.log("Firm active {} asks the number of its clients.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played_and_all_customers_replied":

                n, n_opp = self.get_nb_of_clients(firm_id, opponent_id, t)

                out = self.reply(function_name(), self.time_manager.t, n, n_opp, self.check_end(t))

                price = self.data.current_state["firm_prices"][firm_id]

                self.data.current_state["firm_cumulative_profits"][firm_id] += n * price
                self.data.current_state["firm_profits"][firm_id] = n * price
                self.data.current_state["n_client"][firm_id] = n
                self.data.current_state["active_gets_results"] = True

                self.time_manager.check_state()

                return out

            else:
                return "error/wait"

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:
            n, n_opp = self.get_nb_of_clients(firm_id, opponent_id, t)
            return self.reply(function_name(), t, n, n_opp, self.check_end(t))
