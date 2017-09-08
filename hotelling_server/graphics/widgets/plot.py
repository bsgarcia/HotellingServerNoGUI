from PyQt5.QtWidgets import *
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import qt_compat

from utils.utils import Logger

# noinspection SpellCheckingInspection
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE


class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=5, dpi=150):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_alpha(0)

        self.axes = self.fig.add_subplot(111)

        # Uncomment for axes to be cleared every time plot() is called
        # self.axes.hold(False)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def clear(self):

        self.axes.clear()
        self.axes.patch.set_alpha(0)


class OneLinePlot(MplCanvas):

    font_size = 8
    line_width = 2

    def __init__(self, *args, **kwargs):

        MplCanvas.__init__(self, *args, **kwargs)
        self.line = None
        self.labels = None

    def initialize(self, initial_data, labels):

        x_max = len(initial_data)

        self.labels = labels

        self.line, = self.axes.plot(
            np.arange(x_max),
            initial_data,
            linewidth=self.line_width,
            color="blue",
            label=labels
        )

        # Customize axes
        self.axes.legend(framealpha=0, fontsize=self.font_size, loc=4)
        self.axes.set_autoscaley_on(True)

    def update_plot(self, data):

        self.clear()

        self.line, = self.axes.plot(
            np.arange(len(data)),
            data,
            linewidth=self.line_width,
            color="blue",
            label=self.labels
        )

        # Customize axes
        self.axes.legend(framealpha=0, fontsize=self.font_size, loc=4)
        self.axes.set_autoscaley_on(True)

        # We need to draw *and* flush
        self.draw()
        self.flush_events()


class TwoLinesPlot(MplCanvas, Logger):

    font_size = 8
    line_width = 2
    colors = ["blue", "green"]

    def __init__(self, *args, **kwargs):

        MplCanvas.__init__(self, *args, **kwargs)
        self.lines = None
        self.labels = None

    def initialize(self, initial_data, labels):

        x = np.arange(len(initial_data[0])) if len(initial_data) else []

        self.labels = labels

        self.lines = []
        for i in range(2):
            line, = \
                self.axes.plot(
                    x,
                    initial_data[i],
                    linewidth=self.line_width,
                    color=self.colors[i],
                    label=labels[i]
                )
            self.lines.append(line)

        # Custom axes
        self.axes.legend(framealpha=0, fontsize=self.font_size, loc=4)
        self.axes.set_autoscaley_on(True)

    def update_plot(self, data):

        self.clear()

        self.lines = []
        for i in range(2):
            line, = \
                self.axes.plot(
                    range(len(data[i])),
                    data[i],
                    linewidth=self.line_width,
                    color=self.colors[i],
                    label=self.labels[i]
                )
            self.lines.append(line)

        # Custom axes
        self.axes.legend(framealpha=0, fontsize=self.font_size, loc=4)
        self.axes.set_autoscaley_on(True)

        # We need to draw *and* flush
        self.draw()
        self.flush_events()
