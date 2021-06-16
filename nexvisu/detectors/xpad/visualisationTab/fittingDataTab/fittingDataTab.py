import statistics

import numpy
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.plot import Plot1D
from silx.math.fit import FitManager

from utils.fitAction import pearson7bg, estimate_pearson7

import matplotlib.pyplot as plt
from scipy.signal import find_peaks

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
        self.start_automatic_fit()

    def automatic_fit(self):
        if self._data_to_fit is not None:
            prominence = max(self._data_to_fit[0][1][~numpy.isnan(self._data_to_fit[0][1])])
            print(prominence)
            peaks, _ = find_peaks(self._data_to_fit[0][1], prominence=prominence/3.0)
            plt.plot(peaks, self._data_to_fit[0][1][peaks], "xr")
            plt.plot(self._data_to_fit[0][1])
            plt.legend(['Test detection with prominence'])
            plt.show()

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
            # copy the data arrays, with all the values even the nan ones to keep the size
            # the copy is used to not erase data on arrays ploted in the last panel
            x = data[0].copy()
            y = data[1].copy()
            # get the max of the y array without any nan value (it would be the maximum)
            maximum = max(y[~numpy.isnan(y)])
            # current maximum / peak we are looking for (for the first iteration it will be the max)
            current_maximum = max(y[~numpy.isnan(y)])
            try:
                cpt_peak = 0
                print("Searching peak and fitting it...")
                # plot the original curve, were we are going to plot each fitted peak.
                self.automatic_plot.addCurve(x, y, "Data to fit")
                print("Max : ", maximum, " Current max : ", current_maximum)
                # this threshold means that we only want peaks that are at least at 1/4 distance in y axis of the max.
                while current_maximum > (maximum / 4.0):
                    peak = numpy.where(y == current_maximum)[0][0]
                    left = peak - 35 if peak - 35 > 0 else 0
                    right = peak + 35 if peak + 35 < len(x) else len(x) - 1
                    x_peak = x[left: right]
                    y_peak = y[left: right]
                    # set the data to fit, i.e only the peak without all the curve
                    self.fit.setdata(x=x_peak, y=y_peak)
                    # use the estimate function we made to make a first guess of the parameters of the function that will fit our peak.
                    self.fit.estimate()
                    # fit the function.
                    self.fit.runfit()
                    # draw the resulted function of the fit.
                    self.automatic_plot.addCurve(x_peak,
                                       pearson7bg(x_peak, *(param['fitresult'] for param in self.fit.fit_results)),
                                       f"Peak number {cpt_peak}"
                                       )
                    self._fitted_data.append(self.automatic_plot.getActiveCurve())

                    backgr = self.fit.fit_results[0]['fitresult']
                    fwhm = self.fit.fit_results[4]['fitresult']

                    # erase the peak to make it easier to found other peaks.
                    y[left: right] = statistics.mean(y[~numpy.isnan(y)])
                    current_maximum = max(y[~numpy.isnan(y)])
                    cpt_peak += 1
                    print("new current_max : ", current_maximum)

            except (numpy.linalg.LinAlgError, TypeError):
                print("Singular matrix error: fit is impossible with the given parameters")