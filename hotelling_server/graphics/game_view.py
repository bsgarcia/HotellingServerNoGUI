from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
import numpy as np

from hotelling_server.graphics.widgets.plot_layouts import DonePlayingLayout, OneLinePlot, PlotLayout, TwoLinesPlot
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

        self.table = {"firm": QTableWidget(),
                      "customer": QTableWidget()}

        self.trial_counter = TrialCounter()

        self.plot_layout = dict()

        self.plot_layout["profits"] = PlotLayout(
                parent=self,
                title="",
                plot_class=TwoLinesPlot
        )

        self.plot_layout["distance"] = PlotLayout(
                parent=self,
                title="",
                plot_class=TwoLinesPlot
        )

        self.plot_layout["mean_extra_view_choices"] = PlotLayout(
                parent=self,
                title="",
                plot_class=OneLinePlot
        )

        self.plot_layout["mean_utility"] = PlotLayout(
                parent=self,
                title="",
                plot_class=OneLinePlot
        )

        self.done_playing_layout = DonePlayingLayout(parent=self)

        self.setup()

    def setup(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter, stretch=0)

        self.switch_button.setText("View figures")
        self.layout.addWidget(self.switch_button, stretch=0)

        for widget in self.plot_layout.values():
            self.layout.addWidget(widget, stretch=1)
            widget.hide()

        for widget in self.table.values():
            self.layout.addWidget(widget)

        # self.layout.addLayout(self.done_playing_layout, stretch=0)
        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)
        self.switch_button.clicked.connect(self.push_switch_button)

    def prepare(self, parameters):

        self.log("Preparing...")
        self.prepare_figures()
        self.prepare_stop_button()
        self.prepare_state_table(parameters)
        self.log("Preparation done!")

    def prepare_figures(self):

        self.initialize_figures()
        # self.update_done_playing_labels(data["done_playing_labels"])

    def prepare_stop_button(self):

        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)

    def push_switch_button(self):

        switch = self.switch_button.text() == "View figures"
        self.switch_button.setText(("View figures", "View tables")[switch])

        if switch:
            self.hide_and_show(tohide=self.table, toshow=self.plot_layout)
        else:
            self.hide_and_show(tohide=self.plot_layout, toshow=self.table)

    def hide_and_show(self, tohide, toshow):

        for widget in tohide.values():
            widget.hide()
        for widget in toshow.values():
            widget.show()

    def push_stop_button(self):

        self.stop_button.setEnabled(False)
        self.parent().stop_game()

    def set_trial_number(self, trial_n):

        self.trial_counter.set_trial_number(trial_n)

    def prepare_state_table(self, parameters):

        game_ids, labels, fancy_labels = self.get_state_table_labels(parameters)

        for role in ["firm", "customer"]:
            rows = game_ids[role]
            columns = labels[role]

            # set height and width
            self.table[role].setColumnCount(len(columns))
            self.table[role].setRowCount(len(rows))

            # set column names (parameters to print)
            for i, param in enumerate(fancy_labels[role]):
                self.table[role].setHorizontalHeaderItem(i, QTableWidgetItem(param))

            # fit the widget
            self.table[role].horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table[role].verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_state_table(self, parameters):

        game_ids, labels, fancy_labels = self.get_state_table_labels(parameters)

        for role in ["firm", "customer"]:

            rows = game_ids[role]
            columns = labels[role]

            self.table[role].setColumnCount(len(columns))
            self.table[role].setRowCount(len(rows))

            # set row names (game ids)
            for i, idx in enumerate(rows):
                self.table[role].setVerticalHeaderItem(i, QTableWidgetItem(str(idx)))

            self.fill_state_table(role, rows, columns, parameters)

    def fill_state_table(self, role, rows, columns, parameters):

        # for each game_id
        for x, game_id in enumerate(rows):
            
            # for each label
            for y, label in enumerate(columns):
                data = parameters["current_state"][label]
                role_id = parameters["{}s_id".format(role)][game_id]

                # if data is available
                if len(data) > int(role_id):
                    string = str(data[role_id])
                    self.table[role].setItem(x, y, QTableWidgetItem(string))

    def get_state_table_labels(self, parameters):

        # get game ids
        game_ids = {"firm": list(parameters["firms_id"].keys()),
                    "customer": list(parameters["customers_id"].keys())}

        # pick wanted labels
        firm_labels = "firm_profits", "firm_prices", "firm_positions", "firm_states", "n_client"
        customer_labels = "customer_firm_choices", "customer_extra_view_choices", "customer_utility"

        labels = {"firm": firm_labels,
                   "customer": customer_labels}

        # transform into nicer labels
        fancy_labels = {"firm": [name.replace("_", " ").capitalize() for name in firm_labels],
                        "customer": [name.replace("_", " ").capitalize() for name in customer_labels]}

        return game_ids, labels, fancy_labels

    def initialize_figures(self):

        for widget in self.plot_layout.values():
            widget.plot.clear()

        self.done_playing_layout.clear()

        self.plot_layout["distance"].initialize_figure(
                initial_data=[np.arange(11), np.arange(11)], labels=["position A", "position B"]
        )

        self.plot_layout["profits"].initialize_figure(
                initial_data=[np.arange(11), np.arange(11)], labels=["profits A", "profits B"]
        )

        self.plot_layout["mean_extra_view_choices"].initialize_figure(
                initial_data=np.arange(11), labels="mean view choices"
        )

        self.plot_layout["mean_utility"].initialize_figure(
                initial_data=np.arange(11), labels="mean customer utility"
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
