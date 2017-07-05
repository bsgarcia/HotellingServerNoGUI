from os import path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog

from utils.utils import Logger


class LoadGameNewGameFrame(QWidget, Logger):

    name = "LoadGameNewGame"

    def __init__(self, parent):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.layout = QVBoxLayout()
        self.buttons = dict()

        self.setup()

    def setup(self):

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
        self.parent().show_frame_parameters()

    def click_load_game(self):

        self.set_buttons_activation(False)
        self.open_file_dialog()

    def set_buttons_activation(self, value):

        for b in self.buttons.values():
            b.setEnabled(value)

    def open_file_dialog(self):

        folder_to_open = path.expanduser(self.parent().mod.controller.data.param["folders"]["save"])

        # noinspection PyArgumentList
        file_choice = QFileDialog().getOpenFileName(
            self, '',
            folder_to_open,
            "Backup files (*.p)")
        self.log("User choose file '{}'.".format(file_choice))
        file = file_choice[0]
        if file:
            self.parent().load_game(file)

        else:
            self.set_buttons_activation(True)
