from constants import DataPath
from h5py import File
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, QTimer
from utils.dataViewer import DataViewer
from utils.nexusNavigation import get_dataset
from utils.imageProcessing import compute_geometry, correct_and_unfold_data, get_angles

import numpy


class UnfoldCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(UnfoldCanvas, self).__init__(fig)


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

        self.stop_flag = False

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.tab1, "Raw data")
        self.tabs.addTab(self.tab2, "Unfolded data")
        self.tabs.addTab(self.tab3, "Fitted data")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.raw_data_viewer = DataViewer(self)
        self.tab1.layout.addWidget(self.raw_data_viewer)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self.tab2)
        self.unfolded_data_viewer = UnfoldCanvas()
        self.toolbar = NavigationToolbar2QT(self.unfolded_data_viewer, self)
        self.tab2.layout.addWidget(self.toolbar)
        self.tab2.layout.addWidget(self.unfolded_data_viewer)

        self.unfolded_data_viewer.show()

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

        self.unfold_timer.timeout.connect(self.unfold_data)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

    def set_data(self, path: str) -> None:
        self.path = path
        with File(path, mode='r') as h5file:
            self.raw_data = get_dataset(h5file, DataPath.IMAGE_INTERPRETATION.value)[:]
        self.raw_data_viewer.set_movie(self.raw_data)

    def start_unfolding_raw_data(self, calibration: dict) -> None:
        # Clean the plot
        self.unfolded_data_viewer.axes.cla()
        # Create geometry of the detector
        self.geometry = compute_geometry(calibration, self.flatfield_image, self.raw_data)
        # Collect the angles
        self.delta_array, self.gamma_array = get_angles(self.path)

        # Populate the iterators that will help running the unfolding of data
        self.data_iterator = iter([image for image in self.raw_data])
        self.index_iterator = iter([i for i in range(self.raw_data.shape[0])])

        # Start the timer and the unfolding
        self.unfold_timer.start()

    def unfold_data(self):
        if not self.stop_flag:
            try:
                image = next(self.data_iterator)
                index = next(self.index_iterator)
                delta = self.delta_array[index] if len(self.delta_array) > 1 else self.delta_array[0]
                gamma = self.gamma_array[index] if len(self.gamma_array) > 1 else self.gamma_array[0]
                # Unfold raw data
                unfolded_data = correct_and_unfold_data(self.geometry, image, delta, gamma)
                # Plot them in stack
                self.unfolded_data_viewer.axes.tripcolor(unfolded_data[0],
                                                         unfolded_data[1],
                                                         unfolded_data[2],
                                                         cmap='viridis')
                self.unfolded_data_viewer.draw()
                print(f"Unfolded the image number {index} in {self.path} scan")
                self.stop_flag = True
            except StopIteration:
                self.unfold_timer.stop()

    def get_flatfield(self, flat_img: numpy.ndarray):
        self.flatfield_image = flat_img
