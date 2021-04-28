from PyQt5.QtWidgets import QLabel, QPushButton, QGridLayout, QGroupBox, QLineEdit, QMessageBox, QProgressBar, \
    QCheckBox, QFileDialog
from PyQt5.QtCore import pyqtSignal

from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from silx.gui.plot.tools import PositionInfo
from silx.gui.qt import QToolBar, Qt
from silx.io.nxdata import save_NXdata
from h5py import File

from utils.imageProcessing import gen_flatfield
from utils.nexusNavigation import get_current_directory, get_dataset
from constants import get_dialog_options, DataPath

import numpy
import os


class FlatfieldGroup(QGroupBox):
    computedFlat = pyqtSignal(numpy.ndarray)

    def __init__(self, parent, application):
        super(QGroupBox, self).__init__()
        self._parent = parent
        self.application = application
        self.grid_layout = QGridLayout(self)

        self.colormap = Colormap("viridis", normalization='log')

        self.flat_saved = False

        self.load_flatfield_button = QPushButton("Load already existing flatfield")

        self.flat_scan_label1 = QLabel("Initial flat scan : ")
        self.flat_scan_input1 = QLineEdit()

        self.flat_scan_button1 = QPushButton("Browse file for first scan")

        self.flat_scan_label2 = QLabel("Final flat scan number :")
        self.flat_scan_input2 = QLineEdit()

        self.flat_scan_run = QPushButton("Run the flatfield computing")

        self.flat_scan_progress = QProgressBar(self)

        self.flatfield_label = QLabel("Flatfield name : ")
        self.flatfield_output = QLineEdit()

        self.flat_save_button = QPushButton("Save flatfield")

        self.flat_scan_viewer = Plot2D(self)

        self.init_UI()

    def init_UI(self):

        self.load_flatfield_button.clicked.connect(self.load_flatfield)

        self.flat_scan_input1.setReadOnly(True)

        self.flat_scan_button1.clicked.connect(self._parent.browse_file)

        self.flat_scan_run.clicked.connect(self.generate_flatfield)

        self.flat_scan_progress.setVisible(False)

        self.flat_scan_viewer.setYAxisInverted()
        self.flat_scan_viewer.setKeepDataAspectRatio()
        self.flat_scan_viewer.setGraphTitle("Flatfield, the result of the computation of several scan")
        self.flat_scan_viewer.setGraphXLabel("x (pixels)")
        self.flat_scan_viewer.setGraphYLabel("y (pixels)")
        self.flat_scan_viewer.setDefaultColormap(self.colormap)

        self.flatfield_output.setReadOnly(True)
        self.flatfield_output.textChanged.connect(self.reset_saved_flat)

        self.flat_save_button.clicked.connect(self.save_flatfield)

        """
        self.flat_use_box = QCheckBox("Use the flat to process images")
        self.flat_use_box.setChecked(False)
        self.flat_use_box.stateChanged.connect(self.use_flatfield)
        """

        self.grid_layout.addWidget(self.flat_scan_label1, 0, 0)
        self.grid_layout.addWidget(self.flat_scan_input1, 0, 1)
        self.grid_layout.addWidget(self.flat_scan_button1, 0, 2)
        self.grid_layout.addWidget(self.load_flatfield_button, 0, 3)
        self.grid_layout.addWidget(self.flat_scan_label2, 1, 0)
        self.grid_layout.addWidget(self.flat_scan_input2, 1, 1)
        self.grid_layout.addWidget(self.flat_scan_run, 1, 2)
        self.grid_layout.addWidget(self.flat_scan_progress, 1, 3)
        self.grid_layout.addWidget(self.flatfield_label, 2, 0)
        self.grid_layout.addWidget(self.flatfield_output, 2, 1)
        self.grid_layout.addWidget(self.flat_save_button, 2, 2)
        # self.grid_layout.addWidget(self.flat_use_box, 2, 3)
        self.grid_layout.addWidget(self.flat_scan_viewer, 4, 0, -1, -1)

    def generate_flatfield(self) -> None:
        if self.flat_scan_input1.text() == "":
            QMessageBox(QMessageBox.Icon.Critical, "Can't run a flat computation",
                        "You must select at least two scans to perfom a flatfield").exec()
        else:
            first_scan_number = self.get_scan_number(self.flat_scan_input1.text())
            if self.flat_scan_input2.text() != '':
                last_scan_number = self.get_scan_number(self.flat_scan_input2.text())
                if first_scan_number > last_scan_number:
                    first_scan_number, last_scan_number = last_scan_number, first_scan_number
            else:
                last_scan_number = first_scan_number
            # Generate the flatfield file
            try:
                self.result = gen_flatfield(first_scan_number, last_scan_number, self._parent.flat_scan,
                                            self.flat_scan_progress, self.application)
                self.flatfield_output.setText(f"flatfield_{first_scan_number}_{last_scan_number}")
                self.flat_scan_viewer.addImage(self.result)
                # We emit the signal when the flatfield had been computed,
                # preventing the app from crashing if the user already checked the box to use the flatfield.
                self.computedFlat.emit(self.result)
            except TypeError:
                QMessageBox(QMessageBox.Icon.Critical, "Can't run a flat computation",
                            "You must select scans with xpad images.").exec()
                self.flat_scan_input1.setText("")
                self.flat_scan_input2.setText("")

    def reset_saved_flat(self) -> None:
        self.flat_saved = False

    """
    def use_flatfield(self) -> None:
        if self.flat_use_box.isChecked():
            self.usingFlat.emit()
        else:
            self.notUsingFlat.emit()
    """

    def save_flatfield(self) -> None:
        # If there is a flatfield calculated and it has not yet been saved.
        if hasattr(self, 'result') and not self.flat_saved:
            directory = get_current_directory().replace("nexVisu/src/utils", "") + f"/{self.flatfield_output.text()}.nxs"
            path, _ = QFileDialog.getSaveFileName(self, 'Save File', directory, options=get_dialog_options())
            if path != "":
                save_NXdata(filename=os.path.join(path),
                            signal=numpy.asarray(self.result),
                            signal_name="data",
                            interpretation="image",
                            nxentry_name="flatfield_scan",
                            nxdata_name="generated_data"
                            )
                print(f"Saved flatfield into {os.path.join(path)} location.")
                self.flat_saved = True
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Can't save flatfield",
                        "You must select or compute a flatfield scan before saving it. "
                        "Or you might have already saved this flatfield").exec()

    def load_flatfield(self):
        if hasattr(self, 'result'):
            temp = self.result
        directory = get_current_directory().replace("nexVisu/src/utils", "")
        path, _ = QFileDialog.getOpenFileName(self, 'Select the flatfield file you want.',
                                              directory, options=get_dialog_options())
        if path == "":
            self.result = temp
        else:
            data = numpy.zeros((240, 560))
            with File(path, mode='r') as h5file:
                data += get_dataset(h5file, DataPath.SAVED_IMAGE.value)
            self.result = data
            self.flat_scan_viewer.addImage(self.result)
            self.computedFlat.emit(self.result)

    def get_scan_number(self, path):
        if path.isnumeric():
            return int(path)
        path = path.partition('.')[0].partition('0001')[0]
        if path[-1] == '_':
            path = path.rpartition('_')[0]
        return int(path.partition('_')[-1])
