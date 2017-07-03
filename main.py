from multiprocessing import Queue
import sys
from PyQt5.QtWidgets import QApplication

from interface.interface import Interface, Communicate
from management.senior_manager import SeniorManager


def main():

    manager_queue = Queue()

    communicate = Communicate()
    graphic_queue = Queue()

    senior_manager = SeniorManager(
        manager_queue=manager_queue,
        graphic_queue=graphic_queue,
        communicate=communicate
    )

    senior_manager.start()

    app = QApplication(sys.argv)
    window = Interface(manager_queue=manager_queue, graphic_queue=graphic_queue, communicate=communicate)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":

    main()


