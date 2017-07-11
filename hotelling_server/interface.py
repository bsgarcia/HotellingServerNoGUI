from os import system, getenv
from multiprocessing import Queue, Event

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QMessageBox

from .graphics import game_view, loading_view, parametrization_view, setting_up_view
from utils.utils import Logger


class Communicate(QObject):
    signal = pyqtSignal()


class UI(QWidget, Logger):

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
            parametrization_view.ParametersFrame(parent=self)
        self.frames["game"] = \
            game_view.GameFrame(parent=self)
        self.frames["setting_up"] = \
            setting_up_view.SettingUpFrame(parent=self)
        self.frames["load_game_new_game"] = \
            loading_view.LoadGameNewGameFrame(parent=self)

        self.setWindowTitle(self.app_name)

        self.communicate.signal.connect(self.look_for_msg)
        
        if getenv("USER") == "getz":
            self.dimensions = 300, 100, 900, 450

        self.setGeometry(*self.dimensions)

        grid = QGridLayout()

        for frame in self.frames.values():

            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            grid.addWidget(frame, 0, 0)

        grid.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(grid, stretch=1)

        self.setLayout(self.layout)

        self.send_go_signal()

    def closeEvent(self, event):

        if self.isVisible() and self.show_question("Are you sure you want to quit?"):

            if not self.already_asked_for_saving_parameters:

                self.check_for_saving_parameters()

            self.log("Close window")
            self.close_window()
            event.accept()

        else:
            self.log("Ignore close window.")
            event.ignore()

    def check_for_saving_parameters(self):

        self.already_asked_for_saving_parameters = 1

        if sorted(self.mod.controller.data.param["interface"].items()) != \
                sorted(self.frames["parameters"].get_parameters().items()):

            if self.show_question("Do you want to save the change in parameters?"):

                self.save_parameters(self.frames["parameters"].get_parameters())

            else:
                self.log('Saving of parameters aborted.')

    def update_data_viewer(self, param):

        self.frames["game"].update_state_table(param)
        self.frames["game"].set_trial_number(param["time_manager_t"])
        self.frames["game"].update_statistics(param["statistics"])

    def show_frame_load_game_new_game(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["load_game_new_game"].prepare()
        self.frames["load_game_new_game"].show()

    def show_frame_game(self, *args):

        self.frames["game"].prepare()

        for frame in self.frames.values():
            frame.hide()

        self.frames["game"].show()

    def show_frame_setting_up(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["setting_up"].show()

    def show_frame_parameters(self, *args):

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

    def error_loading_session(self):

        self.show_warning(msg="Error in loading the selected file. Please select another one!")
        self.frames["setting_up"].show()
        self.frames["load_game_new_game"].open_file_dialog()

    def server_error(self, error_message):

        retry = self.show_critical_and_retry(msg="Server error.\nError message: '{}'.".format(error_message))

        if retry:
            self.show_frame_setting_up()
            self.retry_server()

        else:
            if not self.close():
                self.manage_server_error()

    def fatal_error_of_communication(self):

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
            self.log("I received message '{}'.".format(msg))

            command = eval("self.{}".format(msg[0]))
            args = msg[1:]
            if args:
                command(*args)
            else:
                command()
            
            # Able now to handle a new display instruction
            self.occupied.clear()

        else:
            # noinspection PyCallByClass, PyTypeChecker
            QTimer.singleShot(100, self.look_for_msg)

    def get_parameters(self):

        return self.mod.controller.data.param["interface"]

    # TODO: Replace all the following function by these two lines.
    # def ask_controller(self, instruction, arg=None):
    #
    #     self.graphic_queue.put((instruction, arg))

    def run_game(self):
        self.controller_queue.put(("ui_run_game", ))

    def load_game(self, file):
        self.controller_queue.put(("ui_load_game", file))

    def stop_game(self):
        self.controller_queue.put(("ui_stop_game", ))

    def close_window(self):
        self.controller_queue.put(("ui_close_window", ))

    def retry_server(self):
        self.controller_queue.put(("ui_retry_server", ))

    def save_parameters(self, param):
        self.controller_queue.put(("ui_save_game_parameters", param))

    def send_go_signal(self):
        self.controller_queue.put(("ui_send_go_signal", ))

