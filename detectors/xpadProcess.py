from PyQt5.QtWidgets import QPushButton, QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

class XpadVisualisation(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(400,300)

        # Add tabs
        self.tabs.addTab(self.tab1,"Raw data")
        self.tabs.addTab(self.tab2,"Unfolded data")
        self.tabs.addTab(self.tab3,"Fitted data")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
