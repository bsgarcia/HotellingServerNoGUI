from os import getenv
from multiprocessing import Queue, Event

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QMessageBox, QDesktopWidget

from .graphics import game_view, loading_view, parametrization_view, setting_up_view, assignement_view
from utils.utils import Logger


class Communicate(QObject):
    signal = pyqtSignal()


class UI(QWidget, Logger):

    name = "Interface"
    app_name = "Android Experiment"

    def __init__(self, model):

        # noinspection PyArgumentList
        QWidget.__init__(self)

        self.mod = model

        self.occupied = Event()

        self.layout = QVBoxLayout()

        self.frames = dict()

        # refresh interface and update data
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_tables)
        self.timer.start()

        self.already_asked_for_saving_parameters = 0

        self.queue = Queue()

        self.communicate = Communicate()

        self.controller_queue = None

    @property
    def dimensions(self):

        desktop = QDesktopWidget()
        dimensions = desktop.screenGeometry()
        w = dimensions.width() * 0.9
        h = dimensions.height() * 0.8

        return 300, 100, w, h

    def setup(self):

        self.controller_queue = self.mod.controller.queue

        self.frames["assign"] = \
                assignement_view.AssignementFrame(parent=self)

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

        cond1 = sorted(self.mod.controller.data.param["parametrization"].items()) != \
                sorted(self.frames["parameters"].get_parameters().items())

        cond2 = sorted(self.mod.controller.data.param["assignement"]) != \
                sorted(self.frames["assign"].get_parameters())

        if cond1 or cond2:

            if self.show_question("Do you want to save the change in parameters and assignement?"):

                self.save_parameters("parametrization", self.frames["parameters"].get_parameters())
                self.save_parameters("assignement", self.frames["assign"].get_parameters())

            else:
                self.log('Saving of parameters aborted.')

    def update_figures(self, *args):

        data = self.mod.controller.get_current_data()["statistics"]
        self.frames["game"].update_statistics(data)

    def update_tables(self, *args):

        data = self.mod.controller.get_current_data()
        self.frames["game"].update_state_table(data)
        self.frames["game"].set_trial_number(data["time_manager_t"])

    def show_frame_load_game_new_game(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["load_game_new_game"].prepare()
        self.frames["load_game_new_game"].show()

    def show_frame_game(self, *args):

        self.frames["game"].prepare(args[0])

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

    def show_frame_assignement(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["assign"].prepare()
        self.frames["assign"].show()

    def show_question(self, instructions):

        # noinspection PyCallByClass, PyTypeChecker
        button_reply = \
            QMessageBox.question(
                self, '', instructions,  # parent, title, msg
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No  # buttons, default button
            )

        return button_reply == QMessageBox.Yes

    def show_question_and_quit_game(self, instructions):

        msgbox = QMessageBox()
        msgbox.setText(instructions)
        msgbox.setText("Do you want to quit game?")
        msgbox.setIcon(QMessageBox.Question)
        quit = msgbox.addButton("Force to quit", QMessageBox.ActionRole)
        msgbox.addButton("Do not quit", QMessageBox.ActionRole)

        msgbox.exec_()

        return msgbox.clickedButton() == quit

    def show_warning(self, msg):

        button_reply = QMessageBox().warning(
            self, "", msg,
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

    def show_critical(self, msg):

        QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close
        )

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

    def fatal_error(self, error_message):

        self.show_critical(msg="Server error.\nError message: '{}'.".format(error_message))
        self.close_window()
        self.close()

    def force_to_quit_game(self, msg):

        quit = self.show_question_and_quit_game(instructions=msg)

        if quit:
            self.show_frame_load_game_new_game()
            self.controller_queue.put(("stop_server", ))
            self.stop_bots()

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
        return self.mod.controller.data.param["parametrization"]

    def get_current_interface_parameters(self):
        return {"parametrization": self.frames["parameters"].get_parameters(),
                "assignement": self.frames["assign"].get_parameters()}

    def get_game_parameters(self):
        return self.mod.controller.data.param["game"]

    def run_game(self):
        self.controller_queue.put(("ui_run_game", self.get_current_interface_parameters()))

    def load_game(self, file):
        self.controller_queue.put(("ui_load_game", file))

    def stop_game(self):
        self.controller_queue.put(("ui_stop_game", ))

    def close_window(self):
        self.controller_queue.put(("ui_close_window", ))

    def retry_server(self):
        self.controller_queue.put(("ui_retry_server", ))

    def save_parameters(self, key, data):
        self.controller_queue.put(("ui_save_game_parameters", key, data))

    def send_go_signal(self):
        self.controller_queue.put(("ui_send_go_signal", ))

    def send_reboot_signal(self):
        self.controller_queue.put(("reboot", ))

    def stop_bots(self):
        self.controller_queue.put(("ui_stop_bots", ))

    def look_for_alive_players(self):
        self.controller_queue.put(("ui_look_for_alive_players", ))

