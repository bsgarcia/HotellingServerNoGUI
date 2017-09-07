from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QLabel,
QMessageBox, QAbstractItemView, QGridLayout, QButtonGroup, QHBoxLayout, QProgressDialog)
from multiprocessing import Event

from utils.utils import Logger
import operator


class DevicesFrame(QWidget, Logger):

    name = "DevicesFrame"

    def __init__(self, parent):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()

        self.controller = parent.mod.controller

        self.cancel_button = QPushButton()
        self.save_button = QPushButton()
        self.add_button = QPushButton()
        self.remove_button = QPushButton()
        self.scan_button = QPushButton()

        self.table = QTableWidget()

        self.setup()

    def setup(self):

        self.setLayout(self.layout)

        # add tables
        self.layout.addWidget(self.table)

        # button layout :
        # | scan network  |
        # | remove | add  |
        # | cancel | save |

        self.layout.addWidget(self.scan_button, stretch=0, alignment=Qt.AlignCenter)

        grid_layout = QGridLayout()

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addStretch(48)
        horizontal_layout.addLayout(grid_layout)
        horizontal_layout.addStretch(48)

        grid_layout.addWidget(self.remove_button, 0, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.cancel_button, 1, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.add_button, 0, 1, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.save_button, 1, 1, alignment=Qt.AlignCenter)

        self.layout.addLayout(horizontal_layout)

        # noinspection PyUnresolvedReferences
        self.cancel_button.clicked.connect(self.push_cancel_button)

        # noinspection PyUnresolvedReferences
        self.add_button.clicked.connect(self.push_add_button)

        # noinspection PyUnresolvedReferences
        self.save_button.clicked.connect(self.push_save_button)

        # noinspection PyUnresolvedReferences
        self.remove_button.clicked.connect(self.push_remove_button)

        # noinspection PyUnresolvedReferences
        self.scan_button.clicked.connect(self.push_scan_button)

    def prepare(self):

        self.log("Preparing...")
        self.prepare_buttons()
        self.prepare_table()
        self.log("Preparation done!")

    def prepare_buttons(self):

        self.cancel_button.setText("Cancel")
        self.add_button.setText("Add device")
        self.save_button.setText("Save")
        self.remove_button.setText("Remove device")
        self.scan_button.setText("Scan network for new devices...")

    def push_cancel_button(self):
        self.log("Push 'cancel' button")
        self.parent().show_frame_load_game_new_game()

    def push_add_button(self):
        self.log("Push 'add device' button")
        self.table.insertRow(self.table.rowCount())
        self.table.scrollToBottom()

    def push_remove_button(self):
        self.log("Push 'remove device' button")
        self.table.removeRow(self.table.currentRow())

    def push_scan_button(self):
        self.log("Push 'scan device' button")
        
        # get current json file mapping 
        old_data = len(self.controller.get_parameters("map_android_id_server_id"))
        
        self.controller.queue.put(("scan_network_for_new_devices", ))
        
        self.show_loading(msg="Scanning...")
        
        # load new json file mapping 
        self.controller.data.setup()
        
        # get the new config
        new_data = len(self.controller.get_parameters("map_android_id_server_id"))
        
        if old_data == new_data:
            self.show_warning(msg="No device found.")
        else:
            self.show_info(msg="Android device added.")

        self.prepare_table()

    def push_save_button(self):
        self.log("Push 'save' button")

        new_mapping, mapping_to_check = self.get_new_mapping()

        warning = self.check_mapping_validity(mapping_to_check)

        if warning:
            self.show_warning(msg=warning)

        else:
            self.write_map_android_id_server_id(new_mapping)
            self.show_info(msg="Mapping successfully saved in 'map_android_id_server_id.json'.")

        # update data
        self.controller.data.setup()

    def prepare_table(self):

        data = self.controller.get_parameters("map_android_id_server_id")

        sorted_data = sorted(data.items(), key=operator.itemgetter(1))

        labels = "Device name", "Server id"

        # set height and width
        self.table.setColumnCount(len(labels))
        self.table.setRowCount(len(sorted_data))

        # fit the widget
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # select whole rows when clicking
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # set names
        for i in range(len(labels)):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(labels[i]))

        self.fill_table(sorted_data)

    def fill_table(self, rows):

        for x, (name, server_id) in enumerate(rows):
            self.table.setItem(x, 0, QTableWidgetItem(str(name)))
            self.table.setItem(x, 1, QTableWidgetItem(str(server_id)))

    def get_new_mapping(self):

        n_rows = self.table.rowCount()

        item = self.table.item

        keys = [item(i, 0).text() if item(i, 0) else None for i in range(n_rows)]
        values = [item(i, 1).text() if item(i, 1) else None for i in range(n_rows)]

        mapping_to_check = list(enumerate(zip(keys, values)))
        new_mapping = {k: int(v) if str(v).isdigit() else v for k, v in zip(keys, values)}

        return new_mapping, mapping_to_check

    def write_map_android_id_server_id(self, new_mapping):

        self.controller.backup.save_param("map_android_id_server_id", new_mapping)

    @staticmethod
    def check_mapping_validity(mapping_to_check):

        for i, (k, v) in mapping_to_check:

            if not str(v).isdigit():
                return "Wrong input for server id '{}' with key '{}' at row '{}'.".format(v, k, i + 1)

            for j, (other_k, other_v) in mapping_to_check:

                cond0 = k == other_k
                cond1 = v == other_v
                cond2 = i != j

                if cond0 and cond2 or cond1 and cond2:
                    return "Identical input at row '{}' and '{}'.".format(i + 1, j + 1)

    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "warning", instructions["msg"],
            QMessageBox.Ok
        )

    def show_info(self, **instructions):

        QMessageBox().information(
            self, "info", instructions["msg"],
            QMessageBox.Ok
        )

    def show_loading(self, **instructions):

        self.progress_dialog = QProgressDialog(parent=self)
        self.progress_dialog.setWindowTitle("Hold on")
        self.progress_dialog.setModal(True)
        self.progress_dialog.setLabelText("Scanning...")
        self.progress_dialog.setMinimum(0)
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.exec_()

    def close_loading(self):

        self.progress_dialog.close()
        

