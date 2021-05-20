from pathlib import Path
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from silx.gui.plot.actions import PlotAction

from constants import SAVING_PATH

import numpy


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


class SaveAction(PlotAction):
    def __init__(self, plot, parent):
        PlotAction.__init__(self,
                            plot,
                            icon='clipboard',
                            text='save data',
                            tooltip='Saves unfolded data',
                            triggered=self.save_images,
                            parent=parent)
        self.parent=parent

    def save_images(self):
        saved = QMessageBox(QMessageBox.Question, 'Saving unfolded data ?',
                           "Do you want to save the unfolded images ?",
                           QMessageBox.Ok | QMessageBox.Cancel).exec_()
        if saved == QMessageBox.Ok:
            path = SAVING_PATH + "\\unfolded_data"
            for index, image in enumerate(self.parent.get_scatter_items()):
                self.save_unfolded_data(image, index, path)
                print(f"Saved unfolded image number {index} in {path} path")

    def save_unfolded_data(self, image: numpy.ndarray, index: int, path: str):
        Path(path).mkdir(parents=True, exist_ok=True)
        xyz_line = ""
        for i in range(len(image[0])):
            xyz_line += "" + str(image[0][i]) + " " + str(image[1][i]) + " " + str(image[2][i]) + "\n"

        xyz_log_filename = f"raw_{index}.txt"  # modifier cette valeur selon le découpage...
        with open(path + "/" + xyz_log_filename, "w") as saveFile:
            saveFile.write(xyz_line)