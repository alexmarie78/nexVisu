from __future__ import division

import logging
import statistics

import numpy

from scipy.stats import linregress

from silx.gui.plot.actions.PlotToolAction import PlotToolAction
from silx.gui.plot import items
from silx.gui import qt
from silx.math.fit import FitManager

_logger = logging.getLogger(__name__)


def get_roi(plot):
    curve = plot.getActiveCurve()
    new_curve = None
    for roi in plot.getCurvesRoiWidget().getRois():
        if not roi == "ICR":
            new_curve = items.Curve()
            roi = plot.getCurvesRoiWidget().getRois()[roi]
            if curve is not None:
                x = []
                y = []
                for index, value in enumerate(curve[0]):
                    if roi.getFrom() <= value <= roi.getTo():
                        x.append(curve[0][index])
                        y.append(curve[1][index])
                new_curve.setData(x, y)
            else:
                new_curve = None
    if new_curve is not None:
        return new_curve
    else:
        return curve


class FitAction(PlotToolAction):
    """QAction to open a :class:`FitWidget` and set its data to the
    active curve if any, or to the first curve.
    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """

    def __init__(self, plot, parent=None):
        self.__item = None
        self.__activeCurveSynchroEnabled = False
        self.__range = 0, 1
        self.__rangeAutoUpdate = True
        self.__x, self.__y = None, None  # Data to fit
        self.__curveParams = {}  # Store curve parameters to use for fit result
        self.__legend = None

        super(FitAction, self).__init__(
            plot, icon='math-fit', text='Fit curve',
            tooltip='Open a fit dialog',
            parent=parent)

    def _createToolWindow(self):
        # import done here rather than at module level to avoid circular import
        # FitWidget -> BackgroundWidget -> PlotWindow -> actions -> fit -> FitWidget
        from silx.gui.fit.FitWidget import FitWidget
        from silx.math.fit import fittheories

        fit = FitManager()
        fit.loadtheories(fittheories)
        fit.addtheory("pearson7", function=pearson7bg,
                      parameters=["backgr", "slopeline",
                                  "amplitude", "center",
                                  "fwhm", "exposant"],
                      estimate=estimate_pearson7)

        window = FitWidget(parent=self.plot, fitmngr=fit)
        window.setWindowFlags(qt.Qt.Dialog)
        window.sigFitWidgetSignal.connect(self.handle_signal)

        return window

    def _connectPlot(self, window):
        if self.is_x_range_updated_on_zoom():
            self.__set_auto_x_range_enabled(True)
        else:
            plot = self.plot
            if plot is None:
                _logger.error("No associated PlotWidget")
                return
            self._set_x_range(*plot.getXAxis().getLimits())

        if self.isFittedItemUpdatedFromActiveCurve():
            self.__set_fitted_item_auto_update_enabled(True)
        else:
            # Wait for the next iteration, else the plot is not yet initialized
            # No curve available
            qt.QTimer.singleShot(10, self._initFit)

    def _disconnectPlot(self, window):
        if self.is_x_range_updated_on_zoom():
            self.__set_auto_x_range_enabled(False)

        if self.isFittedItemUpdatedFromActiveCurve():
            self.__set_fitted_item_auto_update_enabled(False)

    def _initFit(self):
        plot = self.plot
        if plot is None:
            _logger.error("No associated PlotWidget")
            return

        item = get_roi(plot)

        self._set_x_range(*plot.getXAxis().getLimits())
        self._set_fitted_item(item)
        self.set_x_range_updated_on_zoom(False)

    def __updateFitWidget(self):
        """Update the data/range used by the FitWidget"""
        fit_widget = self._getToolWindow()

        item = self._get_fitted_item()
        xdata = self.getXData(copy=False)
        ydata = self.getYData(copy=False)

        if item is None or xdata is None or ydata is None:
            fit_widget.setData(y=None)
            fit_widget.setWindowTitle("No curve selected")

        else:
            xmin, xmax = self.getXRange()
            fit_widget.setData(
                xdata, ydata, xmin=xmin, xmax=xmax)
            fit_widget.setWindowTitle(
                "Fitting " + item.getName() +
                " on x range %f-%f" % (xmin, xmax))

    # X Range management

    def getXRange(self):
        """Returns the range on the X axis on which to perform the fit."""
        return self.__range

    def _set_x_range(self, xmin, xmax):
        """Set the range on which the fit is done.
        :param float xmin:
        :param float xmax:
        """
        range_ = float(xmin), float(xmax)
        if self.__range != range_:
            self.__range = range_
            self.__updateFitWidget()

    def __set_auto_x_range_enabled(self, enabled):
        """Implement the change of update mode of the X range.
        :param bool enabled:
        """
        plot = self.plot
        if plot is None:
            _logger.error("No associated PlotWidget")
            return

        if enabled:
            self._set_x_range(*plot.getXAxis().getLimits())
            plot.getXAxis().sigLimitsChanged.connect(self._set_x_range)
        else:
            plot.getXAxis().sigLimitsChanged.disconnect(self._set_x_range)

    def set_x_range_updated_on_zoom(self, enabled):
        """Set whether or not to update the X range on zoom change.
        :param bool enabled:
        """
        if enabled != self.__rangeAutoUpdate:
            self.__rangeAutoUpdate = enabled
            if self._getToolWindow().isVisible():
                self.__set_auto_x_range_enabled(enabled)

    def is_x_range_updated_on_zoom(self):
        """Returns the current mode of fitted data X range update.
        :rtype: bool
        """
        return self.__rangeAutoUpdate

    # Fitted item update

    def getXData(self, copy=True):
        """Returns the X data used for the fit or None if undefined.
        :param bool copy:
            True to get a copy of the data, False to get the internal data.
        :rtype: Union[numpy.ndarray,None]
        """
        return None if self.__x is None else numpy.array(self.__x, copy=copy)

    def getYData(self, copy=True):
        """Returns the Y data used for the fit or None if undefined.
        :param bool copy:
            True to get a copy of the data, False to get the internal data.
        :rtype: Union[numpy.ndarray,None]
        """
        return None if self.__y is None else numpy.array(self.__y, copy=copy)

    def _get_fitted_item(self):
        """Returns the current item used for the fit
        :rtype: Union[~silx.gui.plot.items.Curve,~silx.gui.plot.items.Histogram,None]
        """
        return self.__item

    def _set_fitted_item(self, item):
        """Set the curve to use for fitting.
        :param Union[~silx.gui.plot.items.Curve,~silx.gui.plot.items.Histogram,None] item:
        """
        plot = self.plot
        if plot is None:
            _logger.error("No associated PlotWidget")

        if plot is None or item is None:
            self.__item = None
            self.__curveParams = {}
            self.__updateFitWidget()
            return

        axis = item.getYAxis() if isinstance(item, items.YAxisMixIn) else 'left'
        self.__curveParams = {
            'yaxis': axis,
            'xlabel': plot.getXAxis().getLabel(),
            'ylabel': plot.getYAxis(axis).getLabel(),
        }
        self.__legend = item.getName()

        if isinstance(item, items.Histogram):
            bin_edges = item.getBinEdgesData(copy=False)
            # take the middle coordinate between adjacent bin edges
            self.__x = (bin_edges[1:] + bin_edges[:-1]) / 2
            self.__y = item.getValueData(copy=False)
        # else take the active curve, or else the unique curve
        elif isinstance(item, items.Curve):
            self.__x = item.getXData(copy=False)
            self.__y = item.getYData(copy=False)

        self.__item = item

        self.__updateFitWidget()

    def __active_curve_changed(self, previous, current):
        """Handle change of active curve in the PlotWidget
        """
        if current is None:
            self._set_fitted_item(None)
        else:
            item = get_roi(self.plot)
            self._set_fitted_item(item)

    def __set_fitted_item_auto_update_enabled(self, enabled):
        """Implement the change of fitted item update mode
        :param bool enabled:
        """
        plot = self.plot
        if plot is None:
            _logger.error("No associated PlotWidget")
            return

        if enabled:
            item = get_roi(self.plot)
            self._set_fitted_item(item)
            plot.sigActiveCurveChanged.connect(self.__active_curve_changed)

        else:
            plot.sigActiveCurveChanged.disconnect(
                self.__active_curve_changed)

    def set_fitted_item_updated_from_active_curve(self, enabled):
        """Toggle fitted data synchronization with plot active curve.
        :param bool enabled:
        """
        enabled = bool(enabled)
        if enabled != self.__activeCurveSynchroEnabled:
            self.__activeCurveSynchroEnabled = enabled
            if self._getToolWindow().isVisible():
                self.__set_fitted_item_auto_update_enabled(enabled)

    def isFittedItemUpdatedFromActiveCurve(self):
        """Returns True if fitted data is synchronized with plot.
        :rtype: bool
        """
        return self.__activeCurveSynchroEnabled

    # Handle fit completed

    def handle_signal(self, ddict):
        xdata = self.getXData(copy=False)
        if xdata is None:
            _logger.error("No reference data to display fit result for")
            return

        xmin, xmax = self.getXRange()
        x_fit = xdata[xmin <= xdata]
        x_fit = x_fit[x_fit <= xmax]
        fit_legend = "Fit <%s>" % self.__legend
        fit_curve = self.plot.getCurve(fit_legend)

        if ddict["event"] == "FitFinished":
            fit_widget = self._getToolWindow()
            if fit_widget is None:
                return
            y_fit = fit_widget.fitmanager.gendata()
            if fit_curve is None:
                self.plot.addCurve(x_fit, y_fit,
                                   fit_legend,
                                   resetzoom=False,
                                   **self.__curveParams)
            else:
                fit_curve.setData(x_fit, y_fit)
                fit_curve.setVisible(True)
                fit_curve.setYAxis(self.__curveParams.get('yaxis', 'left'))

        if ddict["event"] in ["FitStarted", "FitFailed"]:
            if fit_curve is not None:
                fit_curve.setVisible(False)


