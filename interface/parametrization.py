from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QPushButton, QLabel, QCheckBox, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
from collections import OrderedDict
import json


from utils.utils import log


class ParametersFrame(QWidget):

    name = "ParametersFrame"

    def __init__(self, parent, manager_queue):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.layout = QVBoxLayout()

        self.manager_queue = manager_queue

        self.parameters = OrderedDict()

        with open("parameters/parameters.json") as param_file:

            param = json.load(param_file)

        self.parameters["x1"] = \
            IntParameter(
                text="x1", initial_value=param["x1"],
                value_range=[0, 10**3])

        self.parameters["x2"] = \
            IntParameter(
                text="x2", initial_value=param["x2"],
                value_range=[0, 10**3])

        self.parameters["x3"] = \
            IntParameter(
                text="x3", initial_value=param["x3"],
                value_range=[0, 10**3])

        self.parameters["save"] = \
            CheckParameter(text="Save results", checked=param["save"])

        self.parameters["random"] = \
            CheckParameter(text="Random results", checked=param["random"])

        self.parameters["local"] = \
            CheckParameter(text="Local server", checked=param["local"])

        self.run_button = QPushButton("Run!")

        self.initialize()

    def initialize(self):

        form_layout = QFormLayout()

        for p in self.parameters.keys():

            self.parameters[p].add_to_layout(form_layout)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

        # noinspection PyUnresolvedReferences
        self.run_button.clicked.connect(self.push_run_button)

    def push_run_button(self):

        self.run_button.setEnabled(False)

        error, parameters = self.get_parameters()

        if error:

            self.show_warning(msg=error)

        else:
            log("Push 'run' button.", name=self.name)

            # Communicate parameters through the queue
            self.manager_queue.put(("parameters_frame", "parameters", parameters))

    def get_parameters(self):

        parameters = {}

        error = 0
        for parameter_name in self.parameters:

            value = self.parameters[parameter_name].get_value()
            if type(value) == str and value[0] == "!":

                error = value[1:]
                break
            else:
                parameters[parameter_name] = value

        return error, parameters

    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def prepare(self):

        self.setFocus()
        self.run_button.setFocus()
        self.run_button.setEnabled(True)


class IntParameter(object):

    def __init__(self, text, initial_value, value_range):

        self.initial_value = initial_value
        self.value_range = value_range

        self.label = QLabel(text)
        self.edit = QLineEdit(str(initial_value))

    def get_value(self):

        try:
            value = int(self.edit.text())

            if self.value_range[0] <= value <= self.value_range[1]:
                return value
            else:
                return "!Error: Value for '{}' should be an integer comprised in range {} - {}.".format(
                    self.label.text(), self.value_range[0], self.value_range[1]
                )

        except ValueError:

            return "!Error: Value given for '{}' should be an integer.".format(
                self.label.text()
            )

    def add_to_layout(self, layout):

        layout.addRow(self.label, self.edit)


class CheckParameter(object):

    def __init__(self, text, checked=True):

        self.label = QLabel(text)
        self.check_box = QCheckBox()

        self.check_box.setChecked(checked)

    def get_value(self):

        return self.check_box.isChecked()

    def add_to_layout(self, layout):

        layout.addRow(self.label, self.check_box)
