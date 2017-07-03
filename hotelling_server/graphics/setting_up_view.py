from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from hotelling_server.graphics.widgets import progression_bar


class SettingUpFrame(QWidget):

    def __init__(self, parent):

        # noinspection PyArgumentList
        super().__init__(parent=parent)
        self.layout = QVBoxLayout()
        self.progression_bar = progression_bar.ProgressionBar(parent=self)
        self.initialize()

    def initialize(self):

        self.layout.addWidget(self.progression_bar, alignment=Qt.AlignCenter)
        self.setLayout(self.layout)

    def show(self):

        self.progression_bar.set_up()
        super().show()

    def hide(self):

        self.progression_bar.shutdown()
        super().hide()
