from constants import ScanTypes
from detectors.xpadProcess import XpadVisualisation
from PyQt5.QtWidgets import QPushButton, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, QLabel, \
    QComboBox, QCheckBox, QFileDialog, QMessageBox, QApplication, QProgressBar
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from utils.imageProcessing import gen_flatfield
from utils.nexusNavigation import get_current_directory

import numpy
import os


class XpadContext(QWidget):

    def __init__(self, application: QApplication):
        super(QWidget, self).__init__()
        self.application = application
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.tab1, "Initial Data")
        self.tabs.addTab(self.tab2, "Visualisation and processing")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.data_context = DataContext(self.application)
        self.tab1.layout.addWidget(self.data_context)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self.tab2)
        self.xpad_visualisation = XpadVisualisation()
        self.tab2.layout.addWidget(self.xpad_visualisation)

        self.data_context.scanLabelChanged.connect(self.xpad_visualisation.set_data)
        self.data_context.contextualDataEntered.connect(self.xpad_visualisation.start_unfolding_raw_data)
        self.data_context.usingFlat.connect(self.send_flatfield_image)
        self.data_context.notUsingFlat.connect(self.send_empty_flatfield)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

    def send_flatfield_image(self) -> None:
        self.xpad_visualisation.get_flatfield(self.data_context.send_flatfield())

    def send_empty_flatfield(self) -> None:
        self.xpad_visualisation.get_flatfield(None)


