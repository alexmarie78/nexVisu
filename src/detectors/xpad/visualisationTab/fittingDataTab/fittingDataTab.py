import numpy
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from silx.gui.plot import Plot1D
from silx.math.fit import FitManager

from src.utils.fitAction import pearson7bg, estimate_pearson7


class FittingDataTab(QWidget):
    def __init__(self, parent, data_to_fit=None):
        super().__init__(parent)
        self._data_to_fit = data_to_fit
        self.layout = QVBoxLayout(self)
        self.plot = Plot1D(self)
        self.fit = FitManager()

        """
        self.fitting_widget = self.fitting_data_plot.getFitAction()
        self.fit_action = FitAction(plot=self.fitting_data_plot, parent=self.fitting_data_plot)
        self.toolbar = QToolBar("New")
        """

        self.init_ui()

    def init_ui(self):
        self.setLayout(self.layout)
        self.layout.addWidget(self.plot)

    def set_data_to_fit(self, data_to_fit):
        self._data_to_fit = data_to_fit
        self.start_fitting()

    def start_fitting(self):
        self.fit.addtheory("pearson7", function=pearson7bg,
                           parameters=['backgr', 'slopeLin',
                                       'amplitude', 'center',
                                       'fwhmLike', 'exposant'
                                       ],
                           estimate=estimate_pearson7)
        self.fit.settheory("pearson7")
        for data in self._data_to_fit:
            try:
                self.plot.addCurve(data[0], data[1], "Data to fit")
                self.fit.setdata(x=data[0], y=data[1])
                self.fit.estimate()
                print("Estimated")
                # backgr, slopeLin, amplitude, center, fwhmLike, exposant = (param['fitresult'] for param in self.fit.fit_results)
                self.fit.runfit()
                print('Fitted')
                self.plot.addCurve(data[0],
                                   pearson7bg(data[0], *(param['fitresult'] for param in self.fit.fit_results)),
                                   "Fitted data"
                                   )
                print("Fitted curve added to plot")
            except numpy.linalg.LinAlgError:
                print("Singular matrix error")

