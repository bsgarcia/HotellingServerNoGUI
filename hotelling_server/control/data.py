class Data:

    def __init__(self, controller):

        self.controller = controller

        self.entries = [
            "firm_positions", "firm_prices", "firm_profits",
            "customer_firm_choices", "customer_extra_view_choices", "customer_utility"]

        self.history = {s: [] for s in self.entries}
        self.current_state = {s: [] for s in self.entries}

        self.firms_id = {}  # key: game_id, value: firm_id
        self.customers_id = {}  # key: game_id, value: customer_id
        self.map_server_id_android_id = {}

        self.roles = []

    def save(self):

        self.controller.backup.write(
            {
                "history": self.history,
                "current_state": self.current_state,
                "firms_id": self.firms_id,
                "customers_id": self.customers_id,
                "map_server_id_android_id": self.map_server_id_android_id,
                "roles": self.roles
            }
        )

    def update_history(self):

        for s in self.entries:
            self.history[s].append(self.current_state[s])

    def write(self, key, game_id, value):

        self.current_state[key][game_id] = value

