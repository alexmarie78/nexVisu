import statistics

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
        self.automatic_plot = Plot1D(self)
        self.fitting_data_selector = NumpyAxesSelector(self)
        self.fit = FitManager()

        self.fit.addtheory("pearson7", function=pearson7bg,
                           parameters=['backgr', 'slopeLin',
                                       'amplitude', 'center',
                                       'fwhm', 'exposant'
                                       ],
                           estimate=estimate_pearson7)

        """
        self.fitting_widget = self.fitting_data_plot.getFitAction()
        self.fit_action = FitAction(plot=self.fitting_data_plot, parent=self.fitting_data_plot)
        self.toolbar = QToolBar("New")
        """

        self.init_ui()

    def init_ui(self):
        self.setLayout(self.layout)
        self.layout.addWidget(self.automatic_plot)
        self.layout.addWidget(self.fitting_data_selector)

        self.fitting_data_selector.setNamedAxesSelectorVisibility(False)
        self.fitting_data_selector.setVisible(True)
        self.fitting_data_selector.setAxisNames("12")
        # self.fitting_data_selector.selectionChanged.connect(self.automatic_plot_fit)

    def set_data_to_fit(self, data_to_fit):
        self._data_to_fit = data_to_fit
        self.fitting_data_selector.setData(numpy.zeros((len(data_to_fit), 1, 1)))
        #self.start_automatic_fit()

    def plot_fit(self):
        if len(self._fitted_data) > 0 and len(self._data_to_fit) > 0:
            self.automatic_plot.addCurve(self._data_to_fit[self.fitting_data_selector.selection()[0]][0],
                               self._data_to_fit[self.fitting_data_selector.selection()[0]][1],
                               'Data to fit')
            self.automatic_plot.addCurve(self._fitted_data[self.fitting_data_selector.selection()[0]][0],
                               self._fitted_data[self.fitting_data_selector.selection()[0]][1],
                               'Fitted data')

    def start_automatic_fit(self):
        self.fit.settheory("pearson7")
        print("Start fitting...")
        for data in self._data_to_fit:
            # x = data[0][~numpy.isnan(data[0])]
            # y = data[1][~numpy.isnan(data[1])]
            x = data[0]
            y = data[1]
            print(y)
            maximum = max(y[~numpy.isnan(y)])
            maximums = [index for index in range(len(x)) if y[index] > max(y[~numpy.isnan(y)]) / 4.0]
            current_maximum = max(y[~numpy.isnan(y)])
            try:
                cpt_peak = 0
                print("Searching peak and fitting it...")
                self.automatic_plot.addCurve(x, y, "Data to fit")
                print("Max : ", maximum, " Current max : ", current_maximum)
                # for index, maximum in enumerate(maximums):
                while current_maximum > (maximum / 4.0):
                    print('\n\n', maximum, current_maximum, '\n\n')
                    peak = numpy.where(y == current_maximum)[0][0]
                    left = peak - 100 if peak - 100 > 0 else 0
                    right = peak + 100 if peak + 100 < len(x) else len(x) - 1
                    x_peak = x[left: right]
                    y_peak = y[left: right]
                    self.fit.setdata(x=x_peak, y=y_peak)
                    self.fit.estimate()
                    # backgr, slopeLin, amplitude, center, fwhmLike,
                    # exposant = (param['fitresult'] for param in self.fit.fit_results)
                    self.fit.runfit()
                    self.automatic_plot.addCurve(x_peak,
                                       pearson7bg(x_peak, *(param['fitresult'] for param in self.fit.fit_results)),
                                       f"Peak number {cpt_peak}"
                                       )
                    self._fitted_data.append(self.automatic_plot.getActiveCurve())

                    # x = numpy.concatenate([x[:left], x[left:right] , x[right:]])
                    backgr = self.fit.fit_results[0]['fitresult']
                    y[left: right] = statistics.mean(y[~numpy.isnan(y)])
                    current_maximum = max(y[~numpy.isnan(y)])
                    cpt_peak += 1
                    print("new current_max : ", current_maximum)
            except (numpy.linalg.LinAlgError, TypeError):
                print("Singular matrix error: fit is impossible with the given parameters")