from PyQt5.QtWidgets import *
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from matplotlib.backends import qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
from utils.utils import Logger


class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=5, dpi=150):

        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_alpha(0)

        self.axes = fig.add_subplot(111)

        # Uncomment for axes to be cleared every time plot() is called
        # self.axes.hold(False)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def clear(self):

        self.axes.clear()
        self.axes.patch.set_alpha(0)


class DonePlayingPlot(MplCanvas):

    font_size = 6
    marker_size = 5

    def __init__(self, *args, **kwargs):

        MplCanvas.__init__(self, *args, **kwargs)
        self.line = None
        self.txt = None

    def initialize(self, initial_data):

        n = len(initial_data)

        self.line, = self.axes.plot(
            np.arange(n),
            initial_data,
            "o",
            color="green",
            markeredgecolor="green",
            markersize=self.marker_size,
        )
        self.txt = []
        for i in range(n):
            t = self.axes.text(
                i, 0.85, "x",
                verticalalignment='center', horizontalalignment='center',
                fontsize=self.font_size
            )
            self.txt.append(t)

        self.axes.spines['right'].set_visible(False)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['left'].set_visible(False)
        self.axes.spines['bottom'].set_visible(False)

        self.axes.set_xlim(-0.5, n - 0.5)
        self.axes.set_ylim(0.5, 1.5)

        self.axes.set_yticks([])
        self.axes.set_xticks([])

        self.draw()
        self.flush_events()

    def update_plot(self, data):

        self.line.set_ydata(data)

        # We need to draw *and* flush
        self.draw()
        self.flush_events()

    def update_labels(self, labels):

        for i, label in enumerate(labels):
            t = self.axes.text(
                i, 0.85, label,
                verticalalignment='center', horizontalalignment='center',
                fontsize=self.font_size
            )
            self.txt[i].remove()
            self.txt[i] = t

        self.draw()
        self.flush_events()


class OneLinePlot(MplCanvas):

    font_size = 8
    line_width = 2

    def __init__(self, *args, **kwargs):

        MplCanvas.__init__(self, *args, **kwargs)
        self.line = None

    def initialize(self, initial_data, labels):

        x_max = len(initial_data)

        self.line, = self.axes.plot(
            np.arange(x_max),
            initial_data,
            linewidth=self.line_width,
            color="blue",
            label=labels
        )

        # Customize axes
        # self.axes.set_ylim(-0.01, 1.1)
        self.axes.legend(framealpha=0, fontsize=self.font_size)
        self.axes.set_autoscaley_on(True)

    def update_plot(self, data):

        self.line.set_xdata(range(len(data)))
        self.line.set_ydata(data)

        self.axes.relim()
        self.axes.autoscale_view()

        # self.axes.set_ylim(-0.01, 1.1)

        # We need to draw *and* flush
        self.draw()
        self.flush_events()


class ThreeLinesPlot(MplCanvas):

    font_size = 8
    line_width = 2
    colors = ["blue", "red", "green"]

    def __init__(self, *args, **kwargs):

        MplCanvas.__init__(self, *args, **kwargs)
        self.lines = None

    def initialize(self, initial_data, labels):

        x = np.arange(len(initial_data[0])) if len(initial_data) else []

        self.lines = []
        for i in range(3):
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
        self.axes.legend(framealpha=0, fontsize=self.font_size)
        # frame = legend.get_frame()
        # frame.set_alpha(0)

        self.axes.set_autoscaley_on(True)

    def update_plot(self, data):

        for line, d in zip(self.lines, data):
            line.set_xdata(range(len(d)))
            line.set_ydata(d)

        self.axes.relim()
        self.axes.autoscale_view()

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

    def initialize(self, initial_data, labels):

        x = np.arange(len(initial_data[0])) if len(initial_data) else []

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
        self.axes.legend(framealpha=0, fontsize=self.font_size)
        # frame = legend.get_frame()
        # frame.set_alpha(0)

        self.axes.set_autoscaley_on(True)

    def update_plot(self, data):

        for line, d in zip(self.lines, data):
            line.set_xdata(range(len(d)))
            line.set_ydata(d)
        
        self.clear()
        self.axes.relim()
        self.axes.autoscale_view()

        # We need to draw *and* flush
        self.draw()
        self.flush_events()
