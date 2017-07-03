class Data:

    def __init__(self, controller):

        self.controller = controller
        self.entries = ["save"]
        self.data = {s: None for s in self.entries}
