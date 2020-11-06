from constants import DataPath
from h5py import File
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, QTimer
from utils.dataViewers import RawDataViewer, UnfoldedDataViewer
from utils.nexusNavigation import get_dataset
from utils.imageProcessing import compute_geometry, correct_and_unfold_data, get_angles

import numpy


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

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.tab1, "Raw data")
        self.tabs.addTab(self.tab2, "Unfolded data")
        self.tabs.addTab(self.tab3, "Diffraction diagramme")
        self.tabs.addTab(self.tab4, "Fitted data")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.raw_data_viewer = RawDataViewer(self)
        self.tab1.layout.addWidget(self.raw_data_viewer)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self.tab2)
        self.unfolded_data_viewer = UnfoldedDataViewer(self)
        # self.unfolded_data_viewer = UnfoldCanvas()
        # self.toolbar = NavigationToolbar2QT(self.unfolded_data_viewer, self)
        # self.tab2.layout.addWidget(self.toolbar)
        self.tab2.layout.addWidget(self.unfolded_data_viewer)

        self.unfolded_data_viewer.show()

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

        self.unfold_timer.timeout.connect(self.unfold_data)
        self.unfolded_data_viewer.selector.selectionChanged.connect(self.synchronize_visualisation)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

    def set_data(self, path: str) -> None:
        self.path = path
        with File(path, mode='r') as h5file:
            self.raw_data = get_dataset(h5file, DataPath.IMAGE_INTERPRETATION.value)[:]
        # We put the raw data in the dataviewer
        self.raw_data_viewer.set_movie(self.raw_data)
        # We allocate a number of view in the stack
        self.unfolded_data_viewer.set_stack_slider(self.raw_data.shape[0])

    def start_unfolding_raw_data(self, calibration: dict) -> None:
        if self.is_unfolding:
            self.reset_unfolding()

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

            # Add the unfolded image to the scatter stack of image.
            self.unfolded_data_viewer.add_scatter(unfolded_data, 10)

            print(f"Unfolded the image number {index} in {self.path} scan")
        except StopIteration:
            self.unfold_timer.stop()
            self.is_unfolding = False

    def get_flatfield(self, flat_img: numpy.ndarray):
        self.flatfield_image = flat_img

    def synchronize_visualisation(self):
        # When user change the unfolded view, it set the raw image to the same frame
        self.raw_data_viewer.setFrameNumber(self.unfolded_data_viewer.selector.selection()[0])

    def reset_unfolding(self):
        self.is_unfolding = False
        self.unfold_timer.stop()
        self.unfolded_data_viewer.reset_scatter_view()
