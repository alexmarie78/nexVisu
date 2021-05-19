from PyQt5.QtWidgets import QLabel, QPushButton, QGridLayout, QGroupBox, QComboBox, QMessageBox, QCheckBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal

from constants import ScanTypes

from detectors.xpad.initialDataTab.contextualDataTab.directBeamWidget import DirectBeamWidget


class ContextualDataGroup(QGroupBox):
    scanLabelChanged = pyqtSignal(str)
    contextualDataEntered = pyqtSignal(dict)

    def __init__(self, parent):
        super(QGroupBox, self).__init__()
        self._parent = parent
        self.grid_layout = QGridLayout(self)
        self.contextual_data = {}
        self.file_loaded = False

        self.scan_type_label = QLabel("Scan type : ")
        self.scan_type_input = QComboBox()

        self.direct_beam_widget = DirectBeamWidget(self)

        self.median_filter_check = QCheckBox("Tick this box if you want to use median filter to process data")
        self.save_unfoldded_data_check = QCheckBox("Tick this box if you want to save unfolded data")

        self.scan_title = QLabel("Scan n° : ")
        self.scan_label = QLabel("Click on the button to search for the scan you want")
        self.scan_button = QPushButton("Search scan")

        self.init_ui()

    def init_ui(self):

        font = QFont()
        font.setPointSize(14)
        font.setUnderline(True)

        self.scan_type_label.setFont(font)

        for scan in ScanTypes:
            self.scan_type_input.addItem(scan.value)

        self.save_unfoldded_data_check.setChecked(True)

        self.scan_title.setFont(font)

        self.scan_button.clicked.connect(self._parent.browse_file)

        self.grid_layout.addWidget(self.scan_type_label, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_type_input, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.direct_beam_widget, 2, 0, 5, 2)

        self.grid_layout.addWidget(self.median_filter_check, 7, 0, 1, 1)
        self.grid_layout.addWidget(self.save_unfoldded_data_check, 7, 1, 1, 1)
        self.grid_layout.addWidget(self.scan_title, 8, 0, 1, 2)
        self.grid_layout.addWidget(self.scan_label, 9, 0, 2, 1)
        self.grid_layout.addWidget(self.scan_button, 9, 1, 2, 1)

    def send_context_data(self) -> None:
        if hasattr(self._parent, "scan") and self._parent.scan != "":
            self.contextualDataEntered.emit(self.contextual_data)
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Can't send contextual data",
                        "You must chose a scan file before sending the contextual data linked to it.").exec()


