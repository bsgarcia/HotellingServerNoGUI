import json
from os import path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog

from utils.utils import log


class LoadGameNewGameFrame(QWidget):

    name = "LoadGameNewGame"

    def __init__(self, parent, controller_queue):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.controller_queue = controller_queue
        self.layout = QVBoxLayout()

        self.buttons = dict()

        self.initialize()

    def initialize(self):

        self.buttons["new"] = QPushButton("New game")
        self.buttons["load"] = QPushButton("Load game")

        self.layout.addWidget(self.buttons["new"], alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons["load"], alignment=Qt.AlignCenter)
        self.setLayout(self.layout)

        # noinspection PyUnresolvedReferences
        self.buttons["new"].clicked.connect(self.click_new_game)
        # noinspection PyUnresolvedReferences
        self.buttons["load"].clicked.connect(self.click_load_game)

    def prepare(self):

        self.setFocus()
        self.buttons["new"].setFocus()
        self.set_buttons_activation(True)

    def click_new_game(self):

        self.set_buttons_activation(False)
        self.controller_queue.put(("load_game_new_game", "new"))

    def click_load_game(self):

        self.set_buttons_activation(False)
        self.open_file_dialog()

    def set_buttons_activation(self, value):

        for b in self.buttons.values():
            b.setEnabled(value)

    def open_file_dialog(self):

        folder_to_open = path.expanduser(self.parent().mod.controller.parameters.param["folders"]["save"])

        # noinspection PyArgumentList
        file_choice = QFileDialog().getOpenFileName(
            self, '',
            folder_to_open,
            "Backup files (*.p)")
        log("User choose file '{}'.".format(file_choice), self.name)
        file = file_choice[0]
        if file:
            self.controller_queue.put(("load_game_new_game", "file", file))

        else:
            self.set_buttons_activation(True)
