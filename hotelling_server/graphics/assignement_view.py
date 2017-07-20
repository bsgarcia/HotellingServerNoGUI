from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QPushButton,
        QLabel, QCheckBox, QLineEdit, QMessageBox, QGridLayout, QRadioButton, QButtonGroup, QHBoxLayout)

from utils.utils import Logger


class AssignementFrame(QWidget, Logger):

    name = "AssignementFrame"

    def __init__(self, parent):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.layout = QVBoxLayout()
        self.next_button = QPushButton("Next")
        self.parameters = dict()

        self.error = None

        self.setup()

    def setup(self):

        game_param = self.parent().get_game_parameters()

        roles = ["firm" for i in range(game_param["n_firms"])] \
                +["customer" for i in range(game_param["n_customers"])]

        n_agents = len(roles)


        labels = "Server id", "Firm " + " Customer", "Bot"

        self.parameters["assign"] = [[] for i in range(n_agents)]

        for i in range(n_agents):

            self.parameters["assign"][i].append(IntParameter(text=labels[0],
                initial_value="", value_range=[0, 1000]))

            self.parameters["assign"][i].append(RadioParameter(checked=roles[i]))

            self.parameters["assign"][i].append(CheckParameter(parent=self,
                checked=True, idx=i))

        # prepare layout
        grid_layout = QGridLayout()

        # add labels
        for y, label in enumerate(labels):
            grid_layout.addWidget(QLabel(label), 0, y)

        # grid layout coordinates
        coordinates = [(x, y) for x in range(1, n_agents + 1) for y in range(len(labels))]

        # parameters index
        index = [(i, j) for i in range(n_agents) for j in range(len(labels))]

        for (i, j), (x, y) in zip(index, coordinates):
            self.parameters["assign"][i][j].add_to_grid_layout(grid_layout, x, y)

        self.layout.addLayout(grid_layout)
        self.layout.addWidget(self.next_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

        self.next_button.clicked.connect(self.push_next_button)

    def push_next_button(self):

        self.next_button.setEnabled(False)

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'next' button.")

            self.parent().show_frame_parameters()

    def get_parameters(self):
        return [(i.get_value(), j.get_value(), k.get_value()) for i, j, k in self.parameters["assign"]]

    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def switch_line_state(self, idx):

        if self.parameters["assign"][idx][0].edit.isEnabled():
            self.parameters["assign"][idx][0].edit.setEnabled(False)

        else:
            self.parameters["assign"][idx][0].edit.setEnabled(True)

    def prepare(self):

        self.setFocus()
        self.next_button.setFocus()
        self.next_button.setEnabled(True)


class RadioParameter(object):

    def __init__(self, checked):

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()

        self.firm = QRadioButton()
        self.customer = QRadioButton()
        
        if checked == "customer":
            self.customer.setChecked(True)
        else:
            self.firm.setChecked(True)

        self.group.addButton(self.firm)
        self.group.addButton(self.customer)

        self.layout.addWidget(self.firm)
        self.layout.addWidget(self.customer)

    def get_value(self):

        return ("customer", "firm")[self.firm.isChecked()]

    def add_to_grid_layout(self, layout, x, y):

        layout.addLayout(self.layout, x, y)


class IntParameter(object):

    def __init__(self, text, initial_value, value_range):

        self.initial_value = initial_value
        self.value_range = value_range

        self.label = text
        self.edit = QLineEdit(str(initial_value))

    def get_value(self):

        try:
            value = int(self.edit.text())

            if self.value_range[0] <= value <= self.value_range[1]:
                return value
            else:
                return "!Error: Value for '{}' should be an integer comprised in range {} - {}.".format(
                    self.label, self.value_range[0], self.value_range[1]
                )

        except ValueError:

            return "!Error: Value given for '{}' should be an integer.".format(
                self.label
            )

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.edit, x, y)


class CheckParameter(object):

    def __init__(self, parent, checked, idx):

        self.parent = parent
        self.idx = idx
        self.check_box = QCheckBox()

        self.check_box.stateChanged.connect(lambda: self.parent.switch_line_state(self.idx))

        self.check_box.setChecked(checked)

    def get_value(self):

        return self.check_box.isChecked()

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.check_box, x, y)

