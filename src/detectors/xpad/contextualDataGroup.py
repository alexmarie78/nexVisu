from PyQt5.QtWidgets import QLabel, QPushButton, QGridLayout, QGroupBox, QLineEdit, QComboBox, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal

from src.constants import ScanTypes

import json
import os


class ContextualDataGroup(QGroupBox):
    scanLabelChanged = pyqtSignal(str)
    contextualDataEntered = pyqtSignal(dict)

    def __init__(self, parent):
        super(QGroupBox, self).__init__()
        self._parent = parent
        self.grid_layout = QGridLayout(self)
        self.contextual_data = {}
        self.file_loaded = False
        self.init_UI()

    def init_UI(self):

        font = QFont()
        font.setPointSize(14)
        font.setUnderline(True)

        self.scan_type_label = QLabel("Scan type : ")
        self.scan_type_label.setFont(font)
        self.scan_type_input = QComboBox()
        for scan in ScanTypes:
            self.scan_type_input.addItem(scan.value)

        self.direct_beam_label = QLabel("Direct Beam :")
        self.direct_beam_label.setFont(font)
        # direct_beam_label.setAlignment(Qt.AlignCenter)

        self.x_label = QLabel("x (pixels) : ")
        self.x_input = QLineEdit()
        self.x_input.textChanged.connect(self.distance_computation)

        self.y_label = QLabel("y (pixels) : ")
        self.y_input = QLineEdit()
        self.y_input.textChanged.connect(self.distance_computation)

        self.delta_label = QLabel("delta position (°) : ")
        self.delta_input = QLineEdit()
        self.delta_input.textChanged.connect(self.distance_computation)

        self.gamma_label = QLabel("gamma position (°) : ")
        self.gamma_input = QLineEdit()
        self.gamma_input.textChanged.connect(self.distance_computation)

        self.distance_label = QLabel("number of pixel/° : ")
        self.distance_output = QLineEdit()
        self.distance_output.setReadOnly(True)
        self.distance_output.textChanged.connect(self.distance_computation)

        self.scan_title = QLabel("Scan n° : ")
        self.scan_title.setFont(font)
        self.scan_label = QLabel("Click on the button to search for the scan you want")
        self.scan_button = QPushButton("Search scan")

        self.scan_button.clicked.connect(self._parent.browse_file)

        self.grid_layout.addWidget(self.scan_type_label, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_type_input, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.direct_beam_label, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.x_label, 3, 0)
        self.grid_layout.addWidget(self.x_input, 3, 1)
        self.grid_layout.addWidget(self.y_label, 3, 2)
        self.grid_layout.addWidget(self.y_input, 3, 3)
        self.grid_layout.addWidget(self.delta_label, 4, 0)
        self.grid_layout.addWidget(self.delta_input, 4, 1)
        self.grid_layout.addWidget(self.gamma_label, 4, 2)
        self.grid_layout.addWidget(self.gamma_input, 4, 3)
        self.grid_layout.addWidget(self.distance_label, 5, 0)
        self.grid_layout.addWidget(self.distance_output, 5, 1)
        self.grid_layout.addWidget(self.scan_title, 6, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_label, 7, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_button, 7, 2, 1, 2)

        self.read_calibration()

    def distance_computation(self) -> None:
        try:
            self.contextual_data["x"] = float(self.x_input.text())
            self.contextual_data["y"] = float(self.y_input.text())
            self.contextual_data["delta_position"] = float(self.delta_input.text())
            self.contextual_data["gamma_position"] = float(self.gamma_input.text())
            self.distance_output.setText("95.6677")
            self.contextual_data["distance"] = float(self.distance_output.text())
            if not hasattr(self, "send_data_button"):
                self.send_data_button = QPushButton("Send contextual data")
                self.grid_layout.addWidget(self.send_data_button, 5, 3)
                self.send_data_button.clicked.connect(self.write_calibration)
                self.send_data_button.clicked.connect(self.send_context_data)
        except ValueError:
            pass

    def write_calibration(self) -> None:
        if not self.file_loaded:
            temp = self.contextual_data
            temp["file"] = self._parent.scan
            with open('calibration.json', 'w') as outfile:
                json.dump(temp, outfile)
            print("Calibration saved.")
        else:
            self.file_loaded = False

    def read_calibration(self) -> None:
        try:
            with open('calibration.json', 'r') as infile:
                data = json.load(infile)
            self.x_input.setText(str(data["x"]))
            self.y_input.setText(str(data["y"]))
            self.delta_input.setText(str(data["delta_position"]))
            self.gamma_input.setText(str(data["gamma_position"]))
            self.file_loaded = True
        except IOError:
            print("Calibration not found")
            self.file_loaded = False

    def send_context_data(self) -> None:
        if hasattr(self._parent, "scan") and self._parent.scan != "":
            self.contextualDataEntered.emit(self.contextual_data)
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Can't send contextual data",
                        "You must chose a scan file before sending the contextual data linked to it.").exec()
