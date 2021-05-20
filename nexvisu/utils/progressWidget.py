from PyQt5.QtWidgets import QProgressBar, QDialog


class ProgressWidget(QDialog):
    def __init__(self, name: str, nb_elements: int, parent=None):
        super().__init__(parent=parent)
        self.name = name
        self.maximum = nb_elements
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.name)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(0, 0, 300, 25)
        self.progress.setMaximum(self.maximum - 1)
        self.show()

    def increase_progress(self, value=1):
        self.progress.setValue(self.progress.value() + value)
