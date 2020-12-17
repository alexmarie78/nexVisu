from h5py import File
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QInputDialog, QLineEdit, QMessageBox, QHBoxLayout
from PyQt5.QtCore import pyqtSlot, QTimer
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.fit import FitWidget
from silx.gui.plot import Plot1D

from src.constants import DataPath
from src.utils.dataViewers import RawDataViewer, UnfoldedDataViewer
from src.utils.imageProcessing import compute_geometry, correct_and_unfold_data, get_angles, extract_diffraction_diagram
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
        self.diagram_data_array = []
        self.angles = []
        self.init_UI()

    def init_UI(self):

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.raw_data_tab = QWidget()
        self.unfolded_data_tab = QWidget()
        self.diagram_tab = QWidget()
        self.fitting_data_tab = QWidget()
        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.raw_data_tab, "Raw data")
        self.tabs.addTab(self.unfolded_data_tab, "Unfolded data")
        self.tabs.addTab(self.diagram_tab, "Diffraction diagram")
        self.tabs.addTab(self.fitting_data_tab, "Fitted data")

        # Create raw data display tab
        self.raw_data_tab.layout = QVBoxLayout(self.raw_data_tab)
        self.raw_data_viewer = RawDataViewer(self.raw_data_tab)
        self.raw_data_tab.layout.addWidget(self.raw_data_viewer)

        # Create unfolded and corrected data tab
        self.unfolded_data_tab.layout = QVBoxLayout(self.unfolded_data_tab)
        self.unfolded_data_viewer = UnfoldedDataViewer(self.unfolded_data_tab)
        self.unfolded_data_tab.layout.addWidget(self.unfolded_data_viewer)

        self.unfolded_data_viewer.show()

        # Create diagram plot data tab
        self.diagram_tab.layout = QVBoxLayout(self.diagram_tab)
        self.diagram_data_plot = Plot1D(self.diagram_tab)
        self.diagram_tab.layout.addWidget(self.diagram_data_plot)

        self.diagram_data_plot.setGraphTitle(f"Diagram diffraction")
        self.diagram_data_plot.setGraphXLabel("two-theta (°)")
        self.diagram_data_plot.setGraphYLabel("intensity")
        self.diagram_data_plot.setYAxisLogarithmic(True)

        # Create fitting curve tab
        self.fitting_data_tab.layout = QVBoxLayout(self.fitting_data_tab)
        self.fitting_data_widget = FitWidget(self.fitting_data_tab)
        self.fitting_data_selector = NumpyAxesSelector(self.fitting_data_tab)
        self.fitting_data_selector.setNamedAxesSelectorVisibility(False)
        self.fitting_data_selector.setVisible(True)
        self.fitting_data_selector.setAxisNames("12")
        self.fitting_data_plot = Plot1D(self.fitting_data_tab)
        self.fitting_data_plot.setYAxisLogarithmic(True)


        self.fitting_data_widget_bis = QWidget()
        self.fitting_data_widget_bis.layout = QHBoxLayout(self.fitting_data_widget_bis)
        self.fitting_data_widget_bis.layout.addWidget(self.fitting_data_widget)
        self.fitting_data_widget_bis.layout.addWidget(self.fitting_data_plot)
        self.fitting_data_tab.layout.addWidget(self.fitting_data_widget_bis)
        self.fitting_data_tab.layout.addWidget(self.fitting_data_selector)

        """
        self.fitting_data_tab.layout.addWidget(self.fitting_data_widget)
        self.fitting_data_tab.layout.addWidget(self.fitting_data_plot)
        self.fitting_data_tab.layout.addWidget(self.fitting_data_selector)
        """

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

        self.unfold_timer.timeout.connect(self.unfold_data)
        self.fitting_data_selector.selectionChanged.connect(self.fitting_curve)
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
        # We allocate a number of view in the stack of unfolded data and fitting data
        self.unfolded_data_viewer.set_stack_slider(self.raw_data.shape[0])
        self.fitting_data_selector.setData(numpy.zeros((self.raw_data.shape[0], 1, 1)))

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
            self.diagram_data_array.append(extract_diffraction_diagram(unfolded_data[0],
                                                                       unfolded_data[1],
                                                                       unfolded_data[2],
                                                                       1.0/self.geometry["calib"],
                                                                       -100,
                                                                       100,
                                                                       patch_data_flag=True))

            # Add the unfolded image to the scatter stack of image.
            self.unfolded_data_viewer.add_scatter(unfolded_data, self.scatter_factor)

            print(f"Unfolded the image number {index} in {self.path} scan")
        except StopIteration:
            self.unfold_timer.stop()
            self.is_unfolding = False
            self.plot_diagram([0, 1])
            self.fitting_data_selector.selectionChanged.emit()

    def get_flatfield(self, flat_img: numpy.ndarray):
        self.flatfield_image = flat_img

    def synchronize_visualisation(self):
        # When user change the unfolded view, it set the raw image to the same frame
        self.raw_data_viewer.setFrameNumber(self.unfolded_data_viewer.scatter_selector.selection()[0])

    def reset_unfolding(self):
        self.is_unfolding = False
        self.unfold_timer.stop()
        self.unfolded_data_viewer.reset_scatter_view()

    def plot_diagram(self, images_to_remove=[-1]):
        self.diagram_data_plot.setGraphTitle(f"Diagram diffraction of {self.path.split('/')[-1]}")
        for index, curve in enumerate(self.diagram_data_array):
            if index not in images_to_remove:
                self.diagram_data_plot.addCurve(curve[0], curve[1], f'Data of image {index}', color="#0000FF", replace=False)

    def fitting_curve(self):
        if len(self.diagram_data_array) > 0:
            self.clear_fitting_widget()
            curve = self.diagram_data_array[self.fitting_data_selector.selection()[0]]
            # Collect every index of the array where the value is not nan
            indexes_not_nan = numpy.where(~numpy.isnan(curve[1]))[0]

            index_x_min = indexes_not_nan[0]
            index_x_max = indexes_not_nan[-1]

            index_y_min = int(numpy.floor(min(curve[1][indexes_not_nan[0]: indexes_not_nan[-1] + 1])))
            index_y_max = int(numpy.ceil(max(curve[1][indexes_not_nan[0]: indexes_not_nan[-1] + 1])))

            self.fitting_data_widget.setData(curve[0], curve[1])
            self.fitting_data_plot.addCurve(curve[0], curve[1])
            self.fitting_data_plot.setLimits(curve[0][index_x_min],
                                             curve[0][index_x_max],
                                             index_y_min, index_y_max)

    def clear_fitting_widget(self):
        self.fitting_data_widget.setData(None, None, None)



