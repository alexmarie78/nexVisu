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


class RawDataViewer(StackView):
    def __init__(self, parent):
        super().__init__(parent=parent, aspectRatio=True, yinverted=True, position=True)
        self.setColormap("viridis", autoscale=True, normalization='log')
        self.setLabels(("images", "x (pixel)", "y (pixel)"))
        self.setTitleCallback(self.title)
        self.plot = self.getPlotWidget() if silx_version >= '0.13.0' else self.getPlot()
        self.plot.setYAxisInverted(True)

        self.action_already_created = False

        self.toolbar = QToolBar("Custom toolbar")
        self._plot.addToolBar(self.toolbar)
        self.action_movie = None
        self.action_pause = None
        self.action_resume = None

    def title(self, image_index: int):
        return f"Image number {image_index} of the stack"

    def set_movie(self, images):
        if images is not None:
            self.toolbar.clear()

            self.action_movie = DataViewerMovie(self._plot, images.shape[0], parent=self)
            self.action_pause = PauseMovie(self._plot, self.action_movie, parent=self)
            self.action_resume = ResumeMovie(self._plot, self.action_movie, parent=self)

            self.toolbar.addAction(self.action_movie)
            self.toolbar.addAction(self.action_pause)

            self.setStack(images)
            self.setColormap("viridis", autoscale=True, normalization='log')

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
