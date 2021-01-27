from PyQt5.QtWidgets import QLabel, QPushButton, QGroupBox, QLineEdit, QWidget, QScrollArea, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal


class LabelledInputWidget(QWidget):
    labelFilled = pyqtSignal()

    def __init__(self, parent, label: str):
        super().__init__(parent=parent)
        # self.setFixedSize(parent.size().width(), parent.size().height())
        self.layout = QHBoxLayout(self)

        self.label = QLabel(label)

        self.button = QPushButton("+")

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(2)

        self.inner_widget = QWidget(self.scrollArea)
        self.inner_widget.setLayout(QVBoxLayout())

        self.scrollArea.setWidget(self.inner_widget)

        self.scrollArea.setFixedHeight(self.button.sizeHint().width())

        self.button.clicked.connect(self.add_row)
        self.init_ui()

    def init_ui(self):
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.scrollArea)
        self.layout.addWidget(self.button)

        self.button.clicked.emit()

    def add_row(self):
        if self.inner_widget.layout().count() < 10:
            input_line = QLineEdit()
            input_line.editingFinished.connect(self.label_filled)
            self.inner_widget.layout().addWidget(input_line)

    def label_filled(self):
        self.labelFilled.emit()

    def input_number(self):
        return self.inner_widget.layout().count()

    def get_label_at(self, index: int):
        return self.inner_widget.layout().itemAt(index).widget().text()
