from h5py import File
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QPushButton, QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
from utils.dataViewer import DataViewer
from utils.nexusNavigation import get_dataset, DatasetPathWithAttribute
from utils.imageProcessing import correct_and_unfold_data

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

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(400,300)

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

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

    def set_data(self, path: str) -> None:
        self.path = path
        with File(path, mode='r') as h5file:
            self.raw_data = numpy.zeros(get_dataset(h5file, DatasetPathWithAttribute("interpretation",b"image")).shape)
            for idx, data in enumerate(get_dataset(h5file, DatasetPathWithAttribute("interpretation",b"image"))):
                self.raw_data[idx] = data
        self.raw_data_viewer.set_movie(self.raw_data)

    def unfold_raw_data(self, calibration: dict) -> None:
        # Unfold raw datas
        unfolded_data = correct_and_unfold_data(self.flatfield_image, self.raw_data, self.path, calibration)
        # Plot them in stack
        for unfolded_image in unfolded_data:
            self.unfolded_data_viewer.axes.tripcolor(unfolded_image[1], unfolded_image[2], unfolded_image[3])
            self.unfolded_data_viewer.show()
        # self.unfolded_data_viewer.set_movie(unfolded_data)

    def get_flatfield(self, flat_img: numpy.ndarray):
        self.flatfield_image = flat_img


