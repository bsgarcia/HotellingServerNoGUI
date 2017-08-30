from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QLabel, QAbstractItemView
import numpy as np

from hotelling_server.graphics.widgets.plot_layouts import OneLinePlot, PlotLayout, TwoLinesPlot
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

        self.ip_address = QLabel()

        self.plot_layout = dict()

        self.plot_layout["firm_profits"] = PlotLayout(
                parent=self,
                title="",
                plot_class=TwoLinesPlot
        )

        self.plot_layout["firm_distance"] = PlotLayout(
                parent=self,
                title="",
                plot_class=TwoLinesPlot
        )

        self.plot_layout["customer_mean_extra_view_choices"] = PlotLayout(
                parent=self,
                title="",
                plot_class=OneLinePlot
        )

        self.plot_layout["customer_mean_utility"] = PlotLayout(
                parent=self,
                title="",
                plot_class=OneLinePlot
        )

        # self.done_playing_layout = DonePlayingLayout(parent=self)

        self.setup()

    def setup(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter, stretch=0)

        self.layout.addWidget(self.switch_button, stretch=0)

        # add plots and then hide it
        for key, widget in sorted(self.plot_layout.items()):
            self.layout.addWidget(widget, stretch=1)
            widget.hide()

        # add tables
        for widget in self.table.values():
            self.layout.addWidget(widget)

        # self.layout.addLayout(self.done_playing_layout, stretch=0)
        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # add to layout
        self.layout.addWidget(self.ip_address, alignment=Qt.AlignCenter)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)
        self.switch_button.clicked.connect(self.push_switch_button)

    def prepare(self, parameters):

        self.log("Preparing...")
        self.prepare_figures()
        self.prepare_buttons()
        self.prepare_state_table(parameters)
        self.prepare_ip_label()
        self.log("Preparation done!")

    def prepare_ip_label(self):
        # set ip address
        text = self.parent().mod.controller.server.tcp_server.ip
        font = QFont()
        font.setPointSize(20)
        self.ip_address.setFont(font)
        self.ip_address.setText("IP: {}".format(text))

    def prepare_figures(self):

        self.initialize_figures()
        # self.update_done_playing_labels(data["done_playing_labels"])

    def prepare_buttons(self):

        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)
        self.switch_button.setText("View figures")

    def push_switch_button(self):

        switch = self.switch_button.text() == "View figures"
        self.switch_button.setText(("View figures", "View tables")[switch])

        tohide = (self.plot_layout, self.table)[switch]
        toshow = (self.table, self.plot_layout)[switch]

        self.hide_and_show(tohide=tohide, toshow=toshow)

    def hide_and_show(self, tohide, toshow):

        for widget in tohide.values():
            widget.hide()
        for widget in toshow.values():
            widget.show()

    def push_stop_button(self):

        if self.stop_button.text() == "Stop task":
            self.stop_button.setText("Go to home menu")
            self.parent().stop_game()

        elif self.stop_button.text() == "Go to home menu":
            self.parent().look_for_alive_players()

    def set_trial_number(self, trial_n):

        self.trial_counter.set_trial_number(trial_n)

    def prepare_state_table(self, parameters):

        ids, labels, fancy_labels = self.get_state_table_data(parameters)
        ids = self.parent().mod.controller.data.assignement

        for role in ["firm", "customer"]:

            rows = [server_id for server_id, j, k in ids if j == role]
            columns = fancy_labels[role]

            # empty tables
            self.table[role].clear()

            # set non editable
            self.table[role].setEditTriggers(QAbstractItemView.NoEditTriggers)

            # set height and width
            self.table[role].setColumnCount(len(columns))
            self.table[role].setRowCount(len(rows))

            # fit the widget
            self.table[role].horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table[role].verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

            # set column names (parameters to print)
            for i, param in enumerate(columns):
                self.table[role].setHorizontalHeaderItem(i, QTableWidgetItem(param))

            for i, idx in enumerate(rows):
                self.table[role].setVerticalHeaderItem(
                    i, QTableWidgetItem("Server id: {}".format(idx)
                    )
                )

    def update_state_table(self, parameters):

        ids, labels, fancy_labels = self.get_state_table_data(parameters)

        for role in ["firm", "customer"]:

            rows = ids[role]
            columns = labels[role]

            # set row names (server ids, game ids)
            for i, idx in enumerate(rows):
                    self.table[role].setVerticalHeaderItem(
                            i, QTableWidgetItem("Server id: {} | Game id: {}".format(*idx)
                                    )
                            )

            self.fill_state_table(role, rows, columns, parameters)

    def fill_state_table(self, role, rows, columns, parameters):

        # for each game_id
        for x, (server_id, game_id) in enumerate(rows):
            # for each label
            for y, label in enumerate(columns):
                data = parameters["current_state"][label]
                cond = game_id in parameters["{}s_id".format(role)].keys()
                if cond:
                    role_id = parameters["{}s_id".format(role)][game_id]
                    # if data is available
                    if len(data) > int(role_id):
                        string = str(data[role_id])
                        self.table[role].setItem(x, y, QTableWidgetItem(string))

    def get_state_table_data(self, parameters):

        ids = self.get_ids(parameters)
        labels, fancy_labels = self.get_labels()

        return ids, labels, fancy_labels

    @staticmethod
    def get_ids(parameters):

        server_id = list(parameters["map_server_id_game_id"].items())
        bot_firm_id = list(parameters["bot_firms_id"].items())
        bot_customer_id = list(parameters["bot_customers_id"].items())

        add = bot_firm_id + bot_customer_id

        bot_game_id = [("Bot", game_id) for game_id, i in add]

        server_id_game_id = server_id + bot_game_id

        ids = {"firm": [],
               "customer": []}

        # sort server ids and game ids by role (firm vs customer)
        for role in ["firm", "customer"]:
            ids[role] = [(server_id, game_id) for server_id, game_id in server_id_game_id
                    if parameters["roles"][game_id] == role]
        return ids

    @staticmethod
    def get_labels():

        # pick desired labels
        firm_labels = ("firm_profits",
                       "firm_prices",
                       "firm_positions",
                       "firm_status",
                       "n_client",
                       "firm_cumulative_profits",
                       "firm_states",
                       "time_since_last_request_firms",)

        customer_labels = ("customer_firm_choices",
                           "customer_extra_view_choices",
                           "customer_utility",
                           "customer_states",
                           "time_since_last_request_customers")

        labels = {"firm": firm_labels,
                   "customer": customer_labels}

        # transform into nicer labels
        fancy_labels = {"firm": [name.replace("_", " ").capitalize()
                                for name in firm_labels],
                        "customer": [name.replace("_", " ").capitalize()
                                    for name in customer_labels]}

        return labels, fancy_labels

    def initialize_figures(self):

        for widget in self.plot_layout.values():
            widget.plot.clear()

        # self.done_playing_layout.clear()

        self.plot_layout["firm_distance"].initialize_figure(
                initial_data=[np.arange(11), np.arange(11)], labels=["position A", "position B"]
        )

        self.plot_layout["firm_profits"].initialize_figure(
                initial_data=[np.arange(11), np.arange(11)], labels=["profits A", "profits B"]
        )

        self.plot_layout["customer_mean_extra_view_choices"].initialize_figure(
                initial_data=np.arange(11), labels="mean view choices"
        )

        self.plot_layout["customer_mean_utility"].initialize_figure(
                initial_data=np.arange(11), labels="mean customer utility"
        )

        self.log("Figure initialized.")

    def update_statistics(self, data):

        for key, value in self.plot_layout.items():
            value.update_figure(data[key])

    def update_done_playing(self, done_playing):

        self.done_playing_layout.update_figure(done_playing)

    def update_done_playing_labels(self, done_playing_labels):

        self.done_playing_layout.update_labels(done_playing_labels)

