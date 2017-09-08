from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QProgressBar, QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ProgressionBar(QWidget):

    def __init__(self, parent):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.grid = QGridLayout()

        self.label = QLabel("Setting up a few things...")
        self.progression_bar = QProgressBar(parent=parent)

        self.initialize()

    def initialize(self):

        font = QFont()
        font.setPointSize(14)

        self.label.setFont(font)
        self.label.setContentsMargins(30, 30, 30, 0)

        self.setLayout(self.grid)

        spacer_row_span = 10
        self.grid.addItem(QSpacerItem(0, 1), 0, 0, spacer_row_span, 10)

        # noinspection PyArgumentList
        self.grid.addWidget(self.label, spacer_row_span + 1, 5, Qt.AlignCenter)
        self.grid.addItem(QSpacerItem(0, 0), spacer_row_span + 2, 1, 2, 10)

        # noinspection PyArgumentList
        self.grid.addWidget(self.progression_bar, spacer_row_span + 3 + 2, 3, 1, 5)
        self.grid.addItem(QSpacerItem(0, 0), spacer_row_span + 5, 1, spacer_row_span, 10)

    def set_up(self):
        self.progression_bar.reset()
        self.progression_bar.setMaximum(0)
        self.progression_bar.setMinimum(0)
        self.progression_bar.setValue(0)

    def shutdown(self):

        self.progression_bar.setMaximum(100)
        self.progression_bar.setValue(100)
