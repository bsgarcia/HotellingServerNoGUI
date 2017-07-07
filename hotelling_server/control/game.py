from utils.utils import Logger, function_name
import numpy as np


class Game(Logger):

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.data = self.controller.data
        self.time_manager = self.controller.time_manager

        self.game_parameters = self.controller.data.param["game"]
        self.interface_parameters = self.controller.data.param["interface"]

        self.n_customers = self.game_parameters["n_customers"]
        self.n_firms = self.game_parameters["n_firms"]
        self.n_agents = self.n_firms + self.n_customers

        self.bot_customers = self.interface_parameters["bot_customers"]
        
        self.continue_game = True

        self.save = None

    # ----------------------------------- sides methods --------------------------------------#
    def new(self):
        
        self.data.roles = ["firm" for i in range(self.n_firms)] + \
                          ["customer" for i in range(self.n_customers)]

        np.random.shuffle(self.data.roles)
        np.random.shuffle(self.data.initial_firm_state)

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        try:
            # retrieve method
            self.command = eval("self.{}".format(whole[0]))

            # retrieve method arguments
            args = [int(a) if a.isdigit() else a for a in whole[1:]]

            # call method
            to_client = self.command(*args)

        except Exception as e:
            to_client = (
                "Command contained in request not understood: "
                "{}".format(str(e))
                )

        self.log("Reply '{}' to request '{}'.".format(to_client, request))

        return to_client

    def get_opponent_choices(self, opponent_id):

        opponent_choices = [
            self.data.history[key][self.time_manager.t - 1][opponent_id]
            for key in ["firm_positions", "firm_prices"]
        ]

        return opponent_choices[0], opponent_choices[1]

    @staticmethod
    def reply(*args):
        return "reply/{}".format("/".join([str(a) if type(a) == int else a.replace("ask", "reply") for a in args]))

   #  def stop_as_soon_as_possible(self):

        # self.continue_game = False

    # def end_game(self):

        # self.controller.queue.put(("game_stop_game", ))
    
    # ----------------------------------- clients demands --------------------------------------#

    def ask_init(self, android_id):

        game_id = self.controller.id_manager.get_game_id_from_android_id(android_id, max_n=len(self.data.roles))

        if game_id != -1:

            # pick role
            role = self.data.roles[game_id]

            if role == "firm":

                return self.init_firms(function_name(), game_id, role)

            else:
                return self.init_customers(function_name(), game_id, role)
        else:
            return "Error with ID manager. Maybe not authorized to participate."

    def init_customers(self, func_name, game_id, role):

        customer_id = len(self.data.customers_id) if len(self.data.customers_id) != 0 else 0
        self.data.customers_id[game_id] = customer_id
        position = customer_id + 1
        exploration_cost = self.interface_parameters["exploration_cost"]
        utility_consumption = self.interface_parameters["utility_consumption"]
        self.data.current_state["customer_extra_view_choices"].append(-1)
        self.data.current_state["customer_firm_choices"].append(-1)
        
        self.log("Number of missing agents: {}".format(len(self.data.roles) - (len(self.data.firms_id) +
            len(self.data.customers_id))))

        return self.reply(func_name, game_id, self.time_manager.t, role, position, exploration_cost, utility_consumption)

    def init_firms(self, func_name, game_id, role):

        firm_id = len(self.data.firms_id) if len(self.data.firms_id) != 0 else 0
        self.data.firms_id[game_id] = firm_id
        state = self.data.initial_firm_state[firm_id]  
        position = np.random.randint(self.n_customers)
        price = np.random.randint(self.n_customers)
        self.data.current_state["firm_positions"].append(position)
        self.data.current_state["firm_prices"].append(price)

        self.log("Number of missing agents: {}".format(len(self.data.roles) -
                                                       (len(self.data.firms_id) + len(self.data.customers_id))))

        return self.reply(func_name, game_id, self.time_manager.t, role, state, position, price)

    # ----------------------------------- customer demands --------------------------------------#

    def ask_customer_firm_choices(self, game_id, t):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks for recording his choice as t {}.".format(customer_id, t))

        if t == self.time_manager.t:
            if self.time_manager.state == "active_replied":
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

        if t == self.time_manager.t:

            if not self.data.current_state["customer_replies"][customer_id]:

                self.data.current_state["customer_replies"][customer_id] = 1

                self.data.current_state["customer_extra_view_choices"][customer_id] = extra_view
                self.data.current_state["customer_firm_choices"][customer_id] = firm
                self.time_manager.time_manager.check_state()

            return self.reply(function_name(), self.time_manager.t)

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:
            return self.reply(function_name(), t)

    # ----------------------------------- firm demands -------------------------------------- #

    def ask_firm_opponent_choice(self, game_id, t):
        """called by a passive firm"""

        firm_id = self.data.firms_id[game_id]
        opponent_id = (firm_id + 1) % 2
        self.log("Firm passive {} asks for opponent strategy.".format(firm_id))
        
        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played_and_all_customers_replied":

                # Get number of clients
                firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
                cond = firm_choices == firm_id
                n = sum(cond)

                self.data.current_state["passive_gets_results"] = True

                out = self.reply(
                    function_name(),
                    self.time_manager.t,
                    self.data.current_state["firm_positions"][opponent_id],
                    self.data.current_state["firm_prices"][opponent_id],
                    n
                )

                self.time_manager.check_state()
                return out

            else:
                return "error/wait"

        elif t > self.time_manager.t:
            return "error/time_is_superior"
            
        else:

            # Get number of clients
            firm_choices = np.asarray(self.data.history["customer_firm_choices"][t])
            cond = firm_choices == opponent_id
            n = sum(cond)

            return self.reply(
                    function_name(),
                    t,
                    self.data.history["firm_positions"][t][opponent_id],
                    self.data.history["firm_prices"][t][opponent_id],
                    n
                )

    def ask_firm_choice_recording(self, game_id, t, position, price):
        """called by active firm"""

        firm_id = self.data.firms_id[game_id]

        self.log("Firm {} asks to save its price and position.".format(firm_id))

        if t == self.time_manager.t:

            out = self.reply(function_name(), self.time_manager.t)

            if not self.data.current_state["active_replied"]:

                # Register choice
                opponent_id = (firm_id + 1) % 2
                opponent_pos, opponent_price = self.get_opponent_choices(opponent_id)

                for ids, pos, px in [[firm_id, position, price], [opponent_id, opponent_pos, opponent_price]]:
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

    def ask_firm_n_clients(self, game_id, t):
        """called by active firm"""

        firm_id = self.data.firms_id[game_id]

        self.log("Firm {} asks the number of its clients.".format(firm_id))

        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played_and_all_customers_replied":

                firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
                cond = firm_choices == firm_id
                n = sum(cond)
                
                out = self.reply(function_name(), self.time_manager.t, n)

                self.data.current_state["active_gets_results"] = True
                self.time_manager.check_state()

                return out

            else:
                return "error/wait"

        elif t > self.time_manager.t:
            return "error/time_is_superior"

        else:
            firm_choices = np.asarray(self.data.history["customer_firm_choices"][t])
            cond = firm_choices == firm_id
            n = sum(cond)

            return self.reply(function_name(), t, n)
