from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

from hotelling_server.graphics.widgets.plot_layouts import DonePlayingLayout
from hotelling_server.graphics.widgets.trial_counter import TrialCounter
from utils.utils import log


class GameFrame(QWidget):

    name = "GameFrame"

    def __init__(self, parent):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.layout = QVBoxLayout()
        self.stop_button = QPushButton()
        self.trial_counter = TrialCounter()

        self.plot_layout = dict()

        # self.plot_layout["medium_of_exchange"] = PlotLayout(
        #     parent=self,
        #     title="Good 'i' used as a mean of exchange"
        # )
        #
        # self.plot_layout["exchanges"] = PlotLayout(
        #     parent=self,
        #     title="Number of exchanges"
        # )
        #
        # self.plot_layout["consumption"] = PlotLayout(
        #     parent=self,
        #     title="Consumption",
        #     plot_class=OneLinePlot
        # )

        self.done_playing_layout = DonePlayingLayout(parent=self)

        self.setup()

    def setup(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter, stretch=0)

        for name, layout in sorted(self.plot_layout.items()):
            self.layout.addLayout(layout, stretch=1)

        # self.layout.addLayout(self.done_playing_layout, stretch=0)
        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)

    def prepare(self):

        log("Preparing...", self.name)
        self.prepare_figures()
        self.prepare_stop_button()
        log("Preparation done!", self.name)
        
    def prepare_figures(self):

        pass
        # self.initialize_figures(data["statistics"], data["done_playing"])
        # self.update_statistics(data["statistics"])
        #
        # self.update_done_playing(data["done_playing"])
        # self.update_done_playing_labels(data["done_playing_labels"])
        
    def prepare_stop_button(self):
        
        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)
    
    def push_stop_button(self):

        self.stop_button.setEnabled(False)
        self.parent().stop_game()

    def set_trial_number(self, trial_n):

        self.trial_counter.set_trial_number(trial_n)

    def initialize_figures(self):

        for plot in self.plot_layout.values():
            plot.clear()
        self.done_playing_layout.clear()

        # self.plot_layout["medium_of_exchange"].initialize_figure(
        #     initial_data=statistics["medium_of_exchange"], labels=["Good 0", "Good 1", "Good 2"]
        # )
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

        log("Figure initialized.", self.name)

    def update_statistics(self, data):

        self.trial_counter_layout.set_trial_number(data["n_trial"])
        for key, value in self.plot_layout.items():
            value.update_figure(data[key])

    def update_done_playing(self, done_playing):

        self.done_playing_layout.update_figure(done_playing)

    def update_done_playing_labels(self, done_playing_labels):

        self.done_playing_layout.update_labels(done_playing_labels)

    def update_stop_button(self):

        self.stop_button.setText("Return to start menu")
        self.stop_button.setEnabled(True)
