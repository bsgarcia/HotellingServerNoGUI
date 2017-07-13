from pylab import np, plt
from utils.utils import Logger


class Statistician(Logger):

    def __init__(self, controller):

        self.controller = controller
        self.data = {}
        self.pos = [[], []]
        self.profits = [[], []]
        self.mean_extra_view_choices = []
        self.mean_utility = []

    def compute_distance(self):

        pos = self.controller.data.current_state["firm_positions"]

        for i in range(len(self.pos)):
            self.pos[i].append(pos[i])

        self.data["firm_distance"] = self.pos

    def compute_mean_extra_view_choices(self):

        mean = np.mean(self.controller.data.current_state["customer_extra_view_choices"])

        self.mean_extra_view_choices.append(mean)

        self.data["customer_mean_extra_view_choices"] = self.mean_extra_view_choices

    def compute_profits(self):

        profits = self.controller.data.current_state["firm_profits"]

        for i in range(len(self.profits)):
            self.profits[i].append(profits[i])

        self.data["firm_profits"] = self.profits

    def compute_mean_utility(self):

        mean = np.mean(self.controller.data.current_state["customer_utility"])

        self.mean_utility.append(mean)

        self.data["customer_mean_utility"] = self.mean_utility
