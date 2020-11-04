from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QInputDialog, QWidget, QVBoxLayout

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

        self.plot = ScatterView()
        colormap = Colormap('viridis', normalization='log')
        self.plot.setGraphTitle("Stack of unfolded data")
        self.plot.setColormap(colormap)
        self.plot.getPlotWidget().setGraphXLabel("two-th angle (theta)")
        self.plot.getPlotWidget().setGraphYLabel("psi")
        self.plot.getPlotWidget().setKeepDataAspectRatio(False)
        self.plot.getPlotWidget().setYAxisInverted(True)

        self.selector = NumpyAxesSelector()
        # Prevent user from changing dimensions for the plot
        self.selector.setNamedAxesSelectorVisibility(False)
        self.selector.setVisible(True)
        self.selector.setAxisNames("12")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.plot)
        self.layout.addWidget(self.selector)

        self.stack = []

        self.initial_data_flag = True

        self.selector.selectionChanged.connect(self.change_displayed_data)

    def add_scatter(self, scatter_image: tuple):
        self.stack.append(scatter_image)
        if self.initial_data_flag:
            self.selector.selectionChanged.emit()
            self.initial_data_flag = False

    def set_stack(self, nb_images: int):
        self.clear_scatter_view()
        self.selector.setData(numpy.zeros((nb_images, 1, 1)))

    def change_displayed_data(self):
        if len(self.stack) > 0:
            start = time.time()
            self.clear_scatter_view()
            x_array = self.stack[self.selector.selection()[0]][0]
            y_array = self.stack[self.selector.selection()[0]][1]
            intensity = self.stack[self.selector.selection()[0]][2]
            # x_array, y_array, intensity = self.stack[self.selector.selection()[0]]
            end = time.time()
            print("unpacking took :", (end-start)*1000.0)
            start = time.time()
            self.plot.setData(x_array, y_array, intensity)
            end = time.time()
            print("Setting the data took :", (end - start) * 1000.0)

    def clear_scatter_view(self):
        self.plot.setData(None, None, None)


class RawDataViewer(StackView):
    def __init__(self, parent):
        super().__init__(parent=parent, aspectRatio=True, yinverted=True)
        self.setGraphTitle("Stack of raw data")
        self.setColormap("viridis", autoscale=True, normalization='log')
        self.getPlotWidget().setGraphXLabel("x in pixel")
        self.getPlotWidget().setGraphYLabel("y in pixel")
        self.getPlotWidget().setYAxisInverted(True)

        self.action_already_created = False

        self.toolbar = QToolBar("Custom toolbar")
        self._plot.addToolBar(self.toolbar)
        self.action_movie = None
        self.action_pause = None
        self.action_resume = None

    def set_movie(self, images):
        if self.action_already_created:
            self.toolbar.clear()
        else:
            self.action_already_created = True
        self.action_movie = DataViewerMovie(self._plot, images.shape[0], parent=self)
        self.action_pause = PauseMovie(self._plot, self.action_movie, parent=self)
        self.action_resume = ResumeMovie(self._plot, self.action_movie, parent=self)
        self.toolbar.addAction(self.action_movie)
        self.toolbar.addAction(self.action_pause)
        self.setStack(images)

        self.action_pause.triggered.connect(self.update_pause_button)
        self.action_resume.triggered.connect(self.update_pause_button)

    def update_movie(self, images):
        if images is not None:
            self.setStack(images)
            self.setGraphTitle("Stack of raw data")
            self.setColormap("viridis", autoscale=True, normalization='log')
            self.getPlotWidget().setGraphXLabel("x in pixel")
            self.getPlotWidget().setGraphYLabel("y in pixel")
            self.getPlotWidget().setYAxisInverted(True)
        else:
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
            self.data_timer = QTimer(self, interval=input_interval[0])
            self.dataTimer.timeout.connect(self.data_viewer_movie)
            self.dataTimer.start()

    def data_viewer_movie(self) -> None:
        if self.count < self.nb_images:
            self.parent().setFrameNumber(self.count)
            self.count = self.count + 1
        else:
            self.dataTimer.stop()
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
        self.movie.dataTimer.stop()


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
