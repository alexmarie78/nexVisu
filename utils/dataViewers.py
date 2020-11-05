from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QInputDialog, QWidget, QVBoxLayout

from silx import version as silx_version
from silx.gui.colors import Colormap
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.plot.ScatterView import ScatterView
from silx.gui.plot.StackView import StackView
from silx.gui.plot.PlotActions import PlotAction
from silx.gui.qt import QToolBar

import numpy
import time


class UnfoldedDataViewer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.scatter_view = ScatterView(self)
        colormap = Colormap('viridis', normalization='log')
        self.scatter_view.setGraphTitle("Stack of unfolded data")
        self.scatter_view.setColormap(colormap)
        self.scatter_view.getPlotWidget().setGraphXLabel("two-th angle (theta)")
        self.scatter_view.getPlotWidget().setGraphYLabel("psi")
        self.scatter_view.getPlotWidget().setKeepDataAspectRatio(False)
        self.scatter_view.getPlotWidget().setYAxisInverted(True)

        self.selector = NumpyAxesSelector(self)
        # Prevent user from changing dimensions for the plot
        self.selector.setNamedAxesSelectorVisibility(False)
        self.selector.setVisible(True)
        self.selector.setAxisNames("12")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scatter_view)
        self.layout.addWidget(self.selector)

        self.stack = []

        self.initial_data_flag = True

        self.selector.selectionChanged.connect(self.change_displayed_data)

    def add_scatter(self, scatter_image: tuple):
        # Add an image to the stack. If it is the first, emit the selectionChanged signal to plot the first image
        self.stack.append(scatter_image)
        if self.initial_data_flag:
            self.selector.selectionChanged.emit()
            self.initial_data_flag = False

    def set_stack(self, nb_images: int):
        # Set the size of the sliderbar that will let the user navigate the images
        self.clear_scatter_view()
        self.selector.setData(numpy.zeros((nb_images, 1, 1)))

    def change_displayed_data(self):
        # If there is at least one unfolded image, clear the view, unpack the data and plot a scatter view of the image
        if len(self.stack) > 0:
            self.clear_scatter_view()
            x_array, y_array, intensity = self.stack[self.selector.selection()[0]]
            self.scatter_view.getPlotWidget().setGraphXLimits(min(x_array) - 0.0, max(x_array) + 0.0)
            self.scatter_view.getPlotWidget().setGraphYLimits(min(y_array) - 5.0, max(y_array) + 5.0)
            start = time.time()
            self.scatter_view.setData(x_array, y_array, intensity, copy=False)
            end = time.time()
            print("Setting the data took :", (end - start) * 1000.0, " ms")

    def clear_scatter_view(self):
        self.scatter_view.setData(None, None, None)


class RawDataViewer(StackView):
    def __init__(self, parent):
        super().__init__(parent=parent, aspectRatio=True, yinverted=True)
        self.setGraphTitle("Stack of raw data")
        self.setColormap("viridis", autoscale=True, normalization='log')
        self.plot = self.getPlotWidget() if silx_version >= '0.13.0' else self.getPlot()
        self.plot.setGraphXLabel("x in pixel")
        self.plot.setGraphYLabel("y in pixel")
        self.plot.setYAxisInverted(True)

        self.action_already_created = False

        self.toolbar = QToolBar("Custom toolbar")
        self._plot.addToolBar(self.toolbar)
        self.action_movie = None
        self.action_pause = None
        self.action_resume = None

    def update_graph(self):
        self.setGraphTitle("Stack of raw data")
        self.setColormap("viridis", autoscale=True, normalization='log')
        self.plot.setGraphXLabel("x in pixel")
        self.plot.setGraphYLabel("y in pixel")
        self.plot.setYAxisInverted(True)

    def set_movie(self, images):
        if images is not None:
            self.toolbar.clear()

            self.action_movie = DataViewerMovie(self._plot, images.shape[0], parent=self)
            self.action_pause = PauseMovie(self._plot, self.action_movie, parent=self)
            self.action_resume = ResumeMovie(self._plot, self.action_movie, parent=self)

            self.toolbar.addAction(self.action_movie)
            self.toolbar.addAction(self.action_pause)

            self.setStack(images)
            self.update_graph()

            self.action_pause.triggered.connect(self.update_pause_button)
            self.action_resume.triggered.connect(self.update_pause_button)
        else:
            self.toolbar.clear()
            self.setStack(None)

    def update_pause_button(self):
        if self.toolbar.actions()[-1] == self.action_pause:
            self.toolbar.removeAction(self.action_pause)
            self.toolbar.addAction(self.action_resume)
        else:
            self.toolbar.removeAction(self.action_resume)
            self.toolbar.addAction(self.action_pause)


class DataViewerMovie(PlotAction):
    """QAction that runs a movie of the stacked images
    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, nb_images, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='camera',
                            text='image movie',
                            tooltip='Runs a movie of the stacked images',
                            triggered=self.ask_interval,
                            parent=parent)
        self.nb_images = nb_images
        self.count = 0
        self.data_timer = None

    def ask_interval(self) -> None:
        input_interval = QInputDialog().getDouble(self.parent(),
                                                  "ms for the movie?",
                                                  "milliseconds :",
                                                  value=50.0,
                                                  min=0.0001,
                                                  max=5000,
                                                  decimals=4)
        if input_interval[0] is not None:
            self.data_timer = QTimer(self, interval=input_interval[0]/1000.0)
            self.data_timer.timeout.connect(self.data_viewer_movie)
            self.data_timer.start()

    def data_viewer_movie(self) -> None:
        if self.count < self.nb_images:
            self.parent().setFrameNumber(self.count)
            self.count = self.count + 1
        else:
            self.data_timer.stop()
            self.count = 0


class PauseMovie(PlotAction):
    """QAction that  movie of the stacked images
    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, movie, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='item-2dim',
                            text='pause',
                            tooltip='Pauses the movie of the stacked images',
                            triggered=self.pause_movie,
                            parent=parent)
        self.movie = movie

    def pause_movie(self) -> None:
        # Pauses the stacked images movie
        self.movie.data_timer.stop()


class ResumeMovie(PlotAction):
    def __init__(self, plot, movie, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='next',
                            text='resume',
                            tooltip='Resumes the movie of the stacked images',
                            triggered=self.resume_movie,
                            parent=parent)
        self.movie = movie

    def resume_movie(self) -> None:
        # Resume the movie of the stacked images movie
        self.movie.data_timer.start()