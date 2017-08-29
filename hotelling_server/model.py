import sys
from PyQt5.QtWidgets import QApplication

from hotelling_server.control import backup
from . import interface, controller


class Model:
    """Model class.

    Create the elements of the model, orchestrate their interactions.
    """

    def __init__(self):

        self.app = QApplication(sys.argv)
        self.ui = interface.UI(model=self)
        self.controller = controller.Controller(model=self)

    def run(self):
        try:
            self.controller.start()
            self.ui.setup()
            self.ui.show()
            sys.exit(self.app.exec_())

        except Exception as e:
            self.ui.server_error(msg=str(e))
