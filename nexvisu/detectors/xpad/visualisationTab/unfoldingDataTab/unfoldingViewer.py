from PyQt5.QtWidgets import QWidget, QVBoxLayout
from silx.gui.colors import Colormap
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.qt import QToolBar
from silx.gui.plot.ScatterView import ScatterView
from detectors.xpad.visualisationTab.unfoldingDataTab.unfoldingActions import Unfold, UnfoldWithFlatfield, SaveAction

import numpy
import time


class UnfoldedDataViewer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.scatter_view = ScatterView(self)
        colormap = Colormap('viridis', normalization='log')
        self.scatter_view.setGraphTitle("Stack of unfolded data")
        self.scatter_view.setColormap(colormap)
        self.plot = self.scatter_view.getPlotWidget()
        self.plot.setGraphXLabel("two-theta (°)")
        self.plot.setGraphYLabel("psi (°)")
        self.plot.setKeepDataAspectRatio(False)
        self.plot.setYAxisInverted(True)

        self.scatter_selector = NumpyAxesSelector(self)
        # Prevent user from changing dimensions for the plot
        self.scatter_selector.setNamedAxesSelectorVisibility(False)
        self.scatter_selector.setVisible(True)
        self.scatter_selector.setAxisNames("12")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scatter_view)
        self.layout.addWidget(self.scatter_selector)

        self.stack = []

        self.initial_data_flag = True

        self.toolbar = QToolBar("Custom toolbar 1")
        self.scatter_view.addToolBar(self.toolbar)

        self.action_unfold = Unfold(self.plot, parent=self)
        self.action_unfold_with_flatfield = UnfoldWithFlatfield(self.plot, parent=self)
        self.action_save = SaveAction(self.plot, parent=self)

        self.toolbar.addAction(self.action_unfold)
        self.toolbar.addAction(self.action_unfold_with_flatfield)
        self.toolbar.addAction(self.action_save)

        self.scatter_selector.selectionChanged.connect(self.change_displayed_data)

    def add_scatter(self, scatter_image: tuple, scatter_factor: int):
        # Add an image to the stack. If it is the first, emit the selectionChanged signal to plot the first image
        self.stack.append((scatter_image[0][::scatter_factor],
                           scatter_image[1][::scatter_factor],
                           scatter_image[2][::scatter_factor]))
        if self.initial_data_flag:
            self.scatter_selector.selectionChanged.emit()
            self.initial_data_flag = False

    def set_stack_slider(self, nb_images: int):
        # Set the size of the sliderbar that will let the user navigate the images
        self.clear_scatter_view()
        self.scatter_selector.setData(numpy.zeros((nb_images, 1, 1)))

    def change_displayed_data(self):
        # If there is at least one unfolded image, clear the view, unpack the data and plot a scatter view of the image
        if len(self.stack) > 0:
            self.clear_scatter_view()
            tth_array, psi_array, intensity = self.stack[self.scatter_selector.selection()[0]]
            self.plot.setGraphXLimits(min(tth_array) - 0.0, max(tth_array) + 0.0)
            self.plot.setGraphYLimits(min(psi_array) - 5.0, max(psi_array) + 5.0)
            start = time.time()
            self.scatter_view.setData(tth_array, psi_array, intensity, copy=False)
            end = time.time()
            print("Setting the data took :", (end - start) * 1000.0, " ms")

    def clear_scatter_view(self):
        self.scatter_view.setData(None, None, None)

    def reset_scatter_view(self):
        self.clear_scatter_view()
        self.stack = []
        self.initial_data_flag = True

    def get_scatter_item(self, index: int) -> tuple:
        return self.stack[index]

    def get_scatter_items(self) -> list:
        return self.stack

    def get_unfold_action(self):
        return self.action_unfold

    def get_unfold_with_flatfield_action(self):
        return self.action_unfold_with_flatfield
