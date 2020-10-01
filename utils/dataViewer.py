from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtGui import QIcon

from silx.gui.plot.StackView import StackView
from silx.gui.plot.PlotActions import PlotAction
from silx.gui.qt import QToolBar

class DataViewer(StackView):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.createAction = False
        self.setYAxisInverted()
        self.setKeepDataAspectRatio()
        self.toolbar = QToolBar("Custom toolbar")
        self._plot.addToolBar(self.toolbar)

    def set_movie(self, images):
        if self.createAction:
            self.toolbar.clear()
        else:
            self.createAction = True
        self.action_movie = DataViewerMovie(self._plot, images.shape[0], parent=self)
        self.action_pause = PauseMovie(self._plot, self.action_movie, parent=self)
        self.action_resume = ResumeMovie(self._plot, self.action_movie, parent=self)
        self.toolbar.addAction(self.action_movie)
        self.toolbar.addAction(self.action_pause)
        self.setStack(images)
        self.setColormap("viridis", autoscale=True, normalization='log')

        self.action_pause.triggered.connect(self.update_pause_button)
        self.action_resume.triggered.connect(self.update_pause_button)

    def update_movie(self, images):
        if images is not None:
            self.setStack(images)
            self.setColormap("viridis", autoscale=True, normalization='log')
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
    def __init__(self, plot, nbImages, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='camera',
                            text='image movie',
                            tooltip='Runs a movie of the stacked images',
                            triggered=self.ask_interval,
                            parent=parent)
        self.nbImages = nbImages
        self.count = 0

    def ask_interval(self) -> None:
        inputInterval = QInputDialog().getDouble(self.parent(),
                                                 "ms for the movie?",
                                                 "milliseconds :",
                                                 value=50.0,
                                                 min=0.0001,
                                                 max=5000,
                                                 decimals=4)
        if not inputInterval[0] is None:
            self.dataTimer = QTimer(self, interval=inputInterval[0])
            self.dataTimer.timeout.connect(self.data_viewer_movie)
            self.dataTimer.start()

    def data_viewer_movie(self) -> None:
        if self.count < self.nbImages:
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
                            triggered=self.pauseMovie,
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
                            triggered=self.resumeMovie,
                            parent=parent)
        self.movie = movie

    def resume_movie(self) -> None:
        # Resume the movie of the stacked images movie
        self.movie.dataTimer.start()
