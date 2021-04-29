from PyQt5.QtCore import pyqtSignal
from silx.gui.plot.actions import PlotAction


class UnfoldWithFlatfield(PlotAction):
    unfoldWithFlatfieldClicked = pyqtSignal()

    def __init__(self, plot, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='slice-cross',
                            text='Unfold raw data using flatfield too',
                            tooltip='This action will unfold every image using scripts and flatfield.',
                            triggered=self.start_unfolding,
                            parent=parent)

    def start_unfolding(self):
        self.unfoldWithFlatfieldClicked.emit()


class Unfold(PlotAction):
    unfoldClicked = pyqtSignal()

    def __init__(self, plot, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='slice-horizontal',
                            text='Unfold raw data using only script',
                            tooltip='This action will unfold every image using only scripts.',
                            triggered=self.start_unfolding,
                            parent=parent)

    def start_unfolding(self):
        self.unfoldClicked.emit()
