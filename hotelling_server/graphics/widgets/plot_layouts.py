from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget

from hotelling_server.graphics.widgets.plot import OneLinePlot, DonePlayingPlot


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


class PlotLayout(QWidget):

    def __init__(self, parent, title, plot_class=OneLinePlot):

        super().__init__()

        self.setParent(parent)

        self.plot = plot_class(width=200, height=100, dpi=100)

        self.layout = QVBoxLayout(self)
        self.title = title

        self.initialize()

    def initialize(self):

        self.layout.addWidget(self.plot, alignment=Qt.AlignCenter)
        self.layout.addWidget(QLabel(self.title), alignment=Qt.AlignCenter)

    def initialize_figure(self, initial_data, labels):

        self.plot.initialize(initial_data=initial_data, labels=labels)

    def update_figure(self, data):

        self.plot.update_plot(data)

    def clear(self):
        self.plot.clear()