class DataContext(QWidget):
    # Custom signal to transmit data
    scanLabelChanged = pyqtSignal(str)
    contextualDataEntered = pyqtSignal(dict)
    usingFlat = pyqtSignal()
    notUsingFlat = pyqtSignal()

    def __init__(self, application):
        super(QWidget, self).__init__()
        self.application = application
        self.layout = QGridLayout(self)
        self.contextual_data = {}
        self.flat_saved = False

        self.colormap = Colormap("viridis", normalization='log')

        self.upper_left_corner = None
        self.generate_contextual_data_group()
        self.layout.addWidget(self.upper_left_corner, 0, 0)

        self.upper_right_corner = None
        self.generate_flatfield_group()
        self.layout.addWidget(self.upper_right_corner, 0, 1, 2, 1)

        self.lowerLeftCorner = QGroupBox("Calibration with powder")
        self.layout.addWidget(self.lowerLeftCorner, 1, 0)

    def generate_contextual_data_group(self):
        self.upper_left_corner = QGroupBox("Experimental data")

        self.upper_left_corner_layout = QGridLayout(self.upper_left_corner)

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

        self.x_label = QLabel("x in pixels : ")
        self.x_input = QLineEdit()
        self.x_input.textChanged.connect(self.distance_computation)

        self.y_label = QLabel("y in pixels : ")
        self.y_input = QLineEdit()
        self.y_input.textChanged.connect(self.distance_computation)

        self.delta_label = QLabel("delta offset in degree : ")
        self.delta_input = QLineEdit()
        self.delta_input.textChanged.connect(self.distance_computation)

        self.gamma_label = QLabel("gamma offset in degree : ")
        self.gamma_input = QLineEdit()
        self.gamma_input.textChanged.connect(self.distance_computation)

        self.distance_label = QLabel("number of pixel/degree : ")
        self.distance_output = QLineEdit()
        self.distance_output.setReadOnly(True)
        self.distance_output.textChanged.connect(self.distance_computation)

        self.scan_title = QLabel("Scan n° : ")
        self.scan_title.setFont(font)
        self.scan_label = QLabel("Click on the button to search for the scan you want")
        self.scan_button = QPushButton("Search scan")

        self.scan_button.clicked.connect(self.browse_file)

        self.upper_left_corner_layout.addWidget(self.scan_type_label, 0, 0, 1, 2)
        self.upper_left_corner_layout.addWidget(self.scan_type_input, 1, 0, 1, 2)
        self.upper_left_corner_layout.addWidget(self.direct_beam_label, 2, 0, 1, 2)
        self.upper_left_corner_layout.addWidget(self.x_label, 3, 0)
        self.upper_left_corner_layout.addWidget(self.x_input, 3, 1)
        self.upper_left_corner_layout.addWidget(self.y_label, 3, 2)
        self.upper_left_corner_layout.addWidget(self.y_input, 3, 3)
        self.upper_left_corner_layout.addWidget(self.delta_label, 4, 0)
        self.upper_left_corner_layout.addWidget(self.delta_input, 4, 1)
        self.upper_left_corner_layout.addWidget(self.gamma_label, 4, 2)
        self.upper_left_corner_layout.addWidget(self.gamma_input, 4, 3)
        self.upper_left_corner_layout.addWidget(self.distance_label, 5, 0)
        self.upper_left_corner_layout.addWidget(self.distance_output, 5, 1)
        self.upper_left_corner_layout.addWidget(self.scan_title, 6, 0, 1, 2)
        self.upper_left_corner_layout.addWidget(self.scan_label, 7, 0, 1, 2)
        self.upper_left_corner_layout.addWidget(self.scan_button, 7, 2, 1, 2)

    def generate_flatfield_group(self):
        self.upper_right_corner = QGroupBox("Flatfield")

        self.upper_right_corner_layout = QGridLayout(self.upper_right_corner)

        self.flat_scan_label1 = QLabel("Initial flat scan : ")
        self.flat_scan_input1 = QLineEdit()
        self.flat_scan_input1.setReadOnly(True)
        self.flat_scan_button1 = QPushButton("Browse file for first scan")
        self.flat_scan_button1.clicked.connect(self.browse_file)

        self.flat_scan_label2 = QLabel("Final flat scan number :")
        self.flat_scan_input2 = QLineEdit()

        self.flat_scan_run = QPushButton("Run the flatfield computing")
        self.flat_scan_run.clicked.connect(self.generate_flatfield)

        self.flat_scan_progress = QProgressBar(self)
        self.flat_scan_progress.setVisible(False)

        self.flat_scan_viewer = Plot2D(self)
        self.flat_scan_viewer.setYAxisInverted()
        self.flat_scan_viewer.setKeepDataAspectRatio()

        self.flatfield_label = QLabel("Flatfield name : ")
        self.flatfield_output = QLineEdit()
        self.flatfield_output.setReadOnly(True)
        self.flatfield_output.textChanged.connect(self.reset_saved_flat)

        self.flat_save_button = QPushButton("Save flatfield")
        self.flat_save_button.clicked.connect(self.save_flatfield)

        self.flat_use_box = QCheckBox("Use the flat to process images")
        self.flat_use_box.setChecked(False)
        self.flat_use_box.stateChanged.connect(self.use_flatfield)

        self.upper_right_corner_layout.addWidget(self.flat_scan_label1, 0, 0)
        self.upper_right_corner_layout.addWidget(self.flat_scan_input1, 0, 1)
        self.upper_right_corner_layout.addWidget(self.flat_scan_button1, 0, 2)
        self.upper_right_corner_layout.addWidget(self.flat_scan_label2, 1, 0)
        self.upper_right_corner_layout.addWidget(self.flat_scan_input2, 1, 1)
        self.upper_right_corner_layout.addWidget(self.flat_scan_run, 1, 2)
        self.upper_right_corner_layout.addWidget(self.flat_scan_progress, 1, 3)
        self.upper_right_corner_layout.addWidget(self.flatfield_label, 2, 0)
        self.upper_right_corner_layout.addWidget(self.flatfield_output, 2, 1)
        self.upper_right_corner_layout.addWidget(self.flat_save_button, 2, 2)
        self.upper_right_corner_layout.addWidget(self.flat_use_box, 2, 3)
        self.upper_right_corner_layout.addWidget(self.flat_scan_viewer, 4, 0, -1, -1)

    def browse_file(self) -> None:
        if hasattr(self, "scan"):
            temp = self.scan
        else:
            temp = None
        cursor_position = QCursor.pos()
        directory = get_current_directory().replace("/utils", "").replace("/nexVisu", "")
        options = QFileDialog.Options()
        options |= QFileDialog.DontResolveSymlinks
        options |= QFileDialog.DontUseNativeDialog
        # Helps multiple uses of this function without rewriting it. If the cursor is in the left half-screen part,
        # user wants to chose an experiment file
        if cursor_position.x() <= self.application.desktop().screenGeometry().width()//2:
            self.scan, _ = QFileDialog.getOpenFileName(self, 'Choose the scan file you want to \
visualize.', directory, '*.nxs', options=options)
            if self.scan != "":
                self.scan_label.setText(self.scan.split('/')[-1])
                self.scanLabelChanged.emit(self.scan)
            else:
                # If a scan was selected and the user kills the dialog
                if temp is not None:
                    self.scan = temp
                    self.scan_label.setText(self.scan.split('/')[-1])
                else:
                    self.scan_label.setText("Click on the button to search for the scan you want")
        # Else it means user wants to chose a flatscan that will help reduce the noise in the experiment file
        else:
            self.flat_scan, _ = QFileDialog.getOpenFileName(self, "Choose the flatscan file you want to \
            compute.", directory, "*.nxs *.hdf5", options=options)
            if self.flat_scan != "":
                self.flat_scan_viewer.clear()
                self.flat_scan_input1.setText(self.flat_scan.split('/')[-1])

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
                self.result = gen_flatfield(first_scan, last_scan, self.flat_scan,
                                            self.flat_scan_progress, self.application)
                self.flatfield_output.setText(f"flatfield_{first_scan}_{last_scan}")
                self.flat_scan_viewer.addImage(self.result, colormap=self.colormap,
                                               xlabel='X in pixels', ylabel='Y in pixels')
                # We emit the signal when the flatfield had been computed,
                # preventing the app from crashing if the user already checked the box to use the flatfield.
                self.usingFlat.emit()
            except TypeError:
                QMessageBox(QMessageBox.Icon.Critical, "Can't run a flat computation",
                            "You must select scans with xpad images.").exec()
                self.flat_scan_input1.setText("")
                self.flat_scan_input2.setText("")

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

    def distance_computation(self) -> None:
        try:
            self.contextual_data["x"] = float(self.x_input.text())
            self.contextual_data["y"] = float(self.y_input.text())
            self.contextual_data["delta_offset"] = float(self.delta_input.text())
            self.contextual_data["gamma_offset"] = float(self.gamma_input.text())
            self.distance_output.setText("80.33")
            self.contextual_data["distance"] = float(self.distance_output.text())
            if not hasattr(self, "send_data_button"):
                self.send_data_button = QPushButton("Send contextual data")
                self.upper_left_corner_layout.addWidget(self.send_data_button, 5, 3)
                self.send_data_button.clicked.connect(self.send_context_data)
        except ValueError:
            pass

    def send_context_data(self) -> None:
        if hasattr(self, "scan") and self.scan != "":
            self.contextualDataEntered.emit(self.contextual_data)
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Can't send contextual data",
                        "You must chose a scan file before sending the contextual data linked to it.").exec()

    def use_flatfield(self) -> None:
        if self.flat_use_box.isChecked():
            self.usingFlat.emit()
        else:
            self.notUsingFlat.emit()

    def send_flatfield(self) -> numpy.ndarray:
        if self.flat_use_box.isChecked() and hasattr(self, "result"):
            return self.result

    def reset_saved_flat(self) -> None:
        self.flat_saved = False
