from PyQt5.QtWidgets import QLabel, QPushButton, QGridLayout, QGroupBox, QLineEdit, QComboBox, QMessageBox, QProgressBar, QCheckBox
from PyQt5.QtCore import pyqtSignal

from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D

from utils.imageProcessing import gen_flatfield
from utils.nexusNavigation import get_current_directory

import numpy

class FlatfieldGroup(QGroupBox):
    usingFlat = pyqtSignal()
    notUsingFlat = pyqtSignal()

    def __init__(self, parent, application):
        super(QGroupBox, self).__init__()
        self._parent = parent
        self.application = application
        self.grid_layout = QGridLayout(self)

        self.colormap = Colormap("viridis", normalization='log')

        self.flat_saved = False
        self.init_UI()

    def init_UI(self):

        self.flat_scan_label1 = QLabel("Initial flat scan : ")
        self.flat_scan_input1 = QLineEdit()
        self.flat_scan_input1.setReadOnly(True)
        self.flat_scan_button1 = QPushButton("Browse file for first scan")
        self.flat_scan_button1.clicked.connect(self._parent.browse_file)

        self.flat_scan_label2 = QLabel("Final flat scan number :")
        self.flat_scan_input2 = QLineEdit()

        self.flat_scan_run = QPushButton("Run the flatfield computing")
        self.flat_scan_run.clicked.connect(self.generate_flatfield)

        self.flat_scan_progress = QProgressBar(self)
        self.flat_scan_progress.setVisible(False)

        self.flat_scan_viewer = Plot2D(self)
        self.flat_scan_viewer.setYAxisInverted()
        self.flat_scan_viewer.setKeepDataAspectRatio()
        self.flat_scan_viewer.setGraphTitle("Flatfield, the result of the computation of several scan")
        self.flat_scan_viewer.setGraphXLabel("x (pixels)")
        self.flat_scan_viewer.setGraphYLabel("y (pixels)")
        self.flat_scan_viewer.setDefaultColormap(self.colormap)

        self.flatfield_label = QLabel("Flatfield name : ")
        self.flatfield_output = QLineEdit()
        self.flatfield_output.setReadOnly(True)
        self.flatfield_output.textChanged.connect(self.reset_saved_flat)

        self.flat_save_button = QPushButton("Save flatfield")
        self.flat_save_button.clicked.connect(self.save_flatfield)

        self.flat_use_box = QCheckBox("Use the flat to process images")
        self.flat_use_box.setChecked(False)
        self.flat_use_box.stateChanged.connect(self.use_flatfield)

        self.grid_layout.addWidget(self.flat_scan_label1, 0, 0)
        self.grid_layout.addWidget(self.flat_scan_input1, 0, 1)
        self.grid_layout.addWidget(self.flat_scan_button1, 0, 2)
        self.grid_layout.addWidget(self.flat_scan_label2, 1, 0)
        self.grid_layout.addWidget(self.flat_scan_input2, 1, 1)
        self.grid_layout.addWidget(self.flat_scan_run, 1, 2)
        self.grid_layout.addWidget(self.flat_scan_progress, 1, 3)
        self.grid_layout.addWidget(self.flatfield_label, 2, 0)
        self.grid_layout.addWidget(self.flatfield_output, 2, 1)
        self.grid_layout.addWidget(self.flat_save_button, 2, 2)
        self.grid_layout.addWidget(self.flat_use_box, 2, 3)
        self.grid_layout.addWidget(self.flat_scan_viewer, 4, 0, -1, -1)

    def generate_flatfield(self) -> None:
        if self.flat_scan_input1.text() == "" or self.flat_scan_input2.text() == "":
            QMessageBox(QMessageBox.Icon.Critical, "Can't run a flat computation",
                        "You must select at least two scans to perfom a flatfield").exec()
        else:
            if self.flat_scan_input1.text().split('_')[-1].split('.')[-2] == "0001":
                first_scan = int(self.flat_scan_input1.text().split('_')[-2])
            else:
                first_scan = int(self.flat_scan_input1.text().split('_')[-1].split('.')[-2])
            last_scan = int(self.flat_scan_input2.text())
            if first_scan > last_scan:
                first_scan, last_scan = last_scan, first_scan
            # Generate the flatfield file
            try:
                self.result = gen_flatfield(first_scan, last_scan, self._parent.flat_scan,
                                            self.flat_scan_progress, self.application)
                self.flatfield_output.setText(f"flatfield_{first_scan}_{last_scan}")
                self.flat_scan_viewer.addImage(self.result)
                # We emit the signal when the flatfield had been computed,
                # preventing the app from crashing if the user already checked the box to use the flatfield.
                self.usingFlat.emit()
            except TypeError:
                QMessageBox(QMessageBox.Icon.Critical, "Can't run a flat computation",
                            "You must select scans with xpad images.").exec()
                self.flat_scan_input1.setText("")
                self.flat_scan_input2.setText("")

    def reset_saved_flat(self) -> None:
        self.flat_saved = False

    def use_flatfield(self) -> None:
        if self.flat_use_box.isChecked():
            self.usingFlat.emit()
        else:
            self.notUsingFlat.emit()

    def save_flatfield(self) -> None:
        # If there is a flatfield calculated and it has not yet been saved.
        if hasattr(self, 'result') and not self.flat_saved:
            directory = get_current_directory().replace("/utils", "") + f"/{self.flatfield_output.text()}"
            path, _ = QFileDialog.getSaveFileName(self, 'Save File', directory)
            if path != "":
                numpy.save(os.path.join(path), self.result, False)
                self.flat_saved = True
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Can't save flatfield",
                        "You must select or compute a flatfield scan before saving it. "
                        "Or you might have already saved this flatfield").exec()

    def send_flatfield(self) -> numpy.ndarray:
        if self.flat_use_box.isChecked() and hasattr(self, "result"):
            return self.result
