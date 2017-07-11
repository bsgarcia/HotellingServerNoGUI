from PyQt5.QtCore import Qt
import numpy as np
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView

from hotelling_server.graphics.widgets.plot_layouts import DonePlayingLayout, OneLinePlot, PlotLayout
from hotelling_server.graphics.widgets.trial_counter import TrialCounter
from utils.utils import Logger


class GameFrame(QWidget, Logger):

    name = "GameFrame"

    def __init__(self, parent):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.layout = QVBoxLayout()
        self.stop_button = QPushButton()
        self.switch_button = QPushButton()
        self.table = QTableWidget()
        self.trial_counter = TrialCounter()

        self.plot_layout = dict()

        self.plot_layout["distance"] = PlotLayout(
                parent=self,
                title=""
        )
        
        self.done_playing_layout = DonePlayingLayout(parent=self)

        self.setup()

    def setup(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter, stretch=0)

        self.switch_button.setText("View figures")
        self.layout.addWidget(self.switch_button, stretch=0)

        for name, widget in sorted(self.plot_layout.items()):
            self.layout.addWidget(widget, stretch=1)
            widget.hide()

        self.layout.addWidget(self.table)

        # self.layout.addLayout(self.done_playing_layout, stretch=0)
        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)
        self.switch_button.clicked.connect(self.push_switch_button)

    def prepare(self):

        self.log("Preparing...")
        self.prepare_figures()
        self.prepare_stop_button()
        self.log("Preparation done!")

    def prepare_figures(self):

        self.initialize_figures()
        # self.update_done_playing_labels(data["done_playing_labels"])

    def prepare_stop_button(self):

        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)

    def push_switch_button(self):

        switch = self.switch_button.text() == "View figures"
        self.switch_button.setText(("View figures", "View table")[switch])

        if switch:
            self.table.hide()
            for widget in self.plot_layout.values():
                widget.show()

        else:
            self.table.show()
            for widget in self.plot_layout.values():
                widget.hide()

    def push_stop_button(self):

        self.stop_button.setEnabled(False)
        self.parent().stop_game()

    def set_trial_number(self, trial_n):

        self.trial_counter.set_trial_number(trial_n)

    def update_state_table(self, parameters):

        game_ids, labels, fancy_labels = self.prepare_state_table(parameters)

        # get nb of rows and columns
        rows = game_ids
        columns = labels["firm"] + labels["customer"]

        # set height and width
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(rows))

        # set column names
        for i, param in enumerate(fancy_labels):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(param))

        # fit the widget
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.fill_state_table(game_ids, labels, columns, parameters)

    def fill_state_table(self, game_ids, labels, columns, parameters):

        # for each game_id
        for x in game_ids:
            role = parameters["roles"][x]

            # get its role and its labels
            for label in labels[role]:
                    data = parameters["current_state"][label]
                    y = columns.index(label)
                    role_id = parameters["{}s_id".format(role)][x]

                    # if data is available
                    if len(data) > int(role_id):
                        string = str(data[role_id])
                        self.table.setItem(x, y, QTableWidgetItem(string))

    def prepare_state_table(self, parameters):

        # get game ids
        game_ids = \
                sorted(list(parameters["firms_id"].keys()) + list(parameters["customers_id"].keys()))

        # pick wanted labels
        firm_labels = "firm_profits", "firm_prices", "firm_positions", "firm_states", "n_client"
        customer_labels = "customer_firm_choices", "customer_extra_view_choices", "customer_utility"

        labels = {"firm": firm_labels,
                   "customer": customer_labels}

        # transform into nicer labels
        fancy_labels = [name.replace("_", " ").capitalize() for name in firm_labels] \
            + [name.replace("_", " ").capitalize() for name in customer_labels]

        return game_ids, labels, fancy_labels

    def initialize_figures(self):

        for widget in self.plot_layout.values():
            widget.plot.clear()

        self.done_playing_layout.clear()

        self.plot_layout["distance"].initialize_figure(
                initial_data=np.arange(11), labels="distance"
        )

        # self.plot_layout["exchanges"].initialize_figure(
        #     initial_data=statistics["exchanges"], labels=sorted(list(it.combinations(range(3), r=2)))
        # )
        #
        # self.plot_layout["consumption"].initialize_figure(
        #     initial_data=statistics["consumption"], labels="Consumption"
        # )
        #
        # self.done_playing_layout.initialize_figure(
        #     initial_data=done_playing
        # )

        self.log("Figure initialized.")

    def update_statistics(self, data):

        for key, value in self.plot_layout.items():
            value.update_figure(data[key])

    def update_done_playing(self, done_playing):

        self.done_playing_layout.update_figure(done_playing)

    def update_done_playing_labels(self, done_playing_labels):

        self.done_playing_layout.update_labels(done_playing_labels)

    def update_stop_button(self):

        self.stop_button.setText("Return to start menu")
        self.stop_button.setEnabled(True)
