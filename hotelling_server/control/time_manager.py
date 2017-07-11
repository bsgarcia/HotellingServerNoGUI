import numpy as np

from utils.utils import Logger


class TimeManager(Logger):

    def __init__(self, controller):
        self.controller = controller
        self.data = controller.data
        self.state = ""
        self.t = 0

    def setup(self):
        self.state = self.data.time_manager_state
        self.log("NEW STATE: {}.".format(self.state))
        self.t = self.data.time_manager_t
        self.end = False
        self.continue_game = True
        self.beginning_time_step()
        self.log("Players already inititialized: {}".format(self.data.current_state["init_done"]))

    def check_state(self):
        if self.state == "beginning_init":
            if self.data.current_state["init_done"]:
                self.state = "beginning_time_step"
                self.log("NEW STATE: {}.".format(self.state))

        elif self.state == "beginning_time_step":
            if self.data.current_state["active_replied"]:
                self.state = "active_has_played"
                self.log("NEW STATE: {}.".format(self.state))

        elif self.state == "active_has_played":
            if np.sum(self.data.current_state["customer_replies"]) == self.data.param["game"]["n_customers"]:
                self.state += "_and_all_customers_replied"
                self.log("NEW STATE: {}.".format(self.state))

        elif self.state == "active_has_played_and_all_customers_replied":
            if self.data.current_state["passive_gets_results"] and self.data.current_state["active_gets_results"]:

                self.state = "end_time_step"
                self.log("NEW STATE: {}.".format(self.state))
                self.end_time_step()

                if self.continue_game:
                    self.beginning_time_step()
                    self.state = "beginning_time_step"
                    self.log("NEW STATE: {}.".format(self.state))

    def beginning_time_step(self):

        self.data.current_state["customer_replies"] = np.zeros(self.data.param["game"]["n_customers"])
        self.data.current_state["active_replied"] = False
        self.data.current_state["passive_gets_results"] = False
        self.data.current_state["active_gets_results"] = False

    def end_time_step(self):

        self.log("Game server goes next step.")
        self.data.update_history()

        if not self.continue_game:
            self.state = "beginning_time_step"
            self.controller.queue.put(("game_stop_game", ))
            self.end = True

        self.t += 1

    def stop_as_soon_as_possible(self):
        self.continue_game = False
