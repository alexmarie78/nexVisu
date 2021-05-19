from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QFileDialog

from utils.nexusNavigation import get_current_directory
from detectors.xpad.initialDataTab.contextualDataTab.contextualDataGroup import ContextualDataGroup
from detectors.xpad.initialDataTab.flatfieldTab.flatfieldGroup import FlatfieldGroup
from constants import get_dialog_options


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

        self.scan = None
        self.flat_scan = None

        # self.generate_contextual_data_group()
        self.layout.addWidget(self.tabs)

    def browse_file(self) -> None:
        directory = get_current_directory().replace("/utils", "").replace("/nexVisu", "")
        if self.tabs.currentIndex() == 0:
            scan, validate_dialog = QFileDialog.getOpenFileName(self, 'Choose the scan file you want to visualize.',
                                                                directory, '*.nxs', options=get_dialog_options())
            if validate_dialog:
                self.scan = scan
                self.experimental_data_tab.scan_label.setText(self.scan.split('/')[-1])
                self.experimental_data_tab.scanLabelChanged.emit(self.scan)
            else:
                # If a scan was selected and the user kills the dialog
                if self.scan is not None:
                    self.experimental_data_tab.scan_label.setText(self.scan.split('/')[-1])
                    print("Scan dialog killed, former scan used.")
                else:
                    self.experimental_data_tab.scan_label.setText("Click on the button to search for the scan you want")
                    print("Scan dialog killed, no scan used.")
        # Else it means user wants to chose a flatscan that will help reduce the noise in the experiment file
        else:
            flat_scan, validate_dialog = QFileDialog.getOpenFileName(self,
                                                                     "Choose the flatscan file you want to compute.",
                                                                     directory, "*.nxs *.hdf5",
                                                                     options=get_dialog_options())
            if validate_dialog:
                self.flat_scan = flat_scan
                self.flatfield_tab.flat_scan_viewer.clear()
                self.flatfield_tab.flat_scan_input1.setText(self.flat_scan.split('/')[-1])
            else:
                print("Flatfield scan dialog killed. No or former flatfield used.")
