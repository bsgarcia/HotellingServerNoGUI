from utils.utils import Logger
import numpy as np
from sys import _getframe as func


class Game(Logger):

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.command = None

        self.t = 0

        self.game_parameters = self.controller.data.param["game"]
        self.interface_parameters = self.controller.data.param["interface"]

        self.n_customers = self.game_parameters["n_customers"]
        self.n_firms = self.game_parameters["n_firms"]
        self.n_agents = self.n_firms + self.n_customers

        self.bot_customers = self.interface_parameters["bot_customers"]

        self.continue_game = True

        self.has_played = []

        self.data = self.controller.data

        self.save = None
    
    #----------------------------------- sides methods --------------------------------------#

    @staticmethod
    def get_name(arg):
        return arg.f_code.co_name

    def new(self):
        
        self.data.roles = ["firm_{}".format(("active", "passive")[i]) for i in range(self.n_firms)] + \
                          ["customer" for i in range(self.n_customers)]

        np.random.shuffle(self.data.roles)

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

    def end_time_step(self):
        
        self.log("Game server goes next step.")

        self.has_played = []
        self.t += 1
        self.data.update_history()

        if not self.continue_game:
            self.end_game()

    def switch_firms_role(self, game_id):

        boolean = self.data.roles[game_id] == "firm_active"

        new_role = ("firm_active", "firm_passive")[boolean]

        self.data.roles[game_id] = new_role

        return new_role

    def check_time_step(self, client_t):
        
        for i in range(150): 
            self.log("Time on server is '{}', client's time is '{}'".format(self.t, client_t))
        if not client_t == self.t:
            self.log("Time is not synchronized!")

    def get_opponent_choices(self, opponent_id):

        opponent_choices = [
            self.data.history[key][self.t - 1][opponent_id]
            for key in ["firm_positions", "firm_prices"]
        ]

        return opponent_choices[0], opponent_choices[1]

    @staticmethod
    def reply(*args):
        return "reply/{}".format("/".join([str(a) if type(a) == int else a.replace("ask", "reply") for a in args]))

    def stop_as_soon_as_possible(self):

        self.continue_game = False

    def end_game(self):

        self.controller.queue.put(("game_stop_game", ))
    
    #----------------------------------- clients demands --------------------------------------#

    def ask_init(self, android_id):

        game_id = self.controller.id_manager.get_game_id_from_android_id(android_id, max_n=len(self.data.roles))

        if game_id != -1:

            # pick role
            role = self.data.roles[game_id]

            if "firm" in role:
                return self.init_firms(self.get_name(func()), game_id, role)

            else:
                return self.init_customers(self.get_name(func()), game_id, role)
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

        return self.reply(func_name, game_id, self.t, role, position, exploration_cost, utility_consumption)

    def init_firms(self, func_name, game_id, role):

        firm_id = len(self.data.firms_id) if len(self.data.firms_id) != 0 else 0
        self.data.firms_id[game_id] = firm_id
        position = np.random.randint(self.n_customers)
        price = np.random.randint(self.n_customers)
        self.data.current_state["firm_positions"].append(position)
        self.data.current_state["firm_prices"].append(price)

        self.log("Number of missing agents: {}".format(len(self.data.roles) - (len(self.data.firms_id) +
            len(self.data.customers_id))))

        return self.reply(func_name, game_id, self.t, role, position, price)

    def ask_end_of_init(self, t, game_id, role, game_started):

        general_role = role[:4] if "firm" in role else role

        agent_id = eval("self.data.{}s_id[game_id]".format(general_role))

        self.log("{} {} asks for end of init.".format(role, agent_id))

        cond0 = len(self.data.firms_id) == self.n_firms

        cond1 = len(self.data.customers_id) == self.n_customers

        if game_id not in self.has_played:
            self.has_played.append(game_id)

        cond2 = len(self.has_played) == len(self.data.roles)

        self.log("{} are connected out of {}".format(len(self.has_played), self.n_agents))

        if cond0 and cond1 and cond2 or game_started:
            
            self.end_time_step()

            return self.reply("new_turn", self.t)
        else:
            return self.reply("wait", self.get_name(func()), t, game_id, role, game_started)

    def ask_end_of_turn(self, t, game_id, role):

        agent_id = eval("self.data.{}s_id[game_id]".format(role))

        self.log("{} {} asks for end of turn.".format(role, agent_id))

        current_state = self.data.current_state

        cond0 = all(
            [len(current_state[k]) == self.n_customers
             for k in ["customer_extra_view_choices", "customer_firm_choices"]]
        )

        cond1 = all(
            [len(current_state[k]) == self.n_firms
             for k in ["firm_positions", "firm_prices"]]
        )
       
        if game_id not in self.has_played:
            self.has_played.append(game_id)

        cond2 = len(self.has_played) == len(self.data.roles)

        self.log("{} agents have ended the turn out of {}.".format(len(self.has_played), self.n_agents))

        if cond0 and cond1 and cond2:

            self.end_time_step()

            return self.reply("new_turn", self.t)
        else:
            return self.reply("wait", self.get_name(func()), t, game_id, role)

    #----------------------------------- customer demands --------------------------------------#

    def ask_customer_firm_choices(self, game_id, t):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks for firms strategies.".format(customer_id))

        self.check_time_step(t)
       
        x = self.data.current_state["firm_positions"]
        prices = self.data.current_state["firm_prices"]

        return self.reply(self.get_name(func()), x[0], x[1], prices[0], prices[1])

    def ask_customer_choice_recording(self, game_id, t, extra_view, firm):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks to save its exploration perimeter and firm choice.".format(customer_id))

        self.check_time_step(t)

        self.data.current_state["customer_extra_view_choices"][customer_id] = extra_view
        self.data.current_state["customer_firm_choices"][customer_id] = firm


        return self.reply(self.get_name(func()))

    #----------------------------------- firm demands --------------------------------------#

    def ask_firm_opponent_choice(self, game_id, t):

        assert self.n_firms == 2, "only works if firms are 2"

        firm_id = self.data.firms_id[game_id]

        self.log("Firm {} asks for opponent strategy.".format(firm_id))

        self.check_time_step(t)

        # opponent_id = (self.data.firms_id[game_id] + 1) % 2
        opponent_id = [int(k) for k in self.data.firms_id.values() if k != str(firm_id)][0]

        return self.reply(
            self.get_name(func()),
            self.data.current_state["firm_positions"][opponent_id],
            self.data.current_state["firm_prices"][opponent_id],
        )

    def ask_firm_choice_recording(self, game_id, t, position, price):

        firm_id = self.data.firms_id[game_id]

        self.log("Firm {} asks to save its price and position.".format(firm_id))

        self.check_time_step(t)

        opponent_id = [int(k) for k in self.data.firms_id.values() if k != str(firm_id)][0]

        opponent_pos, opponent_price = self.get_opponent_choices(opponent_id)

        for ids, pos, px in [[firm_id, position, price], [opponent_id, opponent_pos, opponent_price]]:
            self.data.current_state["firm_positions"][int(ids)] = pos
            self.data.current_state["firm_prices"][int(ids)] = px

        return self.reply(self.get_name(func()))

    def ask_firm_n_clients(self, game_id, t):

        firm_id = self.data.firms_id[game_id]

        self.log("Firm {} asks the number of its clients.".format(firm_id))

        self.check_time_step(t)

        firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        cond = firm_choices == firm_id

        n = len(firm_choices[cond])

        return self.reply(self.get_name(func()), self.t, n)
   
    def ask_role(self, game_id, t):

        firm_id = self.data.firms_id[game_id]

        self.log("Firm {} asks for its role (active vs passive).".format(firm_id))

        self.check_time_step(t)
        
        return self.reply(self.get_name(func()), self.t, self.data.roles[game_id])

