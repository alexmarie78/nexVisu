from PyQt5.QtWidgets import QPushButton, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, QLabel, QComboBox, QCheckBox, QFileDialog, QMessageBox, QDesktopWidget, QApplication, QProgressBar
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QFont, QCursor

from constants import scan_types

from detectors.xpadProcess import XpadVisualisation

from utils import flatfield

from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D

import os
import pyqtgraph
import sys

class XpadContext(QWidget):

    def __init__(self, application: QApplication):
        super(QWidget, self).__init__()
        self.application = application
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(400,300)

        # Add tabs
        self.tabs.addTab(self.tab1,"Initial Data")
        self.tabs.addTab(self.tab2,"Visualisation and processing")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.data_context = DataContext(self.application)
        self.tab1.layout.addWidget(self.data_context)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self.tab2)
        self.widget = XpadVisualisation()
        self.tab2.layout.addWidget(self.widget)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

class DataContext(QWidget):

    def __init__(self, application):
        super(QWidget, self).__init__()
        self.application = application
        self.layout = QGridLayout(self)

        self.colormap = Colormap("viridis", normalization='log')

        self.upperLeftCorner = None
        self.generateContextualDataGroup()
        self.layout.addWidget(self.upperLeftCorner, 0, 0)

        self.upperRightCorner = None
        self.generateFlatfieldGroup()
        self.layout.addWidget(self.upperRightCorner, 0, 1, 2, 1)

        self.lowerLeftCorner = QGroupBox("Calibration with powder")
        self.layout.addWidget(self.lowerLeftCorner, 1, 0)

    def generateContextualDataGroup(self):
        self.upperLeftCorner = QGroupBox("Experimental data")

        self.upperLeftCornerLayout = QGridLayout(self.upperLeftCorner)

        font = QFont()
        font.setPointSize(14)
        font.setUnderline(True)

        self.scan_type_label = QLabel("Scan type : ")
        self.scan_type_label.setFont(font)
        self.scan_type_input = QComboBox()
        for scan in scan_types:
            self.scan_type_input.addItem(scan.value)


        self.direct_beam_label = QLabel("Direct Beam :")
        self.direct_beam_label.setFont(font)
        # direct_beam_label.setAlignment(Qt.AlignCenter)

        self.x_label = QLabel("x in pixels : ")
        self.x_input = QLineEdit()
        self.y_label = QLabel("y in pixels : ")
        self.y_input = QLineEdit()
        self.y_input.setMaxLength(50)
        self.gamma_label1 = QLabel("gamma in degree : ")
        self.gamma_input1 = QLineEdit()
        self.gamma_label2 = QLabel("gamma in degree : ")
        self.gamma_input2 = QLineEdit()
        self.distance_label = QLabel("distance in pixel/degree : ")
        self.distance_output = QLineEdit()
        self.distance_output.setReadOnly(True)

        self.scan_title = QLabel("Scan n° : ")
        self.scan_title.setFont(font)
        self.scan_label = QLabel("Click on the button to search for the scan you want")
        self.scan_button = QPushButton("Search scan")

        self.scan_button.clicked.connect(self.browseFile)

        self.upperLeftCornerLayout.addWidget(self.scan_type_label, 0, 0, 1, 2)
        self.upperLeftCornerLayout.addWidget(self.scan_type_input, 1, 0, 1, 2)
        self.upperLeftCornerLayout.addWidget(self.direct_beam_label, 2, 0, 1, 2)
        self.upperLeftCornerLayout.addWidget(self.x_label, 3, 0)
        self.upperLeftCornerLayout.addWidget(self.x_input, 3, 1)
        self.upperLeftCornerLayout.addWidget(self.y_label, 3, 2)
        self.upperLeftCornerLayout.addWidget(self.y_input, 3, 3)
        self.upperLeftCornerLayout.addWidget(self.gamma_label1, 4, 0)
        self.upperLeftCornerLayout.addWidget(self.gamma_input1, 4, 1)
        self.upperLeftCornerLayout.addWidget(self.gamma_label2, 4, 2)
        self.upperLeftCornerLayout.addWidget(self.gamma_input2, 4, 3)
        self.upperLeftCornerLayout.addWidget(self.distance_label, 5, 0)
        self.upperLeftCornerLayout.addWidget(self.distance_output, 5, 1)
        self.upperLeftCornerLayout.addWidget(self.scan_title, 6, 0, 1, 2)
        self.upperLeftCornerLayout.addWidget(self.scan_label, 7, 0, 1, 2)
        self.upperLeftCornerLayout.addWidget(self.scan_button, 7, 2, 1, 2)

    def generateFlatfieldGroup(self):
        self.upperRightCorner = QGroupBox("Flatfield")

        self.upperRightCornerLayout = QGridLayout(self.upperRightCorner)

        self.flat_scan_label1 = QLabel("Initial flat scan : ")
        self.flat_scan_input1 = QLineEdit()
        self.flat_scan_input1.setReadOnly(True)
        self.flat_scan_button1 = QPushButton("Browse file for first scan")
        self.flat_scan_button1.clicked.connect(self.browseFile)

        self.flat_scan_label2 = QLabel("Final flat scan number :")
        self.flat_scan_input2 = QLineEdit()

        self.flat_scan_run = QPushButton("Run the flatfield computing")
        self.flat_scan_run.clicked.connect(self.generateFlatfield)

        self.flat_scan_progress = QProgressBar(self)

        self.data_viewer = Plot2D(self)

        self.flatfield_label = QLabel("Flatfield name : ")
        self.flatfield_output = QLabel()

        self.flat_save_box = QCheckBox("Save flatfield")
        self.flat_save_box.setChecked(False)
        self.flat_save_box.stateChanged.connect(self.saveFlatfield)

        self.upperRightCornerLayout.addWidget(self.flat_scan_label1, 0, 0)
        self.upperRightCornerLayout.addWidget(self.flat_scan_input1, 0, 1)
        self.upperRightCornerLayout.addWidget(self.flat_scan_button1, 0, 2)
        self.upperRightCornerLayout.addWidget(self.flat_scan_label2, 1, 0)
        self.upperRightCornerLayout.addWidget(self.flat_scan_input2, 1, 1)
        self.upperRightCornerLayout.addWidget(self.flat_save_box, 2, 0)
        self.upperRightCornerLayout.addWidget(self.flat_scan_run, 2, 1)
        self.upperRightCornerLayout.addWidget(self.flat_scan_progress, 2, 2)
        self.upperRightCornerLayout.addWidget(self.flatfield_label, 3, 0)
        self.upperRightCornerLayout.addWidget(self.flatfield_output, 3, 1)
        self.upperRightCornerLayout.addWidget(self.data_viewer, 4, 0, 1, 4)

    def browseFile(self) -> None:
        cursor_position = QCursor.pos()
        directory = self.getCurrentDirectory()
        # Helps multiple uses of this function without rewriting it. If the cursor is in the left half-screen part, user wants to chose an experiment file
        if cursor_position.x() <= self.application.desktop().screenGeometry().width()//2:
            self.scan, _ = QFileDialog.getOpenFileName(self, 'Choose the scan file you want to \
visualize.', directory, '*.nxs')
            self.scan_label.setText(self.scan.split('/')[-1])
        # Else it means user wants to chose a flatscan that will help reduce the noise in the experiment file
        else:
            self.flat_scan, _ = QFileDialog.getOpenFileName(self, 'Choose the flatscan file you want to \
compute.', directory, '*.nxs *.hdf5')
            self.flat_scan_input1.setText(self.flat_scan.split('/')[-1])

    def getCurrentDirectory(self) -> str:
        """return the path of the current directory,
        aka where the script is running."""
        return os.path.dirname(os.path.realpath(__file__))

    def generateFlatfield(self) -> None:
        if self.flat_scan_input1.text() == "" or self.flat_scan_input2.text() == "":
            QMessageBox(QMessageBox.Icon.Critical,"Can't run a flat computation", "You must select at least two scans to perfom a flatfield").exec()
        else:
            if self.flat_scan_input1.text().split('_')[-1].split('.')[-2] == "0001":
                first_scan = int(self.flat_scan_input1.text().split('_')[-2])
            else:
                first_scan = int(self.flat_scan_input1.text().split('_')[-1].split('.')[-2])
            last_scan = int(self.flat_scan_input2.text())
            if first_scan > last_scan:
                first_scan, last_scan = last_scan, first_scan
            self.result = flatfield.genFlatfield(first_scan, last_scan, self.flat_scan, self.flat_scan_progress, self.application)
            self.flatfield_output.setText(f"flatfield_{first_scan}_{last_scan}.nxs")
            self.data_viewer.addImage(self.result, colormap=self.colormap, xlabel='X in pixels', ylabel='Y in pixels')

    def saveFlatfield(self) -> None:
        if hasattr(self, 'result') and self.flat_save_box.isChecked():
            numpy.save(self.getCurrentDirectory(), self.result, False)
