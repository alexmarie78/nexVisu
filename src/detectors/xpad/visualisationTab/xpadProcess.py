import math

from h5py import File

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QToolBar
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from scipy.signal import find_peaks
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.plot import Plot1D

from detectors.xpad.visualisationTab.fittingDataTab.fittingDataTab import FittingDataTab
from detectors.xpad.visualisationTab.unfoldingDataTab.unfoldingDataTab import UnfoldingDataTab

from constants import DataPath
from utils.dataViewers import RawDataViewer
from utils.fitAction import FitAction
from utils.imageProcessing import compute_geometry, correct_and_unfold_data, get_angles, extract_diffraction_diagram
from utils.nexusNavigation import get_dataset


import numpy
import os


class XpadVisualisation(QWidget):
    unfoldButtonClicked = pyqtSignal()

    def __init__(self):
        super(QWidget, self).__init__()
        self.layout = QVBoxLayout(self)
        self.raw_data = None
        self.flatfield_image = None
        self.path = None
        self.diagram_data_array = []
        self.angles = []

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.raw_data_tab = QWidget()
        # Create an unfolding data tab
        self.unfolded_data_tab = UnfoldingDataTab(self)
        self.diagram_tab = QWidget()
        self.fitting_data_tab = QWidget()

        # Create raw data display tab
        self.raw_data_tab.layout = QVBoxLayout(self.raw_data_tab)
        self.raw_data_viewer = RawDataViewer(self.raw_data_tab)

        # Create diagram plot data tab
        self.diagram_tab.layout = QVBoxLayout(self.diagram_tab)
        self.diagram_data_plot = Plot1D(self.diagram_tab)

        # Create fitting curve tab
        self.fitting_data_tab.layout = QVBoxLayout(self.fitting_data_tab)
        self.fitting_data_selector = NumpyAxesSelector(self.fitting_data_tab)
        self.fitting_data_plot = Plot1D(self.fitting_data_tab)
        self.fitting_widget = self.fitting_data_plot.getFitAction()
        self.fit_action = FitAction(plot=self.fitting_data_plot, parent=self.fitting_data_plot)
        self.toolbar = QToolBar("New")

        # Create automatic fitting tab
        self.automatic_fit_tab = FittingDataTab(self)

        self.unfolded_data_tab.viewer.get_unfold_with_flatfield_action().unfoldWithFlatfieldClicked.connect(self.get_calibration)
        self.unfolded_data_tab.viewer.get_unfold_action().unfoldClicked.connect(self.get_calibration)
        self.unfolded_data_tab.unfoldingFinished.connect(self.create_diagram_array)

        self.init_UI()

    def init_UI(self):

        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.raw_data_tab, "Raw data")
        self.tabs.addTab(self.unfolded_data_tab, "Unfolded data")
        self.tabs.addTab(self.diagram_tab, "Diffraction diagram")
        self.tabs.addTab(self.fitting_data_tab, "Fitted data")
        self.tabs.addTab(self.automatic_fit_tab, "Automatic fit")

        self.raw_data_tab.layout.addWidget(self.raw_data_viewer)

        self.diagram_tab.layout.addWidget(self.diagram_data_plot)

        self.diagram_data_plot.setGraphTitle(f"Diagram diffraction")
        self.diagram_data_plot.setGraphXLabel("two-theta (°)")
        self.diagram_data_plot.setGraphYLabel("intensity")
        self.diagram_data_plot.setYAxisLogarithmic(True)

        self.fitting_data_selector.setNamedAxesSelectorVisibility(False)
        self.fitting_data_selector.setVisible(True)
        self.fitting_data_selector.setAxisNames("12")

        self.fitting_data_plot.setYAxisLogarithmic(True)
        self.fitting_data_plot.setGraphXLabel("two-theta (°)")
        self.fitting_data_plot.setGraphYLabel("intensity")

        self.fitting_data_plot.getRoiAction().trigger()
        self.fitting_widget.setXRangeUpdatedOnZoom(False)

        self.toolbar.addAction(self.fit_action)
        self.fit_action.setVisible(True)
        self.fitting_data_plot.addToolBar(self.toolbar)
        self.fitting_data_tab.layout.addWidget(self.fitting_data_plot)
        self.fitting_data_tab.layout.addWidget(self.fitting_data_selector)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

        # self.unfold_timer.timeout.connect(self.unfold_data)
        self.fitting_data_selector.selectionChanged.connect(self.fitting_curve)
        self.fitting_data_plot.getCurvesRoiWidget().sigROIWidgetSignal.connect(self.get_roi_list)
        self.unfolded_data_tab.viewer.scatter_selector.selectionChanged.connect(self.synchronize_visualisation)


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
        self.raw_data_viewer.set_movie(self.raw_data, self.flatfield_image)
        self.unfolded_data_tab.images = self.raw_data
        self.unfolded_data_tab.path = self.path
        # We allocate a number of view in the stack of unfolded data and fitting data
        self.unfolded_data_tab.viewer.set_stack_slider(self.raw_data.shape[0])
        self.fitting_data_selector.setData(numpy.zeros((self.raw_data.shape[0], 1, 1)))

    def set_calibration(self, calibration):
        # Check if there is a empty list of coordinate in the direct beam calibration
        if not [] in [value for value in calibration.values()]:
            self.unfolded_data_tab.calibration = calibration
            if self.unfolded_data_tab.images is not None:
                self.unfolded_data_tab.start_unfolding()
        else:
            print("Direct beam not calibrated yet.")

    def get_calibration(self):
        self.unfoldButtonClicked.emit()

    def create_diagram_array(self):
        for image in self.unfolded_data_tab.viewer.get_scatter_items():
            self.diagram_data_array.append(extract_diffraction_diagram(image[0],
                                                                       image[1],
                                                                       image[2],
                                                                       1.0 / self.unfolded_data_tab.geometry["calib"],
                                                                       -100,
                                                                       100,
                                                                       patch_data_flag=True))
        self.plot_diagram()
        self.automatic_fit_tab.set_data_to_fit(self.diagram_data_array)
        self.fitting_data_selector.selectionChanged.emit()

    def plot_diagram(self, images_to_remove=[-1]):
        self.diagram_data_plot.setGraphTitle(f"Diagram diffraction of {self.path.split('/')[-1]}")
        for index, curve in enumerate(self.diagram_data_array):
            if index not in images_to_remove:
                """
                peaks, _ = find_peaks(curve[1], threshold=2, distance=1, prominence=1)
                for peak_index, peak in enumerate(peaks):
                    assymptote_x = [curve[0][peak]] * 2
                    assymptote_y = self.diagram_data_plot.getGraphYLimits()
                    self.diagram_data_plot.addCurve(assymptote_x, assymptote_y, f'Peak {peak_index} of image {index}')
                """
                self.diagram_data_plot.addCurve(curve[0], curve[1], f'Data of image {index}',
                                                color="#0000FF", replace=False, symbol='o')

    def get_flatfield(self, flat_img: numpy.ndarray):
        self.flatfield_image = flat_img
        self.raw_data_viewer.get_action_flatfield().set_flatfield(self.flatfield_image)
        self.unfolded_data_tab.flatfield = flat_img

    def synchronize_visualisation(self):
        # When user change the unfolded view, it set the raw image to the same frame
        self.raw_data_viewer.setFrameNumber(self.unfolded_data_tab.viewer.scatter_selector.selection()[0])

    def fitting_curve(self):
        if len(self.diagram_data_array) > 0:
            self.clear_plot_fitting_widget()
            curve = self.diagram_data_array[self.fitting_data_selector.selection()[0]]
            self.fitting_data_plot.addCurve(curve[0], curve[1], symbol='o')
            self.set_graph_limits(curve)

    def get_roi_list(self, events: dict):
        self.rois_list = list(events["roilist"])

    def clear_plot_fitting_widget(self):
        self.fitting_data_plot.clear()
        self.fitting_data_plot.clearMarkers()

    def set_graph_limits(self, curve):
        indexes_not_nan = numpy.where(numpy.logical_and(~numpy.isnan(curve[1]), ~numpy.isinf(curve[1])))[0]
        index_x_min = indexes_not_nan[0]
        index_x_max = indexes_not_nan[-1]

        index_y_min = int(numpy.floor(min(curve[1][indexes_not_nan[0]: indexes_not_nan[-1] + 1])))
        index_y_max = int(numpy.ceil(max(curve[1][indexes_not_nan[0]: indexes_not_nan[-1] + 1])))
        self.fitting_data_plot.setLimits(curve[0][index_x_min],
                                         curve[0][index_x_max],
                                         index_y_min, index_y_max)


