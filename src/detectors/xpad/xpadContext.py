from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QFileDialog
from PyQt5.QtGui import QCursor

from utils.nexusNavigation import get_current_directory
from .contextualDataGroup import ContextualDataGroup
from .flatfieldGroup import FlatfieldGroup

import sys
import platform


class DataContext(QWidget):
    def __init__(self, application):
        super(QWidget, self).__init__()
        self.application = application

        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget(self)
        self.experimental_data_tab = ContextualDataGroup(self)
        self.flatfield_tab = FlatfieldGroup(self, application)
        self.calibration_with_powder_tab = QWidget()
        self.tabs.resize(400, 300)

        self.tabs.addTab(self.experimental_data_tab, "Experimental Data")
        self.tabs.addTab(self.flatfield_tab, "Flatfield")
        self.tabs.addTab(self.calibration_with_powder_tab, "Calibration with Powder")

        # self.generate_contextual_data_group()
        self.layout.addWidget(self.tabs)

    def browse_file(self) -> None:
        if hasattr(self, "scan"):
            temp = self.scan
        else:
            temp = None
        cursor_position = QCursor.pos()
        directory = get_current_directory().replace("/utils", "").replace("/nexVisu", "")
        options = QFileDialog.Options()
        options |= QFileDialog.DontResolveSymlinks
        if sys.platform.startswith('linux'):
            if platform.linux_distribution()[0] == 'ubuntu':
                options |= QFileDialog.DontUseNativeDialog
        if self.tabs.currentIndex() == 0:
            self.scan, _ = QFileDialog.getOpenFileName(self, 'Choose the scan file you want to \
visualize.', directory, '*.nxs', options=options)
            if self.scan != "":
                self.experimental_data_tab.scan_label.setText(self.scan.split('/')[-1])
                self.experimental_data_tab.scanLabelChanged.emit(self.scan)
            else:
                # If a scan was selected and the user kills the dialog
                if temp is not None:
                    self.scan = temp
                    self.experimental_data_tab.scan_label.setText(self.scan.split('/')[-1])
                else:
                    self.experimental_data_tab.scan_label.setText("Click on the button to search for the scan you want")
        # Else it means user wants to chose a flatscan that will help reduce the noise in the experiment file
        else:
            self.flat_scan, _ = QFileDialog.getOpenFileName(self, "Choose the flatscan file you want to compute.", directory, "*.nxs *.hdf5", options=options)
            if self.flat_scan != "":
                self.flatfield_tab.flat_scan_viewer.clear()
                self.flatfield_tab.flat_scan_input1.setText(self.flat_scan.split('/')[-1])
