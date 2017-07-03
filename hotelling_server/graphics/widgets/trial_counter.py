from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QLabel


class TrialCounter(QVBoxLayout):

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
