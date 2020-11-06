from .xpadContext import DataContext
from .xpadProcess import XpadVisualisation
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QApplication
from PyQt5.QtCore import pyqtSlot, pyqtSignal

import numpy
import os
import platform
import sys


class Xpad(QWidget):

    def __init__(self, application: QApplication):
        super(QWidget, self).__init__()
        self.application = application
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(400, 300)

        # Add tabs
        self.tabs.addTab(self.tab1, "Initial Data")
        self.tabs.addTab(self.tab2, "Visualisation and processing")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.data_context = DataContext(self.application)
        self.tab1.layout.addWidget(self.data_context)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self.tab2)
        self.xpad_visualisation = XpadVisualisation()
        self.tab2.layout.addWidget(self.xpad_visualisation)

        self.data_context.experimental_data_tab.scanLabelChanged.connect(self.xpad_visualisation.set_data)
        self.data_context.experimental_data_tab.contextualDataEntered.connect(self.xpad_visualisation.start_unfolding_raw_data)
        self.data_context.flatfield_tab.usingFlat.connect(self.send_flatfield_image)
        self.data_context.flatfield_tab.notUsingFlat.connect(self.send_empty_flatfield)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

    def send_flatfield_image(self) -> None:
        self.xpad_visualisation.get_flatfield(self.data_context.flatfield_tab.send_flatfield())

    def send_empty_flatfield(self) -> None:
        self.xpad_visualisation.get_flatfield(None)


