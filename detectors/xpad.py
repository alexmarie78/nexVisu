from PyQt5.QtWidgets import QPushButton, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, QLabel, QComboBox, QCheckBox, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QFont

from detectors.xpadProcess import XpadVisualisation

from constants import scan_types

from utils import flatfield

import os
import pyqtgraph
import sys

class XpadContext(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()
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
        self.form = DataContext()
        self.tab1.layout.addWidget(self.form)

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

    def __init__(self):
        super(QWidget, self).__init__()
        self.layout = QGridLayout(self)

        self.upperLeftCorner = self.generateContextualDataGroup()
        self.layout.addWidget(self.upperLeftCorner, 0, 0)

        self.upperRightCorner = self.generateFlatfieldGroup()
        self.layout.addWidget(self.upperRightCorner, 0, 1, 2, 1)

        self.lowerLeftCorner = QGroupBox("Calibration with powder")
        self.layout.addWidget(self.lowerLeftCorner, 1, 0)


    def generateContextualDataGroup(self):
        upperLeftCorner = QGroupBox("Experimental data")

        upperLeftCornerLayout = QGridLayout(upperLeftCorner)

        font = QFont()
        font.setPointSize(14)
        font.setUnderline(True)

        scan_type_label = QLabel("Scan type : ")
        scan_type_label.setFont(font)
        scan_type_input = QComboBox()
        for scan in scan_types:
            scan_type_input.addItem(scan.value)


        direct_beam_label = QLabel("Direct Beam :")
        direct_beam_label.setFont(font)
        # direct_beam_label.setAlignment(Qt.AlignCenter)

        x_label = QLabel("x in pixels : ")
        x_input = QLineEdit()
        y_label = QLabel("y in pixels : ")
        y_input = QLineEdit()
        y_input.setMaxLength(50)
        gamma_label1 = QLabel("gamma in degree : ")
        gamma_input1 = QLineEdit()
        gamma_label2 = QLabel("gamma in degree : ")
        gamma_input2 = QLineEdit()
        distance_label = QLabel("distance in pixel/degree : ")
        distance_output = QLineEdit()
        distance_output.setReadOnly(True)

        scan_title = QLabel("Scan n° : ")
        scan_title.setFont(font)
        scan_label = QLabel("Click on the button to search for the scan you want")
        scan_button = QPushButton("Search scan")

        scan_button.clicked.connect(self.browseFile)

        upperLeftCornerLayout.addWidget(scan_type_label, 0, 0, 1, 2)
        upperLeftCornerLayout.addWidget(scan_type_input, 1, 0, 1, 2)
        upperLeftCornerLayout.addWidget(direct_beam_label, 2, 0, 1, 2)
        upperLeftCornerLayout.addWidget(x_label, 3, 0)
        upperLeftCornerLayout.addWidget(x_input, 3, 1)
        upperLeftCornerLayout.addWidget(y_label, 3, 2)
        upperLeftCornerLayout.addWidget(y_input, 3, 3)
        upperLeftCornerLayout.addWidget(gamma_label1, 4, 0)
        upperLeftCornerLayout.addWidget(gamma_input1, 4, 1)
        upperLeftCornerLayout.addWidget(gamma_label2, 4, 2)
        upperLeftCornerLayout.addWidget(gamma_input2, 4, 3)
        upperLeftCornerLayout.addWidget(distance_label, 5, 0)
        upperLeftCornerLayout.addWidget(distance_output, 5, 1)
        upperLeftCornerLayout.addWidget(scan_title, 6, 0, 1, 2)
        upperLeftCornerLayout.addWidget(scan_label, 7, 0, 1, 2)
        upperLeftCornerLayout.addWidget(scan_button, 7, 2, 1, 2)

        return upperLeftCorner

    def generateFlatfieldGroup(self):
        upperRightCorner = QGroupBox("Flatfield")

        upperRightCornerLayout = QGridLayout(upperRightCorner)

        font = QFont()
        font.setPointSize(14)
        font.setUnderline(True)

        flat_scan_label1 = QLabel("Initial flat scan : ")
        flat_scan_input1 = QLineEdit()

        flat_scan_label2 = QLabel("Final flat scan :")
        flat_scan_input2 = QLineEdit()

        flat_scan_run = QPushButton("Run the flatfield computing")
        flat_scan_run.clicked.connect(self.generateFlatfield)

        graphWidget = pyqtgraph.PlotWidget()
        graphWidget.setBackground('w')
        graphWidget.setTitle("Flatfield")
        #graphWidget.plot([0,0], [0,2])

        flatfield_label = QLabel("Flatfield name : ")
        flatfield_output = QLabel()

        save_box = QCheckBox("Save flatfield")
        save_box.setChecked(True)

        upperRightCornerLayout.addWidget(flat_scan_label1, 0, 0)
        upperRightCornerLayout.addWidget(flat_scan_input1, 0, 1)
        upperRightCornerLayout.addWidget(flat_scan_label2, 1, 0)
        upperRightCornerLayout.addWidget(flat_scan_input2, 1, 1)
        upperRightCornerLayout.addWidget(flat_scan_run, 1, 3)
        upperRightCornerLayout.addWidget(graphWidget, 2, 0, 1, 4)
        upperRightCornerLayout.addWidget(flatfield_label, 3, 0)
        upperRightCornerLayout.addWidget(flatfield_output, 3, 1)
        upperRightCornerLayout.addWidget(save_box, 4, 0)

        return upperRightCorner

    def browseFile(self) -> None:
        directory = self.getCurrentDirectory()
        self.scan, _ = QFileDialog.getOpenFileName(self, 'Choose the scan file you want to \
visualize.', directory, '*.nxs')
        self.upperLeftCorner.layout().itemAt(12).widget().setText(self.scan.split('/')[-1])

    def getCurrentDirectory(self) -> str:
        """return the path of the current directory,
        aka where the script is running."""
        return os.path.dirname(os.path.realpath(__file__))

    def generateFlatfield(self) -> None:
        if self.upperRightCorner.layout().itemAt(1).widget().text() == "" or self.upperRightCorner.layout().itemAt(3).widget().text() == "":
            QMessageBox(QMessageBox.Icon.Critical,"Can't run a flat computation", "You must select at least two scans to perfom a flatfield").exec()
        else:
            path = self.getCurrentDirectory().split('/')[:-1]
            path = '/'.join(path)
            print(path)
            first_scan = int(self.upperRightCorner.layout().itemAt(1).widget().text())
            last_scan = int(self.upperRightCorner.layout().itemAt(3).widget().text())
            print(flatfield.genFlatfield(first_scan, last_scan, path))
