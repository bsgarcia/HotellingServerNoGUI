import numpy as np

from utils.utils import Logger


class TimeManager(Logger):
    def __init__(self, controller):
        self.controller = controller
        self.data = controller.data
        self.state = "beginning_init"
        self.data.current_state["init_done"] = False
        self.log("NEW STATE: {}.".format(self.state))
        self.t = 0
        self.continue_game = True

    def setup(self):
        self.beginning_time_step()

    def restart(self):
        self.state = "beginning_time_step"
        self.continue_game = True

    def check_state(self):
        if self.state == "beginning_init":
            if self.data.current_state["init_done"]:
                self.state = "beginning_time_step"
                self.log("NEW STATE: {}.".format(self.state))

        if self.state == "beginning_time_step":
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

        self.data.save()

        if not self.continue_game:
            self.controller.queue.put(("game_stop_game", ))
        else:
            self.data.update_history()
        
        self.t += 1

    def stop_as_soon_as_possible(self):
        self.continue_game = False
