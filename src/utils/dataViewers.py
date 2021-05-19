from silx import version as silx_version
from silx.gui.plot.StackView import StackView
from silx.gui.plot.tools import PositionInfo
from silx.gui.qt import QToolBar, Qt
from utils.rawViewerActions import DataViewerMovie, PauseMovie, ResumeMovie, UseFlatfield


class RawDataViewer(StackView):
    def __init__(self, parent):
        super().__init__(parent=parent, aspectRatio=True, yinverted=True)

        self.setColormap("viridis", autoscale=True, normalization='log')
        self.setLabels(("images", "y (pixel)", "x (pixel)"))
        self.setTitleCallback(self.title)
        self.plot = self.getPlotWidget() if silx_version >= '0.13.0' else self.getPlot()
        self.plot.setYAxisInverted(True)

        self.action_already_created = False

        self.toolbar = QToolBar("Custom toolbar")
        self.plot.addToolBar(self.toolbar)
        self.action_use_flatfield = UseFlatfield(self.plot, parent=self)
        self.action_movie = DataViewerMovie(self.plot, parent=self)
        self.action_pause = PauseMovie(self.plot, self.action_movie, parent=self)
        self.action_resume = ResumeMovie(self.plot, self.action_movie, parent=self)

        self.toolbar.addAction(self.action_use_flatfield)
        self.toolbar.addAction(self.action_movie)
        self.toolbar.addAction(self.action_pause)

        position = PositionInfo(plot=self.plot, converters=[('Xpixel', lambda x, y: int(x)),
                                                            ('Ypixel', lambda x, y: int(y)),
                                                            ('Intensity', lambda x, y:
                                                            self.getActiveImage().getData()[int(y)][int(x)])])
        toolbar = QToolBar()
        toolbar.addWidget(position)
        self.getPlotWidget().addToolBar(Qt.BottomToolBarArea, toolbar)

    def title(self, image_index: int):
        return f"Image number {image_index} of the stack"

    def set_movie(self, images, flatfield):
        if images is not None:
            self.action_movie.set_movie_size(images.shape[0])
            self.action_use_flatfield.set_images(images)
            self.action_use_flatfield.set_flatfield(flatfield)

            self.setStack(images)
            self.setColormap("viridis", autoscale=True, normalization='log')

            self.action_pause.triggered.connect(self.update_pause_button)
            self.action_resume.triggered.connect(self.update_pause_button)
        else:
            self.setStack(None)

    def update_pause_button(self):
        if self.toolbar.actions()[-1] == self.action_pause:
            self.toolbar.removeAction(self.action_pause)
            self.toolbar.addAction(self.action_resume)
        else:
            self.toolbar.removeAction(self.action_resume)
            self.toolbar.addAction(self.action_pause)

    def get_action_movie(self):
        return self.action_movie

    def get_action_pause(self):
        return self.action_pause

    def get_action_resume(self):
        return self.action_resume

    def get_action_flatfield(self):
        return self.action_use_flatfield




