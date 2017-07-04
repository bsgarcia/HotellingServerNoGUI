class Data:

    def __init__(self, controller):

        self.controller = controller
        self.entries = [
            "firm_positions", "firm_prices", "firm_profits",
            "customer_firm_choices", "customer_extra_view_choices", "customer_utility"]
        self.history = {s: [] for s in self.entries}
        self.current_state = {s: [] for s in self.entries}

    def save(self):

        self.controller.backup.write(
            {
                "history": self.history,
                "current_state": self.current_state
            }
        )

    def update_history(self):

        for s in self.entries:
            self.history[s].append(self.current_state[s])

