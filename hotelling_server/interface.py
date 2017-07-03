import json
from multiprocessing import Queue, Event

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QMessageBox

from .graphics import game_view, loading_view, parametrization_view, setting_up_view
from utils.utils import log


class Communicate(QObject):
    signal = pyqtSignal()


class UI(QWidget):

    name = "Interface"

    dimensions = 300, 100, 2000, 1000
    app_name = "Android Experiment"

    def __init__(self, model):

        # noinspection PyArgumentList
        QWidget.__init__(self)

        self.mod = model
        
        self.occupied = Event()

        self.layout = QVBoxLayout()

        self.frames = dict()

        self.already_asked_for_saving_parameters = 0

        self.queue = Queue()
        self.communicate = Communicate()

        self.controller_queue = None

    def setup(self):

        self.controller_queue = self.mod.controller.queue

        self.frames["parameters"] = \
            parametrization_view.ParametersFrame(parent=self, controller_queue=self.controller_queue)
        self.frames["game"] = \
            game_view.GameFrame(parent=self, controller_queue=self.controller_queue)
        self.frames["setting_up"] = \
            setting_up_view.SettingUpFrame(parent=self)
        self.frames["load_game_new_game"] = \
            loading_view.LoadGameNewGameFrame(parent=self, controller_queue=self.controller_queue)

        self.initialize()

    def initialize(self):

        self.setWindowTitle(self.app_name)

        self.communicate.signal.connect(self.look_for_msg)

        self.setGeometry(*self.dimensions)

        grid = QGridLayout()

        for frame in self.frames.values():

            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            grid.addWidget(frame, 0, 0)

        grid.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(grid, stretch=1)

        self.setLayout(self.layout)

        self.controller_queue.put(("interface", "running"))

    def closeEvent(self, event):

        if self.isVisible() and self.show_question("Are you sure you want to quit?"):

            if not self.already_asked_for_saving_parameters:

                self.check_for_saving_parameters()

            log("Close window", name=self.name)
            self.controller_queue.put(("interface", "close"))
            event.accept()

        else:
            log("Ignore close window.", name=self.name)
            event.ignore()

    def check_for_saving_parameters(self):

        self.already_asked_for_saving_parameters = 1

        if sorted(self.mod.controller.parameters.param["game"].items()) != \
                sorted(self.frames["parameters"].get_parameters().items()):

            if self.show_question("Do you want to save the change in parameters?"):

                self.mod.controller.parameters.save("game", self.frames["parameters"].get_parameters())

                log('Parameters saved.', name=self.name)

            else:
                log('Saving of parameters aborted.', name=self.name)

    def show_load_game_new_game_frame(self):

        for frame in self.frames.values():
            frame.hide()

        self.frames["load_game_new_game"].prepare()
        self.frames["load_game_new_game"].show()

    def show_experimental_frame(self):

        self.frames["game"].prepare()

        for frame in self.frames.values():
            frame.hide()

        self.frames["game"].show()

    def show_setting_up_frame(self):

        for frame in self.frames.values():
            frame.hide()

        self.frames["setting_up"].show()

    def show_parameters_frame(self):

        for frame in self.frames.values():
            frame.hide()

        self.frames["parameters"].prepare()
        self.frames["parameters"].show()

    def show_question(self, instructions):

        # noinspection PyCallByClass, PyTypeChecker
        button_reply = \
            QMessageBox.question(
                self, '', instructions,  # parent, title, msg
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No  # buttons, default button
            )

        return button_reply == QMessageBox.Yes

    def show_warning(self, **instructions):

        button_reply = QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )
        return button_reply == QMessageBox.Yes

    def show_critical_and_retry(self, msg):

        button_reply = QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close | QMessageBox.Retry,  # Buttons
            QMessageBox.Retry  # Default button
        )

        return button_reply == QMessageBox.Retry

    def show_critical_and_ok(self, msg):

        button_reply = QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close | QMessageBox.Ok,  # Buttons
            QMessageBox.Ok  # Default button
        )

        return button_reply == QMessageBox.Ok

    def manage_error_load_session(self):

        self.show_warning(msg="Error in loading the selected file. Please select another one!")
        self.frames["setting_up"].show()
        self.frames["load_game_new_game"].open_file_dialog()

    def manage_server_error(self):

        retry = self.show_critical_and_retry(msg="Server error.")

        if retry:
            self.show_setting_up_frame()
            self.controller_queue.put(("interface", "retry"))

        else:
            if not self.close():
                self.manage_server_error()

    def manage_fatal_error_of_communication(self):

        ok = self.show_critical_and_ok(msg="Fatal error of communication. You need to relaunch the game AFTER "
                                           "having relaunched the apps on Android's clients.")

        if ok:
            self.show_load_game_new_game_frame()

        else:
            if not self.close():
                self.manage_fatal_error_of_communication()

    def look_for_msg(self):

        if not self.occupied.is_set():
            self.occupied.set()

            msg = self.queue.get()
            log("I received message '{}'.".format(msg), self.name)

            instruction = msg[0]

            if instruction == "fatal_error_of_communication":
                self.manage_fatal_error_of_communication()

            elif instruction == "error_load_session":
                self.manage_error_load_session()

            elif instruction == "server_error":
                self.manage_server_error()

            elif instruction == "show_experimental_frame":
                self.show_experimental_frame()

            elif instruction == "show_setting_up_frame":
                self.show_setting_up_frame()

            elif instruction == "show_parameters_frame":
                self.show_parameters_frame()

            elif instruction == "show_load_game_new_game":
                self.show_load_game_new_game_frame()

            elif instruction == "update_stop_button_experimental_frame":
                self.frames["game"].update_stop_button()

            elif instruction == "update_statistics":
                statistics = msg[1]
                self.frames["game"].update_statistics(statistics)

            elif instruction == "update_done_playing":
                done_playing = msg[1]
                self.frames["game"].update_done_playing(done_playing)

            elif instruction == "update_done_playing_labels":
                done_playing_labels = msg[1]
                self.frames["game"].update_done_playing_labels(done_playing_labels)

            else:
                raise Exception(
                    "{}: Received instruction '{}' but did'nt expected anything like that."
                    .format(self.name, instruction))
            
            # Able now to handle a new display instruction
            self.occupied.clear()

        else:
            # noinspection PyCallByClass, PyTypeChecker
            QTimer.singleShot(100, self.look_for_msg)
