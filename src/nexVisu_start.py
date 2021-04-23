import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QTabWidget, QVBoxLayout, QComboBox, QLayout
from PyQt5.QtCore import Qt

from constants import Detectors
from detectors.xpad import xpad
from detectors import cirpad


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

        self.init_ui()
        
        self.show()

    def init_ui(self):
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
        for detector in Detectors:
            self.selectionButton.addItem(detector.value)
        self.selectionButton.currentTextChanged.connect(self.change_tab)
        self.table_widget = self.init_detector_ui()

        layout.addWidget(self.selectionButton)
        layout.addWidget(self.table_widget)
        widget.setLayout(layout)
        # Set the global widget in the window
        self.setCentralWidget(widget)

    def init_detector_ui(self) -> QTabWidget or None:
        if self.selectionButton.currentText() == Detectors.XPAD.value:
            return xpad.Xpad(self.application)
        if self.selectionButton.currentText() == Detectors.CIRPAD.value:
            return cirpad.CirpadContext()

    def change_tab(self) -> None:
        clear_tab(self.centralWidget().layout())
        self.table_widget = self.initDetectorUI()
        self.centralWidget().layout().addWidget(self.table_widget)


def clear_tab(layout: QLayout) -> None:
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


def application_instance():
    res = QApplication.instance()
    if not res:
        res = QApplication(sys.argv)
    return res


if __name__ == '__main__':
    app = application_instance()
    app.setStyleSheet("""
    QLineEdit {
        border: 2px solid gray; 
        border-radius: 10px; 
        padding: 0 8px; 
        background: lightblue; 
        selection-background-color: darkgray;
    }
    
    QTabWidget::pane {
        border-top: 2px solid #C2C7CB;
    }
    
    QTabWidget::tab-bar {
        left: 5px; /* move to the right by 5px */
    }

    /* Style the tab using the tab sub-control. Note that
    it reads QTabBar _not_ QTabWidget */
    QTabBar::tab {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                    stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                    stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
        border: 2px solid #C4C4C3;
        border-bottom-color: #C2C7CB; /* same as the pane color */
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        min-width: 8ex;
        padding: 2px;
    }

    QTabBar::tab:selected, QTabBar::tab:hover {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                    stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                    stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);
    }

    QTabBar::tab:selected {
        border-color: #9B9B9B;
        border-bottom-color: #C2C7CB; /* same as pane color */
    }
    
    QTabBar::tab:!selected {
        margin-top: 2px; /* make non-selected tabs look smaller */
    }
    
    /* make use of negative margins for overlapping tabs */
    QTabBar::tab:selected {
        /* expand/overlap to the left and right by 4px */
        margin-left: -4px;
        margin-right: -4px;
    }

    QTabBar::tab:first:selected {
        margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
    }
    
    QTabBar::tab:last:selected {
        margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
    }
    
    QTabBar::tab:only-one {
        margin: 0; /* if there is only one tab, we don't want overlapping margins */
    }""")
    Window = Window(app)
    sys.exit(app.exec_())
