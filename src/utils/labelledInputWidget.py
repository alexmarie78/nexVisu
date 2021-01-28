from PyQt5.QtWidgets import QLabel, QPushButton, QGroupBox, QLineEdit, QWidget, QScrollArea, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal


class LabelledInputWidget(QWidget):
    labelFilled = pyqtSignal()

    def __init__(self, parent, label: str, button_flag=True):
        super().__init__(parent=parent)
        self.layout = QHBoxLayout(self)

        self.button_flag = button_flag

        self.label = QLabel(label)
        if self.button_flag:
            self.button = QPushButton("+")
            self.button.clicked.connect(self.add_row)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(2)

        self.inner_widget = QWidget(self.scrollArea)
        self.inner_widget.setLayout(QVBoxLayout())

        self.scrollArea.setWidget(self.inner_widget)

        if self.button_flag:
            self.scrollArea.setFixedHeight(self.button.sizeHint().width())
        else:
            self.scrollArea.setFixedHeight(self.label.sizeHint().width())

        self.init_ui()

    def init_ui(self):
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.scrollArea)
        if self.button_flag:
            self.layout.addWidget(self.button)
            self.button.clicked.emit()
        else:
            self.add_row()
            self.labelFilled.emit()

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
