import sys
from . import controller


class Model:
    """Model class.
    Create the elements of the model, orchestrate their interactions.
    """

    def __init__(self):

        self.controller = controller.Controller(model=self)

    def run(self):

        try:

            self.controller.start()

        except Exception as e:

            print(str(e))