def pearson7bg(x, backgr, slopeline, amplitude, center, fwhmlike, exposant):
    print(x, backgr, slopeline, amplitude, center, fwhmlike, exposant)
    return backgr + slopeline * x + amplitude * (1 + ((x-center) / fwhmlike) ** 2.0) ** (-exposant)


def estimate_pearson7(x, y):
    backgr = statistics.mean(y[:5] + y[-5:])
    slopeline, _, _, _, _ = linregress(x, y)
    amplitude = max(y) - backgr
    center = x[numpy.argmax(y)]
    upper_points = [index for index in range(len(x)) if y[index] > max(y)/2.0]
    fwhm = []

    for i in range(1, len(upper_points)):
        if upper_points[i] - upper_points[i - 1] > 10:
            fwhm.append(x[upper_points[i - 1]])
            break
        fwhm.append(x[upper_points[i - 1]])

    fwhm = fwhm[-1] - fwhm[0]
    exposant = 2.0

    # params = [1.95029979e+04, -2.60909223e+03, 3.52252164e+02, 1.33957258e+01, 1.69597427e-01, 1.90484157e+00]
    params = numpy.array([backgr, slopeline, amplitude, center, fwhm, exposant])
    constraints = numpy.zeros(shape=(len(params), 3))
    return params, constraints
