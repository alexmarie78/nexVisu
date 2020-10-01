import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTabWidget, QVBoxLayout, QComboBox, QLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRect, Qt

from constants import detectors
from detectors import xpad, cirpad

class Window(QMainWindow):

    def __init__(self, application):
        super().__init__()
        self.application = application
        self.screenSize = application.desktop().screenGeometry()
        self.title = 'Nexus visualisation'
        self.left = 0
        self.top = 0
        self.width = self.screenSize.width()
        self.height = self.screenSize.height()

        self.initUI()
        
        self.show()

    def initUI(self):
        # Set the title and the geometry for the window
        self.setWindowTitle(self.title)
        self.setGeometry((self.width - self.screenSize.width())//2,
                         (self.height - self.screenSize.height())//2,
                         self.width, self.height)

        # Create the widget that will contain the button selection and the tabs
        widget = QWidget()
        layout = QVBoxLayout()
        self.selectionButton = QComboBox(self)
        # Let the software edit the text in the button
        self.selectionButton.setEditable(True)
        # Prevent user from rewrite the names of the detector
        self.selectionButton.lineEdit().setReadOnly(True)
        # Align the text
        self.selectionButton.lineEdit().setAlignment(Qt.AlignCenter)
        # Populate the selection button with the detectors' name
        for detector in detectors:
            self.selectionButton.addItem(detector.value)
        self.selectionButton.currentTextChanged.connect(self.changeTab)
        self.table_widget = self.initDetectorUI()

        layout.addWidget(self.selectionButton)
        layout.addWidget(self.table_widget)
        widget.setLayout(layout)
        # Set the global widget in the window
        self.setCentralWidget(widget)

    def initDetectorUI(self) -> QTabWidget or None:
        if self.selectionButton.currentText() == detectors.XPAD.value:
            return xpad.XpadContext(self.application)
        if self.selectionButton.currentText() == detectors.CIRPAD.value:
            return cirpad.CirpadContext()

    def changeTab(self) -> None:
        self.clearTab(self.centralWidget().layout())
        self.table_widget = self.initDetectorUI()
        self.centralWidget().layout().addWidget(self.table_widget)
        
    def clearTab(self, layout: QLayout) -> None:
        """Delete all the objects, i.e the widgets that are non essential to the gui when
        changing the mode in order to make the change faster"""

        # while layout.count():
        # We get the widget at the second place in the main layout, i.e the tabs
        child = layout.takeAt(1)
        if child.widget() is not None:
            child.widget().deleteLater()
        # elif child.layout() is not None:
        #     # Prevent the function from removing the layout that is in every mode
        #     if child.layout() not in self.unvariant_layouts:
        #         self.clearLayout(child.layout())


def applicationInstance():
    res = QApplication.instance()
    if not res:
        res = QApplication(sys.argv)
    return res

if __name__ == '__main__':
    app = applicationInstance()
    Window = Window(app)
    sys.exit(app.exec_())
