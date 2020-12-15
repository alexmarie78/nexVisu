from h5py import File
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer
from silx.gui.plot import Plot1D

from src.constants import DataPath
from src.utils.dataViewers import RawDataViewer, UnfoldedDataViewer
from src.utils.imageProcessing import compute_geometry, correct_and_unfold_data, get_angles
from src.utils.nexusNavigation import get_dataset

import numpy
import os


class XpadVisualisation(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()
        self.layout = QVBoxLayout(self)
        self.raw_data = None
        self.flatfield_image = None
        self.path = None
        self.data_iterator = None
        self.index_iterator = None
        self.unfold_timer = QTimer(self, interval=1)
        self.gamma_array = None
        self.delta_array = None
        self.geometry = None
        self.is_unfolding = False
        self.diagram = []
        self.angles = []
        self.init_UI()

    def init_UI(self):

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.raw_data_tab = QWidget()
        self.unfolded_data_tab = QWidget()
        self.diagram_tab = QWidget()
        self.fitted_data_tab = QWidget()
        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.raw_data_tab, "Raw data")
        self.tabs.addTab(self.unfolded_data_tab, "Unfolded data")
        self.tabs.addTab(self.diagram_tab, "Diffraction diagram")
        self.tabs.addTab(self.fitted_data_tab, "Fitted data")

        # Create raw data display tab
        self.raw_data_tab.layout = QVBoxLayout(self.raw_data_tab)
        self.raw_data_viewer = RawDataViewer(self)
        self.raw_data_tab.layout.addWidget(self.raw_data_viewer)

        # Create unfolded and corrected data tab
        self.unfolded_data_tab.layout = QVBoxLayout(self.unfolded_data_tab)
        self.unfolded_data_viewer = UnfoldedDataViewer(self)
        self.unfolded_data_tab.layout.addWidget(self.unfolded_data_viewer)

        self.unfolded_data_viewer.show()

        # Create diagram plot data tab
        self.diagram_tab.layout = QVBoxLayout(self.diagram_tab)
        self.diagram_data_plot = Plot1D(self.diagram_tab)
        self.diagram_tab.layout.addWidget(self.diagram_data_plot)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

        self.unfold_timer.timeout.connect(self.unfold_data)
        self.unfolded_data_viewer.scatter_selector.selectionChanged.connect(self.synchronize_visualisation)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

    def set_data(self, path: str) -> None:
        self.path = path
        with File(os.path.join(path), mode='r') as h5file:
            self.raw_data = get_dataset(h5file, DataPath.IMAGE_INTERPRETATION.value)[:]
        # We put the raw data in the dataviewer
        self.raw_data_viewer.set_movie(self.raw_data)
        # We allocate a number of view in the stack
        self.unfolded_data_viewer.set_stack_slider(self.raw_data.shape[0])

    def start_unfolding_raw_data(self, calibration: dict) -> None:
        if self.is_unfolding:
            self.reset_unfolding()

        self.scatter_factor, _ = QInputDialog.getInt(self, "You ran unfolding data process",
                                                  "Choose a factor to speed the scatter",
                                                  QLineEdit.Normal)

        if not isinstance(self.scatter_factor, int):
            QMessageBox(QMessageBox.Icon.Critical, "Can't send contextual data",
                        "You must enter a integer (whole number) to run the unfolding of data").exec()
        else:
            if self.scatter_factor <= 0:
                self.scatter_factor = 1
            # Create geometry of the detector
            self.geometry = compute_geometry(calibration, self.flatfield_image, self.raw_data)
            # Collect the angles
            self.delta_array, self.gamma_array = get_angles(self.path)

            # Populate the iterators that will help running the unfolding of data
            self.data_iterator = iter([image for image in self.raw_data])
            self.index_iterator = iter([i for i in range(self.raw_data.shape[0])])

            # Start the timer and the unfolding
            self.unfold_timer.start()
            self.is_unfolding = True

    def unfold_data(self):
        try:
            image = next(self.data_iterator)
            index = next(self.index_iterator)
            delta = self.delta_array[index] if len(self.delta_array) > 1 else self.delta_array[0]
            gamma = self.gamma_array[index] if len(self.gamma_array) > 1 else self.gamma_array[0]
            # Correct and unfold raw data
            unfolded_data = correct_and_unfold_data(self.geometry, image, delta, gamma)
            self.diagram.append(numpy.cumsum(unfolded_data[0], axis=0))
            self.angles.append(unfolded_data[0][::self.scatter_factor])

            # Add the unfolded image to the scatter stack of image.
            self.unfolded_data_viewer.add_scatter(unfolded_data, self.scatter_factor)

            print(f"Unfolded the image number {index} in {self.path} scan")
        except StopIteration:
            self.unfold_timer.stop()
            self.is_unfolding = False
            self.diagram_data_plot.addCurve(numpy.concatenate(self.angles, axis=None),
                                            numpy.concatenate(self.diagram, axis=None))

    def get_flatfield(self, flat_img: numpy.ndarray):
        self.flatfield_image = flat_img

    def synchronize_visualisation(self):
        # When user change the unfolded view, it set the raw image to the same frame
        self.raw_data_viewer.setFrameNumber(self.unfolded_data_viewer.scatter_selector.selection()[0])

    def reset_unfolding(self):
        self.is_unfolding = False
        self.unfold_timer.stop()
        self.unfolded_data_viewer.reset_scatter_view()
