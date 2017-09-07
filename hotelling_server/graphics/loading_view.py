from os import path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QGridLayout, QCheckBox, QLineEdit, QLabel, QHBoxLayout

from utils.utils import Logger, get_local_ip


class LoadGameNewGameFrame(QWidget, Logger):

    name = "LoadGameNewGame"

    def __init__(self, parent):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()
        self.buttons = dict()
        self.widgets = dict()

        self.param = self.parent().mod.controller.get_parameters("network")

        self.setup()

    def setup(self):

        self.fill_layout()

        self.buttons["new"].clicked.connect(self.click_new_game)
        self.buttons["load"].clicked.connect(self.click_load_game)
        self.buttons["devices"].clicked.connect(self.click_devices)

    def fill_layout(self):

        grid_layout = QGridLayout()

        self.widgets["localhost"] = QCheckBox()
        self.widgets["ip_address"] = QLineEdit()
        
        # do ugly things to get the right alignement for each widget
        for i, (label, widget) in enumerate(self.widgets.items()):

            grid_layout.addWidget(QLabel(label), i, 0, alignment=Qt.AlignLeft)

            if label == "localhost":
                grid_layout.addWidget(widget, i, 1, alignment=Qt.AlignLeft)
            else:
                grid_layout.addWidget(widget, i, 1, alignment=Qt.AlignCenter)

        self.layout.addLayout(grid_layout)

        horizontal_layout = QHBoxLayout()

        self.buttons["new"] = QPushButton("New game")
        self.buttons["load"] = QPushButton("Load game")
        self.buttons["devices"] = QPushButton("Devices management")

        horizontal_layout.addWidget(self.buttons["new"], alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.buttons["load"], alignment=Qt.AlignCenter)

        self.layout.addLayout(horizontal_layout)
        self.layout.addWidget(self.buttons["devices"], alignment=Qt.AlignBottom)

        self.setLayout(self.layout)

    def prepare(self):

        self.setFocus()
        self.buttons["new"].setFocus()
        self.set_buttons_activation(True)
        self.prepare_network()

    def prepare_network(self):
        
        self.widgets["ip_address"].setText(get_local_ip())
        self.widgets["ip_address"].setEnabled(not self.param["local"])
        self.widgets["localhost"].setChecked(self.param["local"])
        self.widgets["localhost"].stateChanged.connect(self.switch_line_edit)

    def switch_line_edit(self):
        
        self.widgets["ip_address"].setEnabled(not self.widgets["localhost"].isChecked())

    def click_new_game(self):

        self.write_network_parameters()
        self.set_buttons_activation(False)
        self.parent().show_frame_assignement()

    def click_load_game(self):

        self.write_network_parameters()
        self.set_buttons_activation(False)
        self.open_file_dialog()

    def click_devices(self):

        self.set_buttons_activation(False)
        self.parent().show_frame_devices()

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

    def write_network_parameters(self):

        self.param["ip_address"] = self.widgets["ip_address"].text()
        self.param["local"] = self.widgets["localhost"].isChecked()

        self.parent().mod.controller.backup.save_param("network", self.param)
        self.parent().mod.controller.backup.save_param("network", self.param)
