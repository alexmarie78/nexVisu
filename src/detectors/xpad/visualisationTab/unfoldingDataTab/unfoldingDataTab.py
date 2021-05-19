from pathlib import Path

import numpy
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QInputDialog, QMessageBox
from detectors.xpad.visualisationTab.unfoldingDataTab.unfoldingViewer import UnfoldedDataViewer
from utils.imageProcessing import compute_geometry, correct_and_unfold_data, extract_diffraction_diagram, get_angles
from utils.progressWidget import ProgressWidget


class UnfoldingDataTab(QWidget):
    unfoldingFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout(self)
        self.viewer = UnfoldedDataViewer(self)

        self.timer = QTimer(self, interval=1)

        self.geometry = {}
        self.calibration = {}

        self.flatfield = None
        self.images = None

        self.scatter_factor = 0

        self.median_filter = False
        self.save_data = False

        self.delta_array = []
        self.gamma_array = []

        self.path = None

        self.is_unfolding = False

        self.data_iterator = None
        self.index_iterator = None
        self.progress = None

        self.use_flatfield = True

        self.init_ui()

    def init_ui(self):
        self.layout.addWidget(self.viewer)
        self.timer.timeout.connect(self.unfold_data)

        self.viewer.get_unfold_action().unfoldClicked.connect(self.remove_flatfield)
        self.viewer.get_unfold_with_flatfield_action().unfoldWithFlatfieldClicked.connect(self.add_flatfield)

    def start_unfolding(self):
        self.viewer.reset_scatter_view()
        if self.is_unfolding:
            self.reset_unfolding()

        self.scatter_factor, validate_button = QInputDialog.getInt(self, "You ran unfolding data process",
                                                                   "Choose a factor to speed the scatter",
                                                                   QLineEdit.Normal)

        if not isinstance(self.scatter_factor, int):
            self.reset_unfolding()
            QMessageBox(QMessageBox.Icon.Critical, "Can't send contextual data",
                        "You must enter a integer (whole number) to run the unfolding of data").exec()
        elif not validate_button:
            self.reset_unfolding()
            print("Dialog killed, unfolding stopped")
        else:
            if self.scatter_factor <= 0:
                self.scatter_factor = 1
            # Create geometry of the detector
            self.median_filter = self.calibration["median_filter"]
            self.save_data = self.calibration["save_data"]
            if self.use_flatfield:
                self.geometry = compute_geometry(self.calibration, self.flatfield, self.images)
            else:
                self.geometry = compute_geometry(self.calibration, None, self.images)
            # Collect the angles
            self.delta_array, self.gamma_array = get_angles(self.path)

            # Populate the iterators that will help running the unfolding of data
            self.data_iterator = iter([image for image in self.images])
            self.index_iterator = iter([i for i in range(self.images.shape[0])])
            self.progress = ProgressWidget('Unfolding data', self.images.shape[0])
            # Start the timer and the unfolding
            self.timer.start()
            self.is_unfolding = True

    def unfold_data(self):
        try:
            image = next(self.data_iterator)
            index = next(self.index_iterator)
            delta = self.delta_array[index] if len(self.delta_array) > 1 else self.delta_array[0]
            gamma = self.gamma_array[index] if len(self.gamma_array) > 1 else self.gamma_array[0]
            # Correct and unfold raw data
            unfolded_data = correct_and_unfold_data(self.geometry, image, delta, gamma, self.median_filter)

            # Add the unfolded image to the scatter stack of image.
            self.viewer.add_scatter(unfolded_data, self.scatter_factor)
            if self.save_data:
                self.save_unfolded_data(unfolded_data, index, "../saved_data")
                print(f"Saved unfolded image number {index} of {self.path} scan in '../saved_data' path")
            self.progress.increase_progress()

        except StopIteration:
            self.timer.stop()
            self.is_unfolding = False
            self.progress.deleteLater()
            self.progress = None
            self.unfoldingFinished.emit()

    def reset_unfolding(self):
        self.is_unfolding = False
        self.timer.stop()

    def save_unfolded_data(self, image: numpy.ndarray, index: int, path: str):
        Path(path).mkdir(parents=True, exist_ok=True)
        xyz_line = ""
        for i in range(len(image[0])):
            xyz_line += ""+str(image[0][i])+" "+str(image[1][i])+" "+str(image[2][i])+"\n"

        xyz_log_filename = f"raw_{index}.txt"  # modifier cette valeur selon le découpage...
        with open(path + "/" + xyz_log_filename, "w") as saveFile:
            saveFile.write(xyz_line)

        """
        image = numpy.asarray((image[0], image[1])) #image[2]))
        im = Image.fromarray(image)
        im = im.convert('RGB')
        im.save(path + f"/image_{index}.png", "PNG")
        """

    def remove_flatfield(self):
        self.use_flatfield = False

    def add_flatfield(self):
        self.use_flatfield = True
