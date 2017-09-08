from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QLabel, QAbstractItemView
import numpy as np

from hotelling_server.graphics.widgets.plot_layouts import PlotLayout
from hotelling_server.graphics.widgets.plot import OneLinePlot, TwoLinesPlot
from hotelling_server.graphics.widgets.trial_counter import TrialCounter
from utils.utils import Logger


class AddDevices(QWidget, Logger):

    name = "AddDevices"

    def __init__(self, parent):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()
        
        self.controller = parent.mod.controller 

        self.cancel_button = QPushButton()
        self.save_button = QPushButton()
        self.add_button = QPushButton()

        self.table = QTableWidget()

        self.setup()

    def setup(self):

        self.setLayout(self.layout)

        # add tables
        self.layout.addWidget(self.table)

        self.layout.addWidget(self.cancel_button, alignment=Qt.AlignBottom)
        self.layout.addWidget(self.add_button, alignment=Qt.AlignBottom)
        self.layout.addWidget(self.save_button, alignment=Qt.AlignBottom)

        # noinspection PyUnresolvedReferences
        self.cancel_button.clicked.connect(self.push_cancel_button)
        
        # noinspection PyUnresolvedReferences
        self.add_button.clicked.connect(self.push_add_button)

        # noinspection PyUnresolvedReferences
        self.save_button.clicked.connect(self.push_save_button)

    def prepare(self, parameters):

        self.log("Preparing...")
        self.prepare_buttons()
        self.prepare_table()
        self.log("Preparation done!")

    def prepare_buttons(self):

        self.cancel_button.setText("Cancel")
        self.add_button.setText("Add device")
        self.save_button.setText("Save")

    def push_cancel_button(self):
        pass 

    def push_add_button(self):
        pass

    def push_save_button(self):
        pass

    def prepare_table(self):
        
        data = self.controller.get_parameters("map_android_id_server_id")
        
        labels = "Device name", "Server id"
        
        # set height and width
        self.table.setColumnCount(len(labels))
        self.table.setRowCount(len(data))

        # fit the widget
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # set names
        for i in range(len(labels)):
            self.table.setVerticalHeaderItem(i, QTableWidgetItem(labels[i]))

        self.fill_table(data)

    def fill_table(self, rows):

        for x, (name, server_id) in enumerate(rows.items()):
            self.table.setItem(x, 0, QTableWidgetItem(str(name)))
            self.table.setItem(x, 1, QTableWidgetItem(str(server_id)))
