import numpy
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.plot import Plot1D
from silx.math.fit import FitManager

from utils.fitAction import pearson7bg, estimate_pearson7


class FittingDataTab(QWidget):
    def __init__(self, parent, data_to_fit=None):
        super().__init__(parent)
        self._data_to_fit = data_to_fit
        self._fitted_data = []
        self.layout = QVBoxLayout(self)
        self.plot = Plot1D(self)
        self.fitting_data_selector = NumpyAxesSelector(self)
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
        self.layout.addWidget(self.fitting_data_selector)

        self.fitting_data_selector.setNamedAxesSelectorVisibility(False)
        self.fitting_data_selector.setVisible(True)
        self.fitting_data_selector.setAxisNames("12")
        self.fitting_data_selector.selectionChanged.connect(self.plot_fit)

    def set_data_to_fit(self, data_to_fit):
        self._data_to_fit = data_to_fit
        self.fitting_data_selector.setData(numpy.zeros((len(data_to_fit), 1, 1)))
        #self.start_fitting()

    def plot_fit(self):
        if len(self._fitted_data) > 0:
            self.plot.addCurve(self._data_to_fit[self.fitting_data_selector.selection()[0]][0],
                               self._data_to_fit[self.fitting_data_selector.selection()[0]][1],
                               'Data to fit')
            self.plot.addCurve(self._fitted_data[self.fitting_data_selector.selection()[0]][0],
                               self._fitted_data[self.fitting_data_selector.selection()[0]][1],
                               'Fitted data')

    def start_fitting(self):
        self.fit.addtheory("pearson7", function=pearson7bg,
                           parameters=['backgr', 'slopeLin',
                                       'amplitude', 'center',
                                       'fwhm', 'exposant'
                                       ],
                           estimate=estimate_pearson7)
        self.fit.settheory("pearson7")
        print("Start fitting...")
        maximums = []
        for data in self._data_to_fit:
            # x = data[0][~numpy.isnan(data[0])]
            # y = data[1][~numpy.isnan(data[1])]
            x = data[0]
            y = data[1]
            maximums.append(max(y))
            try:
                print("Searching peak and fitting it...")
                while maximum > (maximums[0] / 2.0):
                    print('\n\n', first_maximum, maximum, '\n\n')
                    peak = numpy.where(y == maximum)[0][0]
                    print("Peak : ", peak)
                    left = peak - 800 if peak - 800 > 0 else 0
                    right = peak + 800 if peak + 800 < len(x) else len(x) - 1
                    print("Peak around : ", x[left], x[right])
                    x_peak = x[left: right]
                    y_peak = y[left: right]
                    self.plot.addCurve(data[0], data[1], "Data to fit")
                    self.fit.setdata(x=x_peak, y=y_peak)
                    self.fit.estimate()
                    # backgr, slopeLin, amplitude, center, fwhmLike, exposant = (param['fitresult'] for param in self.fit.fit_results)
                    self.fit.runfit()

                    self.plot.addCurve(x_peak, pearson7bg(x_peak, *(param['fitresult'] for param in self.fit.fit_results)),
                                       "Fitted data"
                                       )
                    self._fitted_data.append(self.plot.getActiveCurve())

                    x = numpy.concatenate([x[:left], x[right:]])
                    y = numpy.concatenate([y[:left], y[right:]])
                    maximum = max(y)
            except (numpy.linalg.LinAlgError, TypeError):
                print("Singular matrix error")

