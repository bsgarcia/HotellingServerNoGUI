from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from os import path
import json

from utils.utils import log


class LoadGameNewGameFrame(QWidget):

    name = "LoadGameNewGame"

    def __init__(self, parent, manager_queue):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.manager_queue = manager_queue
        self.layout = QVBoxLayout()
        self.new_game_button = QPushButton("New game")
        self.load_game_button = QPushButton("Load game")

        with open("parameters/localization.json") as file:

            self.initial_save_folder = path.expanduser(json.load(file)["save"])

        self.initialize()

    def initialize(self):

        self.layout.addWidget(self.new_game_button, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.load_game_button, alignment=Qt.AlignCenter)
        self.setLayout(self.layout)

        # noinspection PyUnresolvedReferences
        self.new_game_button.clicked.connect(self.click_new_game)
        # noinspection PyUnresolvedReferences
        self.load_game_button.clicked.connect(self.click_load_game)

    def prepare(self):

        self.setFocus()
        self.new_game_button.setFocus()
        self.enable_push_buttons()

    def click_new_game(self):

        self.disable_push_buttons()
        self.manager_queue.put(("load_game_new_game", "new"))

    def click_load_game(self):

        self.disable_push_buttons()
        self.open_file_dialog()

    def disable_push_buttons(self):

        self.new_game_button.setEnabled(False)
        self.load_game_button.setEnabled(False)

    def enable_push_buttons(self):

        self.new_game_button.setEnabled(True)
        self.load_game_button.setEnabled(True)

    def open_file_dialog(self):

        # noinspection PyArgumentList
        file_choice = QFileDialog().getOpenFileName(self, '', self.initial_save_folder, "Backup files (*.p)")
        log("User choose file '{}'.".format(file_choice), self.name)
        file = file_choice[0]
        if file:
            self.manager_queue.put(("load_game_new_game", "file", file))

        else:
            self.enable_push_buttons()
