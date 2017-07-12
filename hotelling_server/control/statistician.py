from pylab import np, plt
from utils.utils import Logger


class Statistician(Logger):

    def __init__(self,  controller):

        self.controller = controller
        self.data = {}
        self.pos = []

    def compute_distance(self):

        pos = self.controller.data.current_state["firm_positions"]
        t = self.controller.time_manager.t

        x = np.arange(t)
        y = abs(pos[0] - pos[1])

        self.pos.append(y)

        self.data["distance"] = (x, self.pos)
