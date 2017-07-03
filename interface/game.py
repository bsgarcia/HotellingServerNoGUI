from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import itertools as it

from graph.graph import OneLinePlot, ThreeLinesPlot, DonePlayingPlot
from utils.utils import log


class TrialCounterLayout(QVBoxLayout):

    font_size = 30

    def __init__(self):

        super().__init__()

        self.trial_label = QLabel("0000")
        self.trial_c_label = QLabel("Trials")

        self.initialize()

    def initialize(self):

        font = QFont()
        font.setPointSize(self.font_size)

        self.trial_label.setFont(font)

        self.addWidget(self.trial_label, alignment=Qt.AlignCenter)
        self.addWidget(self.trial_c_label, alignment=Qt.AlignCenter)
        self.setAlignment(Qt.AlignCenter)

    def set_trial_number(self, n_trial):

        self.trial_label.setText(str(n_trial).zfill(4))


class DonePlayingLayout(QVBoxLayout):

    def __init__(self, parent):

        super().__init__()

        self.done_playing_plot = DonePlayingPlot(
            parent=parent, width=200, height=1, dpi=100)

        self.initialize()

    def initialize(self):

        self.addWidget(self.done_playing_plot, alignment=Qt.AlignCenter)
        self.addWidget(QLabel("Response monitoring"), alignment=Qt.AlignCenter)

    def initialize_figure(self, initial_data):

        self.done_playing_plot.initialize(initial_data=initial_data)

    def update_figure(self, data):

        self.done_playing_plot.update_plot(data)

    def update_labels(self, labels):

        self.done_playing_plot.update_labels(labels)

    def clear(self):

        self.done_playing_plot.clear()


class PlotLayout(QVBoxLayout):

    def __init__(self, parent, title, plot_class=ThreeLinesPlot):

        super().__init__()
        self.plot = plot_class(
            parent=parent, width=200, height=100, dpi=100)

        self.title = title

        self.initialize()

    def initialize(self):

        self.addWidget(self.plot, alignment=Qt.AlignCenter)
        self.addWidget(QLabel(self.title), alignment=Qt.AlignCenter)

    def initialize_figure(self, initial_data, labels):

        self.plot.initialize(initial_data=initial_data, labels=labels)

    def update_figure(self, data):

        self.plot.update_plot(data)

    def clear(self):
        self.plot.clear()


class ExperimentalFrame(QWidget):

    name = "ExperimentalFrame"

    def __init__(self, parent, manager_queue):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.manager_queue = manager_queue

        self.layout = QVBoxLayout()
        self.stop_button = QPushButton()

        self.trial_counter_layout = TrialCounterLayout()

        self.plot_layout = dict()

        self.plot_layout["medium_of_exchange"] = PlotLayout(
            parent=self,
            title="Good 'i' used as a mean of exchange"
        )

        self.plot_layout["exchanges"] = PlotLayout(
            parent=self,
            title="Number of exchanges"
        )

        self.plot_layout["consumption"] = PlotLayout(
            parent=self,
            title="Consumption",
            plot_class=OneLinePlot
        )

        self.done_playing_layout = DonePlayingLayout(parent=self)

        self.initialize()

    def initialize(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter_layout, stretch=0)

        for name, layout in sorted(self.plot_layout.items()):
                self.layout.addLayout(layout, stretch=1)

        self.layout.addLayout(self.done_playing_layout, stretch=0)
        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)

    def prepare(self, data):

        log("Preparing...", self.name)
        self.initialize_figures(data["statistics"], data["done_playing"])
        self.update_statistics(data["statistics"])
        self.update_done_playing(data["done_playing"])
        self.update_done_playing_labels(data["done_playing_labels"])
        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)
        log("Preparation done!", self.name)

    def push_stop_button(self):

        self.stop_button.setEnabled(False)
        self.manager_queue.put(("experimental_frame", "stop"))

    def set_trial_number(self, trial_n):

        self.trial_counter_layout.set_trial_number(trial_n)

    def initialize_figures(self, statistics, done_playing):

        for plot in self.plot_layout.values():
            plot.clear()
        self.done_playing_layout.clear()

        self.plot_layout["medium_of_exchange"].initialize_figure(
            initial_data=statistics["medium_of_exchange"], labels=["Good 0", "Good 1", "Good 2"]
        )
        self.plot_layout["exchanges"].initialize_figure(
            initial_data=statistics["exchanges"], labels=sorted(list(it.combinations(range(3), r=2)))
        )

        self.plot_layout["consumption"].initialize_figure(
            initial_data=statistics["consumption"], labels="Consumption"
        )

        self.done_playing_layout.initialize_figure(
            initial_data=done_playing
        )

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
