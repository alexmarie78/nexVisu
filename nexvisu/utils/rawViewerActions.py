import numpy
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QInputDialog
from silx.gui.plot.actions import PlotAction


class DataViewerMovie(PlotAction):
    """QAction that runs a movie of the stacked images
    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, nb_images=0, parent=None):
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

    def set_movie_size(self, size):
        self.nb_images = size


class PauseMovie(PlotAction):
    """QAction that  movie of the stacked images
    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, movie=None, parent=None):
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
        if self.movie.data_timer:
            self.movie.data_timer.stop()

    def set_movie(self, movie):
        self.movie = movie


class ResumeMovie(PlotAction):
    def __init__(self, plot, movie=None, parent=None):
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
        if self.movie.data_timer:
            self.movie.data_timer.start()

    def set_movie(self, movie):
        self.movie = movie


class UseFlatfield(PlotAction):
    def __init__(self, plot, images=None, flatfield=None, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='stats-whole-items',
                            text='use flatfield',
                            tooltip='use flatfield to divide raw datas',
                            triggered=self.use_flatfield,
                            parent=parent)
        self.flatfield = flatfield
        self.images = images
        self.already_triggered = False

    def use_flatfield(self):
        index_image = self.parent().getFrameNumber()
        if self.already_triggered or self.flatfield is None:
            self.parent().setStack(self.images)
            self.parent().setFrameNumber(index_image)
            self.parent().setColormap("viridis", autoscale=True, normalization='log')
            self.already_triggered = False
        else:
            numpy.seterr(divide='ignore', invalid='ignore')
            images = [image / self.flatfield for image in self.images]
            self.parent().setStack(images)
            self.parent().setFrameNumber(index_image)
            self.parent().setColormap("viridis", autoscale=True, normalization='log')
            self.already_triggered = True
            numpy.seterr(divide='raise', invalid='raise')

    def set_flatfield(self, flatfield):
        self.flatfield = flatfield

    def set_images(self, images):
        self.images = images
