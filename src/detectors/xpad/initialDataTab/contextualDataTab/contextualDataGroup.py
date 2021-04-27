from PyQt5.QtWidgets import QLabel, QPushButton, QGridLayout, QGroupBox, QLineEdit, QComboBox, QMessageBox, QWidget, \
    QVBoxLayout, QHBoxLayout, QCheckBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal

from constants import ScanTypes
from utils.labelledInputWidget import LabelledInputWidget

import json
import statistics

from src.detectors.xpad.initialDataTab.contextualDataTab.directBeamWidget import DirectBeamWidget


class ContextualDataGroup(QGroupBox):
    scanLabelChanged = pyqtSignal(str)
    contextualDataEntered = pyqtSignal(dict)

    def __init__(self, parent):
        super(QGroupBox, self).__init__()
        self._parent = parent
        self.grid_layout = QGridLayout(self)
        self.contextual_data = {}
        self.file_loaded = False
        self.init_ui()

    def init_ui(self):

        font = QFont()
        font.setPointSize(14)
        font.setUnderline(True)

        self.scan_type_label = QLabel("Scan type : ")
        self.scan_type_label.setFont(font)
        self.scan_type_input = QComboBox()
        for scan in ScanTypes:
            self.scan_type_input.addItem(scan.value)

        self.direct_beam_widget = DirectBeamWidget(self)

        self.median_filter_check = QCheckBox("Tick this box if you want to use median filter to process data")
        self.median_filter_check.stateChanged.connect(self.set_contextual_data)

        self.save_unfoldded_data_check = QCheckBox("Tick this box if you want to save unfolded data")
        self.save_unfoldded_data_check.setChecked(True)
        self.save_unfoldded_data_check.stateChanged.connect(self.set_contextual_data)

        self.scan_title = QLabel("Scan n° : ")
        self.scan_title.setFont(font)
        self.scan_label = QLabel("Click on the button to search for the scan you want")
        self.scan_button = QPushButton("Search scan")

        self.scan_button.clicked.connect(self._parent.browse_file)

        self.grid_layout.addWidget(self.scan_type_label, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_type_input, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.direct_beam_widget, 2, 0, 5, 2)

        self.grid_layout.addWidget(self.median_filter_check, 7, 0, 1, 1)
        self.grid_layout.addWidget(self.save_unfoldded_data_check, 7, 1, 1, 1)
        self.grid_layout.addWidget(self.scan_title, 8, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_label, 9, 0, 2, 1)
        self.grid_layout.addWidget(self.scan_button, 9, 1, 2, 1)

        self.read_calibration()

    def distance_computation(self) -> None:
        inputs = self.x_tab_input if self.x_tab_input.input_number() >= self.y_tab_input.input_number() else self.y_tab_input
        try:
            differences = []
            for index in range(1, inputs.input_number()):
                if inputs.get_label_at(index) != '':
                    differences.append(float(inputs.get_label_at(index))
                                       - float(inputs.get_label_at(index - 1)))
            self.distance_output.setText(str(statistics.mean(differences)))
            self.set_contextual_data()
        except statistics.StatisticsError:
            self.distance_output.setText("95.6677")
            self.set_contextual_data()
            self.test_send_data()

    def set_contextual_data(self):
        try:
            self.contextual_data["x"] = float(self.x_tab_input.inner_widget.layout().itemAt(0).widget().text())
            self.contextual_data["y"] = float(self.y_tab_input.inner_widget.layout().itemAt(0).widget().text())
            self.contextual_data["delta_position"] = float(self.delta_tab_input.inner_widget.layout().itemAt(0).widget().text())
            self.contextual_data["gamma_position"] = float(self.gamma_tab_input.inner_widget.layout().itemAt(0).widget().text())
            self.contextual_data["distance"] = float(self.distance_output.text())
            self.contextual_data["median_filter"] = self.median_filter_check.isChecked()
            self.contextual_data["save_unfolded_data"] = self.save_unfoldded_data_check.isChecked()
            self.test_send_data()
        except ValueError:
            pass

    def test_send_data(self):
        if not hasattr(self, "send_data_button"):
            self.send_data_button = QPushButton("Send contextual data")
            self.grid_layout.addWidget(self.send_data_button, 5, 1)
            self.send_data_button.clicked.connect(self.write_calibration)
            self.send_data_button.clicked.connect(self.send_context_data)

    def write_calibration(self) -> None:
        if not self.file_loaded:
            temp = self.contextual_data
            temp["file"] = self._parent.scan
            with open('../../../../calibration.json', 'w') as outfile:
                json.dump(temp, outfile)
            print("Calibration saved.")
        else:
            self.file_loaded = False

    def read_calibration(self) -> None:
        try:
            with open('../../../../calibration.json', 'r') as infile:
                data = json.load(infile)
            self.x_tab_input.inner_widget.layout().itemAt(0).widget().setText(str(data["x"]))
            self.y_tab_input.inner_widget.layout().itemAt(0).widget().setText(str(data["y"]))
            self.delta_tab_input.inner_widget.layout().itemAt(0).widget().setText(str(data["delta_position"]))
            self.gamma_tab_input.inner_widget.layout().itemAt(0).widget().setText(str(data["gamma_position"]))
            if "distance" in data.keys():
                self.distance_output.setText(str(data["distance"]))
                self.set_contextual_data()
                self.test_send_data()
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

    def get_x_input(self, text):
        self.x_inputs.append(float(text))


