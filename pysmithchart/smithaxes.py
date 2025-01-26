"""
Library for producing Smith Chart.

It also provides the following modifications and features:

    - circle shaped drawing area with labels placed around
    - :meth:`plot` accepts single real/complex numbers or numpy.ndarray
    - plotted lines can be interpolated
    - start/end markers of lines can be modified and rotate tangential
    - gridlines are 3-point arcs to improve space efficiency of exported plots
    - 'fancy' option for adaptive grid generation
    - own tick locators for nice axis labels

For making a Smith Chart, it is sufficient to import :mod:`smithplot` and
create a new subplot with projection set to 'smith'. Parameters can be set
either with keyword arguments or :meth:`update_Params`.

Example:
    >>> from matplotlib import pyplot as plt
    >>> from pysmithchart import Z_PARAMETER
    >>> plt.subplot(1, 1, 1, projection='smith', grid_minor_enable=True)
    >>> plt.plot([25, 50 + 50j, 100 - 50j], datatype=Z_PARAMETER)
    >>> plt.show()

Note: Supplying parameters to :meth:`subplot` may not always work as
expected, because subplot uses an index for the axes with a key created
of all given parameters. This does not work always, especially if the
parameters are array-like types (e.g. numpy.ndarray).
"""

import copy
from enum import Enum
from collections.abc import Iterable
from numbers import Number
from types import MethodType

import matplotlib as mp
import numpy as np

from matplotlib.axes import Axes
from matplotlib.cbook import simple_linear_interpolation as linear_interpolation
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Circle, Arc
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.ticker import Formatter, AutoMinorLocator, Locator
from matplotlib.transforms import Affine2D, BboxTransformTo, Transform
from scipy.interpolate import splprep, splev
from . import smithhelper
from .smithhelper import EPSILON, TWO_PI, ang_to_c, z_to_xy


class ParameterType(Enum):
    """Defines parameter types for use with Smith charts."""

    S_PARAMETER = "S"
    Z_PARAMETER = "Z"
    Y_PARAMETER = "Y"


S_PARAMETER = ParameterType.S_PARAMETER
Z_PARAMETER = ParameterType.Z_PARAMETER
Y_PARAMETER = ParameterType.Y_PARAMETER


class SmithAxes(Axes):
    """
    An implementation of :class:`matplotlib.axes.Axes` for Smith charts.

    The :class:`SmithAxes` provides an implementation of :class:`matplotlib.axes.Axes`
    for drawing a full automatic Smith Chart it also provides own implementations for

        - :class:`matplotlib.transforms.Transform`
            -> :class:`MoebiusTransform`
            -> :class:`InvertedMoebiusTransform`
            -> :class:`PolarTranslate`
        - :class:`matplotlib.ticker.Locator`
            -> :class:`RealMaxNLocator`
            -> :class:`ImagMaxNLocator`
            -> :class:`SmithAutoMinorLocator`
        - :class:`matplotlib.ticker.Formatter`
            -> :class:`RealFormatter`
            -> :class:`ImagFormatter`

        Method for updating the parameters of a SmithAxes instance. If no instance
        is given, the changes are global, but affect only instances created
        afterwards. Parameter can be passed as dictionary or keyword arguments.
        If passed as keyword, the separator '.' must be  replaced with '_'.

        Note: Parameter changes are not always immediate (e.g. changes to the
        grid). It is not recommended to modify parameter after adding anything to
        the plot. For a reset call :meth:`clear`.

    Example:
            update_scParams({grid.major: True})
            update_scParams(grid_major=True)

        Valid parameters with default values and description:

        plot.zorder: 5
            Zorder of plotted lines.
            Accepts: integer

        plot.marker.hack: True
            Enables the replacement of start and endmarkers.
            Accepts: boolean
            Note: Uses ugly code injection and may causes unexpected behavior.

        plot.marker.rotate: True
            Rotates the endmarker in the direction of its line.
            Accepts: boolean
            Note: needs plot.marker.hack=True

        plot.marker.start: 's',
            Marker for the first point of a line, if it has more than 1 point.
            Accepts: None or see matplotlib.markers.MarkerStyle()
            Note: needs plot.marker.hack=True

        plot.marker.default: 'o'
            Marker used for linepoints.
            Accepts: None or see matplotlib.markers.MarkerStyle()

        plot.marker.end: '^',
            Marker for the last point of a line, if it has more than 1 point.
            Accepts: None or see matplotlib.markers.MarkerStyle()
            Note: needs plot.marker.hack=True

        plot.default.interpolation: 5
            Default number of interpolated steps between two points of a
            line, if interpolation is used.
            Accepts: integer

        plot.default.datatype: S_PARAMETER
            Default datatype for plots.
            Accepts: SmithAxes.[S_PARAMETER,Z_PARAMETER,Y_PARAMETER]

        grid.zorder : 1
            Zorder of the gridlines.
            Accepts: integer
            Note: may not work as expected

        grid.locator.precision: 2
            Sets the number of significant decimals per decade for the
            Real and Imag MaxNLocators. Example with precision 2:
                1.12 -> 1.1, 22.5 -> 22, 135 -> 130, ...
            Accepts: integer
            Note: value is an orientation, several exceptions are implemented

        grid.major.enable: True
            Enables the major grid.
            Accepts: boolean

        grid.major.linestyle: 'solid'
            Major gridline style.
            Accepts: see matplotlib.patches.Patch.set_linestyle()

        grid.major.linewidth: 1
            Major gridline width.
            Accepts: float

        grid.major.color: '0.2'
            Major gridline color.
            Accepts: matplotlib color
            Note: changes both real x and imag y major grid lines.

        grid.major.color.x: '0.2'
            Major real gridline color
            Accepts: matplotlib color
            Note: Major real valued grid lines.

        grid.major.color.y: '0.2'
            Major imag gridline color
            Accepts: matplotlib color
            Note: Major imaginary valued grid lines.

        grid.major.xmaxn: 10
            Maximum number of spacing steps for the real axis.
            Accepts: integer

        grid.major.ymaxn: 16
            Maximum number of spacing steps for the imaginary axis.
            Accepts: integer

        grid.major.fancy: True
            Draws a fancy major grid instead of the standard one.
            Accepts: boolean

        grid.major.fancy.threshold: (100, 50)
            Minimum distance times 1000 between two gridlines relative to
            total plot size 2x2. Either tuple for individual real and
            imaginary distances or single value for both.
            Accepts: (float, float) or float

        grid.minor.enable: True
            Enables the minor grid.
            Accepts: boolean

        grid.minor.capstyle: 'round'
            Minor dashes capstyle
            Accepts: 'round', 'butt', 'miter', 'projecting'

        grid.minor.dashes: (0.2, 2)
            Minor gridline dash style.
            Accepts: tuple

        grid.minor.linewidth: 0.75
            Minor gridline width.
            Accepts: float

        grid.minor.color: 0.4
            Minor gridline color.
            Accepts: matplotlib color

        grid.minor.color.x: '0.2'
            Minor real gridline color
            Accepts: matplotlib color

        grid.minor.color.y: '0.2'
            Minor imag gridline color
            Accepts: matplotlib color

        grid.minor.xauto: 4
            Maximum number of spacing steps for the real axis.
            Accepts: integer

        grid.minor.yauto: 4
            Maximum number of spacing steps for the imaginary axis.
            Accepts: integer

        grid.minor.fancy: True
            Draws a fancy minor grid instead the standard one.
            Accepts: boolean

        grid.minor.fancy.dividers: [1, 2, 3, 5, 10, 20]
            Divisions for the fancy minor grid, which are selected by
            comparing the distance of gridlines with the threshold value.
            Accepts: list of integers

        grid.minor.fancy.threshold: 25
            Minimum distance for using the next bigger divider. Value times
            1000 relative to total plot size 2.
            Accepts: float

        axes.xlabel.rotation: 90
           Rotation of the real axis labels in degree.
           Accepts: float

        axes.xlabel.fancybox: {"boxstyle": "round4,pad=0.3,rounding_size=0.2",
                                           "facecolor": 'w',
                                           "edgecolor": "w",
                                           "mutation_aspect": 0.75,
                                           "alpha": 1},
            FancyBboxPatch parameters for the x-label background box.
            Accepts: dictionary with rectprops

        axes.ylabel.correction: (-1, 0, 0)
            Correction in x, y, and radial direction for the labels of the imaginary axis.
            Usually needs to be adapted when fontsize changes 'font.size'.
            Accepts: (float, float, float)

        axes.radius: 0.44
            Radius of the plotting area. Usually needs to be adapted to
            the size of the figure.
            Accepts: float

        axes.impedance: 50
            Defines the reference impedance for normalisation.
            Accepts: float

        axes.normalize: True
            If True, the Smith Chart is normalized to the reference impedance.
            Accepts: boolean

        axes.normalize.label: True
            If 'axes.normalize' is True, a label like 'Z_0: 50 Ω' is created
            Accepts: boolean

        axes.normalize.label.position: -1-1j
            Position of normalization label, default is lower left corner
            Accepts: complex number (-1-1j is bottom left, 1+1j it top right)

        symbol.infinity: "∞ "
            Symbol string for infinity.
            Accepts: string

            Note: Without the trailing space the label might get cut off.

        symbol.infinity.correction: 8
            Correction of size for the infinity symbol, because normal symbol
            seems smaller than other letters.
            Accepts: float

        symbol.ohm "Ω"
            Symbol string for the resistance unit (usually a large Omega).
            Accepts: string

    Note: The keywords are processed after the dictionary and override
    possible double entries.
    """

    name = "smith"

    _datatypes = [S_PARAMETER, Z_PARAMETER, Y_PARAMETER]

    # constants used for indicating values near infinity, which are all transformed into one point
    _inf = smithhelper.INF
    _near_inf = 0.9 * smithhelper.INF
    _ax_lim_x = 2 * _inf  # prevents missing labels in special cases
    _ax_lim_y = 2 * _inf  # prevents missing labels in special cases

    # default parameter for matplotlib
    _rcDefaultParams = {
        "font.size": 12,
        "legend.fontsize": 12,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "lines.linestyle": "-",
        "lines.linewidth": 2,
        "lines.markersize": 7,
        "lines.markeredgewidth": 1,
        "xtick.major.pad": 0,
        "ytick.major.pad": 4,
        "legend.fancybox": False,
        "legend.shadow": False,
        "legend.markerscale": 1,
        "legend.numpoints": 3,
        "axes.axisbelow": True,
    }

    # default parameter, see update_scParams for description
    scDefaultParams = {
        "init.updaterc": True,
        "plot.zorder": 4,
        "plot.marker.hack": True,
        "plot.marker.rotate": True,
        "plot.marker.start": "s",
        "plot.marker.default": "o",
        "plot.marker.end": "^",
        "plot.default.interpolation": 5,
        "plot.default.datatype": S_PARAMETER,
        "grid.zorder": 1,
        "grid.locator.precision": 2,
        "grid.major.enable": True,
        "grid.major.linestyle": "-",
        "grid.major.linewidth": 1,
        "grid.major.color": "0.2",
        "grid.major.color.x": "0.2",
        "grid.major.color.y": "0.2",
        "grid.major.xmaxn": 10,
        "grid.major.ymaxn": 16,
        "grid.major.fancy": True,
        "grid.major.fancy.threshold": (100, 50),
        "grid.minor.enable": False,
        "grid.minor.linestyle": ":",
        "grid.minor.capstyle": "round",
        "grid.minor.dashes": [0.2, 2],
        "grid.minor.linewidth": 0.75,
        "grid.minor.color": "0.4",
        "grid.minor.color.x": "0.4",
        "grid.minor.color.y": "0.4",
        "grid.minor.xauto": 4,
        "grid.minor.yauto": 4,
        "grid.minor.fancy": True,
        "grid.minor.fancy.dividers": [1, 2, 3, 5, 10, 20],
        "grid.minor.fancy.threshold": 35,
        "path.default_interpolation": 75,
        "symbol.infinity": "∞ ",  # BUG: symbol gets cut off without end-space
        "symbol.infinity.correction": 8,
        "symbol.ohm": "Ω",
        "axes.xlabel.rotation": 90,
        "axes.xlabel.fancybox": {
            "boxstyle": "round,pad=0.2,rounding_size=0.2",
            "facecolor": "w",
            "edgecolor": "w",
            "mutation_aspect": 0.75,
            "alpha": 1,
        },
        "axes.impedance": 50,
        "axes.ylabel.correction": (-2, 0, 0),
        "axes.radius": 0.43,
        "axes.normalize.label.position": -1 - 1j,
        "axes.normalize": True,
        "axes.normalize.label": True,
    }

    @classmethod
    def get_rc_params(cls):
        """Gets the default values for matplotlib parameters."""
        return cls._rcDefaultParams.copy()

    def update_scParams(self, sc_dict=None, reset=False, **kwargs):
        """
        Update scParams for the current instance based on a dictionary or keyword arguments.

        Args:
            sc_dict (dict, optional): Dictionary of parameters to update.
            reset (bool, optional): If True, resets scParams to default values before updating.
            **kwargs: Additional key-value pairs to update parameters.

        Raises:
            KeyError: If an invalid parameter key is provided (unless `filter_dict` is True).
        """
        # Reset to defaults if specified
        if reset:
            self.scParams = copy.deepcopy(SmithAxes.scDefaultParams)

        # Updates from sc_dict
        if sc_dict is not None:
            for key, value in sc_dict.items():
                if key in self.scParams:
                    self.scParams[key] = value
                    if key == "grid.major.color":
                        self.scParams["grid.major.color.x"] = value
                        self.scParams["grid.major.color.y"] = value
                    elif key == "grid.minor.color":
                        self.scParams["grid.minor.color.x"] = value
                        self.scParams["grid.minor.color.y"] = value
                else:
                    raise KeyError("key '%s' is not in scParams" % key)

        # Update from kwargs
        remaining = kwargs.copy()
        for key in kwargs:
            key_dot = key.replace("_", ".")
            if key_dot in self.scParams:
                value = remaining.pop(key)  # Extract value from kwargs
                self.scParams[key_dot] = value
                if key_dot == "grid.major.color":
                    self.scParams["grid.major.color.x"] = value
                    self.scParams["grid.major.color.y"] = value
                elif key_dot == "grid.minor.color":
                    self.scParams["grid.minor.color.x"] = value
                    self.scParams["grid.minor.color.y"] = value
                else:
                    self.scParams[key_dot] = value
            else:
                raise KeyError("key '%s' is not in scParams" % key_dot)

    def __init__(self, *args, **kwargs):
        """
        Initializes a new instance of the `SmithAxes` class.

        This constructor builds a Smith chart as a custom Matplotlib axes projection.
        It initializes instance-specific parameters, separates axes-related configurations
        from Smith chart-specific configurations, and applies default settings where applicable.

        Args:
            *args:
                Positional arguments passed to the base `matplotlib.axes.Axes` class.
            **kwargs:
                Keyword arguments for configuring the Smith chart or the underlying Matplotlib axes.
                These include:
                    - Smith chart parameters: Parameters specific to the Smith chart, such as
                      normalization, impedance, or appearance settings. See `update_scParams`
                      for a list of supported parameters.
                    - Axes parameters: Parameters unrelated to Smith chart functionality,
                      passed directly to the `matplotlib.axes.Axes` class.

        Attributes:
            scParams (dict):
                A deep copy of the default Smith chart parameters (`SmithAxes.scDefaultParams`)
                for this instance. Modifications to these parameters are unique to the instance.
            _majorarcs (None or list):
                Holds major arcs on the Smith chart, initialized as `None` and set later during rendering.
            _minorarcs (None or list):
                Holds minor arcs on the Smith chart, initialized as `None` and set later during rendering.
            _impedance (None or float):
                Impedance value used for normalizing Smith chart calculations, if applicable.
            _normalize (None or bool):
                Indicates whether normalization is applied to the Smith chart.
            _current_zorder (None or float):
                Tracks the current Z-order of plotted elements for layering purposes.

        Notes:
            - Parameters in `kwargs` not recognized as Smith chart parameters or Matplotlib default parameters
              are treated as axes-specific configurations and passed to the base `matplotlib.axes.Axes` class.
            - This method calls `update_scParams` to apply Smith chart-specific settings.
            - If the `"init.updaterc"` parameter is enabled, this method also updates Matplotlib's `rcParams`
              with custom Smith chart defaults.

        See Also:
            - `update_scParams`: Updates Smith chart-specific parameters for the current instance.
            - `matplotlib.axes.Axes`: The base class for this custom projection.
        """
        # define new class attributes
        self.transProjection = None
        self.transAffine = None
        self.transDataToAxes = None
        self.transAxes = None
        self.transMoebius = None
        self.transData = None
        self._xaxis_pretransform = None
        self._xaxis_transform = None
        self._xaxis_text1_transform = None
        self._yaxis_stretch = None
        self._yaxis_correction = None
        self._yaxis_transform = None
        self._yaxis_text1_transform = None

        self._majorarcs = None
        self._minorarcs = None
        self._impedance = None
        self._normalize = None
        self._current_zorder = None

        # Create a unique copy of the default parameters for this instance
        self.scParams = copy.deepcopy(SmithAxes.scDefaultParams)

        # Separate out parameters intended for Axes configuration.
        # Iterate through the provided keyword arguments (`kwargs`) to identify any
        # parameters not meant for `scParams` or `_rcDefaultParams`. These parameters
        # are assumed to be for Axes and are moved to `axes_kwargs`.
        axes_kwargs = {}
        for key in kwargs.copy():
            key_dot = key.replace("_", ".")
            if not (key_dot in self.scParams or key_dot in self._rcDefaultParams):
                axes_kwargs[key] = kwargs.pop(key_dot)

        self.update_scParams(**kwargs)

        if self._get_key("init.updaterc"):
            for key, value in self._rcDefaultParams.items():
                if mp.rcParams[key] == mp.rcParamsDefault[key]:
                    mp.rcParams[key] = value

        Axes.__init__(self, *args, **axes_kwargs)
        self.set_aspect(1, adjustable="box", anchor="C")
        self.tick_params(axis="both", which="both", bottom=False, top=False, left=False, right=False)

    def _get_key(self, key):
        """Get value for key from the local dictionary or the global matplotlib rcParams."""
        if key in self.scParams:
            return self.scParams[key]
        if key in mp.rcParams:
            return mp.rcParams[key]
        raise KeyError("%s is not a valid key" % key)

    def _init_axis(self):
        self.xaxis = mp.axis.XAxis(self)
        self.yaxis = mp.axis.YAxis(self)
        self._update_transScale()

    def clear(self):
        """
        Clear the current Smith Chart axes and reset them to their initial state.

        This method overrides the base `clear` (clear axes) method from `matplotlib.axes.Axes`
        to perform additional setup and customization specific to the Smith Chart. It clears
        custom properties like arcs, gridlines, and axis formatting, while also restoring
        default configurations.

        Key Functionality:
            - Resets internal storage for major and minor arcs (`_majorarcs` and `_minorarcs`).
            - Temporarily disables the grid functionality during the base class's `clear` call
              to prevent unintended behavior.
            - Reinitializes important Smith Chart-specific properties, such as normalization
              settings, impedance, and z-order tracking.
            - Configures axis locators and formatters for real and imaginary components.
            - Updates axis tick alignment, label styles, and normalization box positioning.
            - Redraws the gridlines (major and minor) based on the current settings.

        Notes:
            - This method ensures that the Smith Chart maintains its specific configuration
              after clearing, unlike a standard `matplotlib` axes.
            - Labels and gridlines are re-added to maintain proper layering and alignment.

        Side Effects:
            - Resets `_majorarcs` and `_minorarcs` to empty lists.
            - Updates the axis locators, formatters, and gridlines.
            - Configures custom label alignment and appearance.
        """
        self._majorarcs = []
        self._minorarcs = []

        original_grid = self.grid
        self.grid = lambda *args, **kwargs: None  # No-op grid method
        try:
            Axes.clear(self)
        finally:
            self.grid = original_grid

        self._normbox = None
        self._impedance = self._get_key("axes.impedance")
        self._normalize = self._get_key("axes.normalize")
        self._current_zorder = self._get_key("plot.zorder")

        self.xaxis.set_major_locator(self.RealMaxNLocator(self, self._get_key("grid.major.xmaxn")))
        self.yaxis.set_major_locator(self.ImagMaxNLocator(self, self._get_key("grid.major.ymaxn")))

        self.xaxis.set_minor_locator(self.SmithAutoMinorLocator(self._get_key("grid.minor.xauto")))
        self.yaxis.set_minor_locator(self.SmithAutoMinorLocator(self._get_key("grid.minor.yauto")))

        self.xaxis.set_ticks_position("none")
        self.yaxis.set_ticks_position("none")

        Axes.set_xlim(self, 0, self._ax_lim_x)
        Axes.set_ylim(self, -self._ax_lim_y, self._ax_lim_y)

        for label in self.get_xticklabels():   # pylint: disable=not-callable
            label.set_verticalalignment("center")
            label.set_horizontalalignment("center")
            label.set_rotation_mode("anchor")
            label.set_rotation(self._get_key("axes.xlabel.rotation"))
            label.set_bbox(self._get_key("axes.xlabel.fancybox"))
            self.add_artist(label)  # if not readded, labels are drawn behind grid

        for tick, loc in zip(self.yaxis.get_major_ticks(), self.yaxis.get_majorticklocs()):
            # workaround for fixing too small infinity symbol
            if abs(loc) > self._near_inf:
                tick.label1.set_size(tick.label1.get_size() + self._get_key("symbol.infinity.correction"))

            tick.label1.set_verticalalignment("center")

            x = np.real(self.moebius_z(loc * 1j))
            if x < -0.1:
                tick.label1.set_horizontalalignment("right")
            elif x > 0.1:
                tick.label1.set_horizontalalignment("left")
            else:
                tick.label1.set_horizontalalignment("center")

        self.yaxis.set_major_formatter(self.ImagFormatter(self))
        self.xaxis.set_major_formatter(self.RealFormatter(self))

        if self._get_key("axes.normalize") and self._get_key("axes.normalize.label"):
            x, y = z_to_xy(self.moebius_inv_z(self._get_key("axes.normalize.label.position")))
            impedance = self._get_key("axes.impedance")
            s = r"Z$_\mathrm{0}$ = %d$\,$%s" % (impedance, self._get_key("symbol.ohm"))
            box = self.text(x, y, s, ha="left", va="bottom")
            px = self._get_key("ytick.major.pad")
            py = px + 0.5 * box.get_fontsize()
            box.set_transform(self._yaxis_correction + Affine2D().translate(-px, -py))

        for grid in ["major", "minor"]:
            self.grid(visible=self._get_key("grid.%s.enable" % grid), which=grid)

    def _set_lim_and_transforms(self):
        """
        Configure the axis limits and transformation pipelines for the chart.

        This method defines and applies a series of transformations to map data
        space, Möbius space, axes space, and drawing space.

        Transformations:
            - `transProjection`: Maps data space to Möbius space using a Möbius transformation.
            - `transAffine`: Scales and translates Möbius space to fit axes space.
            - `transDataToAxes`: Combines `transProjection` and `transAffine` to map data space to axes space.
            - `transAxes`: Maps axes space to drawing space using the bounding box (`bbox`).
            - `transMoebius`: Combines `transAffine` and `transAxes` to map Möbius space to drawing space.
            - `transData`: Combines `transProjection` and `transMoebius` as data-to-drawing-space transform.

        X-axis transformations:
            - `_xaxis_pretransform`: Scales and centers the x-axis based on axis limits.
            - `_xaxis_transform`: Combines `_xaxis_pretransform` and `transData` for full x-axis mapping.
            - `_xaxis_text1_transform`: Adjusts x-axis label positions.

        Y-axis transformations:
            - `_yaxis_stretch`: Scales the y-axis based on axis limits.
            - `_yaxis_correction`: Applies additional translation to the y-axis for label adjustments.
            - `_yaxis_transform`: Combines `_yaxis_stretch` and `transData` for full y-axis mapping.
            - `_yaxis_text1_transform`: Combines `_yaxis_stretch` and `_yaxis_correction` for y label position
        """
        r = self._get_key("axes.radius")
        self.transProjection = self.MoebiusTransform(self)  # data space  -> moebius space
        self.transAffine = Affine2D().scale(r, r).translate(0.5, 0.5)  # moebius space -> axes space
        self.transDataToAxes = self.transProjection + self.transAffine
        self.transAxes = BboxTransformTo(self.bbox)  # axes space -> drawing space
        self.transMoebius = self.transAffine + self.transAxes
        self.transData = self.transProjection + self.transMoebius

        self._xaxis_pretransform = Affine2D().scale(1, 2 * self._ax_lim_y).translate(0, -self._ax_lim_y)
        self._xaxis_transform = self._xaxis_pretransform + self.transData
        self._xaxis_text1_transform = Affine2D().scale(1.0, 0.0) + self.transData

        self._yaxis_stretch = Affine2D().scale(self._ax_lim_x, 1.0)
        self._yaxis_correction = self.transData + Affine2D().translate(
            *self._get_key("axes.ylabel.correction")[:2]
        )
        self._yaxis_transform = self._yaxis_stretch + self.transData
        self._yaxis_text1_transform = self._yaxis_stretch + self._yaxis_correction

    def get_xaxis_transform(self, which="grid"):
        """Return the x-axis transformation for ticks or grid."""
        assert which in ["tick1", "tick2", "grid"]
        return self._xaxis_transform

    def get_xaxis_text1_transform(self, pad_points):
        """Return the transformation for x-axis label placement."""
        return self._xaxis_text1_transform, "center", "center"

    def get_yaxis_transform(self, which="grid"):
        """Return the y-axis transformation for ticks or grid."""
        assert which in ["tick1", "tick2", "grid"]
        return self._yaxis_transform

    def get_yaxis_text1_transform(self, pad_points):
        """Return the transformation for y-axis label placement."""
        if hasattr(self, "yaxis") and len(self.yaxis.majorTicks) > 0:
            font_size = self.yaxis.majorTicks[0].label1.get_size()
        else:
            font_size = self._get_key("font.size")

        offset = self._get_key("axes.ylabel.correction")[2]
        return (
            self._yaxis_text1_transform
            + self.PolarTranslate(self, pad=pad_points + offset, font_size=font_size),
            "center",
            "center",
        )

    def _gen_axes_patch(self):
        """Generate the patch used to draw the Smith chart axes."""
        r = self._get_key("axes.radius") + 0.015
        c = self._get_key("grid.major.color.x")
        return Circle((0.5, 0.5), r, edgecolor=c)

    def _gen_axes_spines(self, locations=None, offset=0.0, units="inches"):
        """Generate the spines for the circular Smith chart axes."""
        return {SmithAxes.name: Spine.circular_spine(self, (0.5, 0.5), self._get_key("axes.radius"))}

    def set_xscale(self, *args, **kwargs):
        """
        Set the x-axis scale (only 'linear' is supported).

        Args:
            *args: Positional arguments for the scale (first argument must be 'linear').
            **kwargs: Keyword arguments for additional scale settings.
        """
        if len(args) == 0 or args[0] != "linear":
            raise NotImplementedError("Only 'linear' scale is supported for the x-axis.")
        # pylint: disable=not-callable
        Axes.set_xscale(self, *args, **kwargs)

    def set_yscale(self, *args, **kwargs):
        """
        Set the y-axis scale (only 'linear' is supported).

        Args:
            *args: Positional arguments for the scale (first argument must be 'linear').
            **kwargs: Keyword arguments for additional scale settings.
        """
        if len(args) == 0 or args[0] != "linear":
            raise NotImplementedError("Only 'linear' scale is supported for the y-axis.")
        # pylint: disable=not-callable
        Axes.set_yscale(self, *args, **kwargs)

    def set_xlim(self, *args, **kwargs):
        """
        Override the `set_xlim` method to enforce immutability.

        The x-axis limits for the Smith chart are fixed to `(0, infinity)` and cannot
        be modified. Any arguments passed to this method are ignored.
        """
        # pylint: disable=unused-argument
        Axes.set_xlim(self, 0, self._ax_lim_x)

    def set_ylim(self, *args, **kwargs):
        """
        Override the `set_ylim` method to enforce immutability.

        The y-axis limits for the Smith chart are fixed to `(-infinity, infinity)` and cannot
        be modified. Any arguments passed to this method are ignored.
        """
        # pylint: disable=unused-argument
        Axes.set_ylim(self, -self._ax_lim_y, self._ax_lim_y)

    def format_coord(self, x, y):
        """Format real and imaginary parts of a complex number."""
        sgn = "+" if y > 0 else "-"
        return "%.5f %s %.5fj" % (x, sgn, abs(y)) if x > 0 else ""

    def get_data_ratio(self):
        """Return the fixed aspect ratio of the Smith chart data."""
        return 1.0

    def can_zoom(self):
        """Check if zooming is enabled (always returns False)."""
        return False

    def start_pan(self, x, y, button):
        """Handle the start of a pan action (disabled for Smith chart)."""

    def end_pan(self):
        """Handle the end of a pan action (disabled for Smith chart)."""

    def drag_pan(self, button, key, x, y):
        """Handle panning during a drag action (disabled for Smith chart)."""

    def moebius_z(self, *args, normalize=None):
        """
        Apply a Möbius transformation to the input values.

        This function uses the `smithhelper.moebius_z` method to compute the Möbius transformation:
        `w = 1 - 2 * norm / (z + norm)`. The transformation can handle a single complex value or
        a combination of real and imaginary parts provided as separate arguments. The normalization
        value can be specified or determined automatically based on the instance's settings.

        Args:
            *args:
                Input arguments passed to `smithhelper.moebius_z`. These can include:
                - A single complex number or numpy.ndarray with `dtype=complex`.
                - Two arguments representing the real and imaginary parts of a complex number
                  or array of complex numbers (floats or arrays of floats).
            normalize (bool or None, optional):
                If `True`, normalizes the values to `self._impedance`.
                If `None`, uses the instance attribute `self._normalize` to determine behavior.
                If `False`, no normalization is applied.

        Returns:
            complex or numpy.ndarray:
                The Möbius-transformed value(s), returned as a complex number or an array of
                complex numbers, depending on the input.
        """
        if normalize is not None:
            print("moebius normalize=", normalize)

        if normalize is None:
            normalize = self._normalize

        if normalize:
            norm = 1
        else:
            norm = self._get_key("axes.impedance")

        return smithhelper.moebius_z(*args, norm=norm)

    def moebius_inv_z(self, *args, normalize=None):
        """
        Perform the inverse Möbius transformation.

        This method applies the inverse Möbius transformation formula:
        w = k * (1 - z)/(1 + z), where k is determined
        by the axes scale or normalization settings. The transformation is
        applied to complex numbers or real/imaginary pairs.

         Normalization is applied using the impedance (`self._impedance`) if enabled.
         This method uses the `smithhelper.moebius_inv_z` utility for calculations.

        Args:
            *args:
                Input data to transform, either as:
                - `z` (complex): A complex number or `numpy.ndarray` with `dtype=complex`.
                - `x, y` (float): Real and imaginary parts, either as floats or
                  `numpy.ndarray` values with non-complex `dtype`.
            normalize (bool or None, optional):
                Specifies whether to normalize the transformation:
                - `True`: Normalize values to `self._impedance`.
                - `False`: No normalization is applied.
                - `None` (default): Use the instance's default normalization setting (`self._normalize`).

        Returns: Transformed data, either as a single complex value or a
                `numpy.ndarray` with `dtype=complex`.
        """
        normalize = self._normalize if normalize is None else normalize
        norm = 1 if normalize else self._get_key("axes.impedance")
        return smithhelper.moebius_inv_z(*args, norm=norm)

    def real_interp1d(self, x, steps):
        """
        Interpolate a vector of real values with evenly spaced points.

        This method interpolates the given real values such that, after applying a Möbius
        transformation with an imaginary part of 0, the resulting points are evenly spaced.

        The result is mapped back to the original space using the inverse Möbius transformation.

        Args:
            x (iterable): Real values to interpolate.
            steps (int): Interpolation steps between two points.

        Returns: Interpolated real values.
        """
        return self.moebius_inv_z(linear_interpolation(self.moebius_z(np.array(x)), steps))

    def imag_interp1d(self, y, steps):
        """
        Interpolate a vector of imaginary values with evenly spaced points.

        This method interpolates the given imaginary values such that, after applying
        a Möbius transformation with a real part of 0, the resulting points are evenly spaced.

        The result is mapped back to the original space using the inverse Möbius transformation.

        Args:
            y (iterable): Imaginary values to interpolate.
            steps (int): Interpolation steps between two points.

        Returns: Interpolated imaginary values.
        """
        angs = np.angle(self.moebius_z(np.array(y) * 1j)) % TWO_PI
        i_angs = linear_interpolation(angs, steps)
        return np.imag(self.moebius_inv_z(ang_to_c(i_angs)))

    def legend(self, *args, **kwargs):
        """
        Create and display a legend for the Smith chart, filtering duplicate entries.

        This method customizes the legend behavior to ensure unique entries are displayed
        and applies a specialized handler for lines with custom markers. It also filters out
        duplicate legend labels, keeping only the first occurrence.

        Args:
            *args:
                Positional arguments passed directly to `matplotlib.axes.Axes.legend`.
            **kwargs:
                Keyword arguments for configuring the legend. Includes all standard arguments
                supported by `matplotlib.axes.Axes.legend`, such as:
                    - loc: Location of the legend (e.g., 'upper right', 'lower left').
                    - fontsize: Font size for the legend text.
                    - ncol: Number of columns in the legend.
                    - title: Title for the legend.
                See the Matplotlib documentation for more details.

        Returns:
            matplotlib.legend.Legend:
                The legend instance created for the Smith chart.
        """
        this_axes = self

        class SmithHandlerLine2D(HandlerLine2D):
            """
            Custom legend handler for `Line2D` objects in Smith charts.

            This class extends `matplotlib.legend_handler.HandlerLine2D` to provide
            customized rendering of legend entries for `Line2D` objects, especially
            those with marker modifications in Smith charts. It ensures that custom
            markers, such as start and end markers, are rendered correctly in the legend.
            """

            def create_artists(
                self,
                legend,
                orig_handle,
                xdescent,
                ydescent,
                width,
                height,
                fontsize,
                trans,
            ):
                """Creates the legend artist applying custom markers."""
                legline = HandlerLine2D.create_artists(
                    self,
                    legend,
                    orig_handle,
                    xdescent,
                    ydescent,
                    width,
                    height,
                    fontsize,
                    trans,
                )

                if hasattr(orig_handle, "markers_hacked"):
                    this_axes.hack_linedraw(legline[0], True)
                return legline

        # Filter out duplicate legend entries while keeping the first occurrence
        handles, labels = self.get_legend_handles_labels()
        seen_labels = set()
        unique_handles = []
        unique_labels = []

        for handle, label in zip(handles, labels):
            if label not in seen_labels:
                seen_labels.add(label)
                unique_handles.append(handle)
                unique_labels.append(label)

        # Pass unique handles and labels to the legend
        return Axes.legend(
            self, unique_handles, unique_labels, handler_map={Line2D: SmithHandlerLine2D()}, **kwargs
        )

    def plot(self, *args, **kwargs):
        """
        Plot data on the Smith Chart.

        This method extends the functionality of :meth:`matplotlib.axes.Axes.plot` to
        support Smith Chart-specific features, including handling of complex data and
        additional keyword arguments for customization.

        Args:
            *args:
                Positional arguments for the data to plot. Supports real and complex
                data. Complex data should either be of type `complex` or a
                `numpy.ndarray` with `dtype=complex`.
            **kwargs:
                Keyword arguments for customization. Includes all arguments supported
                by :meth:`matplotlib.axes.Axes.plot`, along with the following:

                datatype (str, optional):
                    Specifies the input data format. Must be one of:
                    - `S_PARAMETER` ('S'): Scattering parameters.
                    - `Z_PARAMETER` ('Z'): Impedance.
                    - `Y_PARAMETER` ('Y'): Admittance.
                    Defaults to `Z_PARAMETER`.

                interpolate (bool or int, optional):
                    If `True`, interpolates the given data linearly with a default step size.
                    If an integer, specifies the number of interpolation steps.
                    Defaults to `False`.

                equipoints (bool or int, optional):
                    If `True`, interpolates the data to equidistant points. If an integer,
                    specifies the number of equidistant points. Cannot be used with
                    `interpolate`. Defaults to `False`.

                markerhack (bool, optional):
                    Enables manipulation of the start and end markers of the line.
                    Defaults to `False`.

                rotate_marker (bool, optional):
                    If `markerhack` is enabled, rotates the end marker in the direction
                    of the corresponding path. Defaults to `False`.

        Returns:
            list[matplotlib.lines.Line2D]:
                A list of line objects representing the plotted data.

        Raises:
            ValueError: If `datatype` is not one of `S_PARAMETER`, `Z_PARAMETER`, or `Y_PARAMETER`.
            ValueError: If both `interpolate` and `equipoints` are enabled.
            ValueError: If `interpolate` is specified with a non-positive value.

        Examples:
            Plot impedance data on a Smith Chart:

            >>> import matplotlib.pyplot as plt
            >>> import pysmithchart
            >>> ZL = [30 + 30j, 50 + 50j, 100 + 100j]
            >>> plt.subplot(1, 1, 1, projection="smith")
            >>> plt.plot(ZL, "b", marker="o", markersize=10, datatype=pysmithchart.Z_PARAMETER)
            >>> plt.show()
        """
        # Extract and validate datatype
        datatype = kwargs.pop("datatype", self._get_key("plot.default.datatype"))
        if datatype not in self._datatypes:
            raise ValueError(
                f"Invalid datatype: {datatype}. Must be S_PARAMETER, Z_PARAMETER, or Y_PARAMETER"
            )

        # split input into real and imaginary part if complex
        new_args = ()
        for arg in args:
            if not isinstance(arg, (str, np.ndarray)):
                if isinstance(arg, Number):
                    # Convert single numbers to a 1-element numpy array
                    arg = np.array([arg])
                elif isinstance(arg, Iterable):
                    # Convert iterables (e.g., lists, tuples) to numpy arrays
                    arg = np.array(arg)

            # Additional processing for complex numpy arrays
            if isinstance(arg, np.ndarray) and arg.dtype in [complex, np.complex128]:
                new_args += z_to_xy(arg)
            else:
                new_args += (arg,)

        # ensure newer plots are above older ones
        if "zorder" not in kwargs:
            kwargs["zorder"] = self._current_zorder
            self._current_zorder += 0.001

        # extract or load non-matplotlib keyword arguments from parameters
        interpolate = kwargs.pop("interpolate", False)
        equipoints = kwargs.pop("equipoints", False)
        kwargs.setdefault("marker", self._get_key("plot.marker.default"))
        markerhack = kwargs.pop("markerhack", self._get_key("plot.marker.hack"))
        rotate_marker = kwargs.pop("rotate_marker", self._get_key("plot.marker.rotate"))

        if interpolate:
            if equipoints > 0:
                raise ValueError("Interpolation is not available with equidistant markers")

            interpolation = self._get_key("plot.default.interpolation")
            if interpolation < 0:
                raise ValueError("Interpolation is only for positive values possible!")

            if "markevery" in kwargs:
                mark = kwargs["markevery"]
                if isinstance(mark, Iterable):
                    mark = np.asarray(mark) * (interpolate + 1)
                else:
                    mark *= interpolate + 1
                kwargs["markevery"] = mark

        lines = Axes.plot(self, *new_args, **kwargs)
        for line in lines:
            cdata = smithhelper.xy_to_z(line.get_data())

            if datatype == S_PARAMETER:
                z = self.moebius_inv_z(cdata)
            elif datatype == Y_PARAMETER:
                z = 1 / cdata
            else:
                z = cdata

            if self._normalize and datatype != S_PARAMETER:
                z /= self._get_key("axes.impedance")

            line.set_data(z_to_xy(z))

            if interpolate or equipoints:
                z = self.moebius_z(*line.get_data())
                if len(z) > 1:
                    # pylint: disable=unbalanced-tuple-unpacking
                    spline, t0 = splprep(z_to_xy(z), s=0)
                    ilen = (interpolate + 1) * (len(t0) - 1) + 1
                    if equipoints == 1:
                        t = np.linspace(0, 1, ilen)
                    elif equipoints > 1:
                        t = np.linspace(0, 1, equipoints)
                    else:
                        t = np.zeros(ilen)
                        t[0], t[1:] = t0[0], np.concatenate(
                            [np.linspace(i0, i1, interpolate + 2)[1:] for i0, i1 in zip(t0[:-1], t0[1:])]
                        )

                    z = self.moebius_inv_z(*splev(t, spline))
                    line.set_data(z_to_xy(z))

            if markerhack:
                self.hack_linedraw(line, rotate_marker)

        return lines

    def grid(self, visible=None, which="major", axis=None, dividers=None, threshold=None, **kwargs):
        """
        Draw gridlines on the Smith chart, with optional customization for style and behavior.

        This method overrides the default grid functionality in Matplotlib to use arcs
        instead of straight lines. The grid consists of major and minor components, which
        can be drawn in either a standard or "fancy" style. Fancy grids dynamically adjust
        spacing and length based on specified parameters.

        The "fancy" grid mode is only valid when `axis='both'`.

        Keyword arguments like `linestyle`, `linewidth`, `color`, and `alpha`
        can be used to customize the grid appearance.

        The `zorder` of the gridlines defaults to the Smith chart's settings
        unless explicitly overridden.

        Args:
            visible (bool, optional):
                Enables or disables the selected grid. Defaults to the current state.
            which (str, optional):
                Specifies which gridlines to draw:
                - `'major'`: Major gridlines only.
                - `'minor'`: Minor gridlines only.
                - `'both'`: Both major and minor gridlines.
                Defaults to `'major'`.
            axis (bool, optional):
                If `True`, draws the grid in a "fancy" style with dynamic spacing
                and length adjustments. Defaults to `None`, which uses the standard style.
            dividers (list[int], optional):
                Adaptive divisions for the minor fancy grid. Only applicable when `axis=True`.
                Has no effect on major or standard grids.
            threshold (float or tuple[float, float], optional):
                Specifies the threshold for dynamically adapting grid spacing and
                line length. Can be a single float for both axes or a tuple for
                individual axis thresholds.
            **kwargs:
                Additional keyword arguments passed to the gridline creator. Note that
                gridlines are created as `matplotlib.patches.Patch` objects, so not all
                properties from `matplotlib.lines.Line2D` are supported.

        See Also:
            - `matplotlib.axes.Axes.grid`: The base grid function being overridden.
            - `matplotlib.patches.Patch`: The class used to create the gridlines.
        """
        assert which in ["both", "major", "minor"]
        assert axis in [None, False, True]

        def get_kwargs(grid):
            kw = kwargs.copy()
            kw.setdefault("zorder", self._get_key("grid.zorder"))
            kw.setdefault("alpha", self._get_key("grid.alpha"))

            for key in ["linestyle", "linewidth", "color"]:
                if grid == "minor" and key == "linestyle":
                    if "linestyle" not in kw:
                        kw.setdefault("dash_capstyle", self._get_key("grid.minor.capstyle"))
                        kw.setdefault("dashes", self._get_key("grid.minor.dashes"))
                else:
                    kw.setdefault(key, self._get_key("grid.%s.%s" % (grid, key)))

            return kw

        def check_fancy(yticks):
            """
            Checks if the imaginary axis ticks are symmetric about zero.

            This property is required for "fancy" minor grid styling.

            Args:
                yticks: Array or list of tick values for the imaginary axis.

            Returns:
                The upper half of the `yticks` array (non-negative values).
            """
            len_y = (len(yticks) - 1) // 2  # Calculate the midpoint index
            if not (len(yticks) % 2 == 1 and (yticks[len_y:] + yticks[len_y::-1] < EPSILON).all()):
                s = "Fancy minor grid is only supported for zero-symmetric imaginary grid. "
                s += "--- e.g., ImagMaxNLocator"
                raise ValueError(s)
            return yticks[len_y:]

        def split_threshold(threshold):
            if isinstance(threshold, tuple):
                thr_x, thr_y = threshold
            else:
                thr_x = thr_y = threshold

            assert thr_x > 0 and thr_y > 0

            return thr_x / 1000, thr_y / 1000

        def add_arc(ps, p0, p1, grid, arc_type):
            """
            Add an arc to the Smith Chart.

            Parameters:
                ps (tuple): Starting point of the arc in parameterized space.
                p0 (tuple): One endpoint of the arc.
                p1 (tuple): The other endpoint of the arc.
                grid (str): Specifies whether the arc is part of the "major" or "minor" grid.
                            Must be one of ["major", "minor"].
                arc_type (str): Specifies the type of the arc, either "real" or "imag" for
                            real or imaginary components.

            Side Effects:
                Appends the created arc to the appropriate list:
                - `_majorarcs` if `grid` is "major".
                - `_minorarcs` if `grid` is "minor".

            Notes:
                The `param` variable, which holds the styling parameters for the gridline
                (e.g., z-order, color, etc.), is defined in the enclosing scope.
            """
            assert grid in ["major", "minor"]
            assert arc_type in ["real", "imag"]
            assert p0 != p1
            if grid == "major":
                arcs = self._majorarcs
                if arc_type == "real":
                    param["color"] = self._get_key("grid.major.color.x")
                else:
                    param["color"] = self._get_key("grid.major.color.y")
            else:
                arcs = self._minorarcs
                if arc_type == "real":
                    param["color"] = self._get_key("grid.minor.color.x")
                else:
                    param["color"] = self._get_key("grid.minor.color.y")
                param["zorder"] -= 1e-9
            arcs.append((arc_type, (ps, p0, p1), self._add_gridline(ps, p0, p1, arc_type, **param)))

        def draw_nonfancy(grid):
            if grid == "major":
                xticks = self.xaxis.get_majorticklocs()
                yticks = self.yaxis.get_majorticklocs()
            else:
                xticks = self.xaxis.get_minorticklocs()
                yticks = self.yaxis.get_minorticklocs()

            xticks = np.round(xticks, 7)
            yticks = np.round(yticks, 7)

            for xs in xticks:
                if xs < self._near_inf:
                    add_arc(xs, -self._near_inf, self._inf, grid, "real")

            for ys in yticks:
                if abs(ys) < self._near_inf:
                    add_arc(ys, 0, self._inf, grid, "imag")

        # set fancy parameters
        if axis is None:
            fancy_major = self._get_key("grid.major.fancy")
            fancy_minor = self._get_key("grid.minor.fancy")
        else:
            fancy_major = fancy_minor = axis

        # check parameters
        if "axis" in kwargs and kwargs["axis"] != "both":
            raise ValueError("Only 'both' is a supported value for 'axis'")

        # plot major grid
        if which in ["both", "major"]:
            for _, _, arc in self._majorarcs:
                arc.remove()
            self._majorarcs = []

            if visible:
                param = get_kwargs("major")
                if fancy_major:
                    xticks = np.sort(self.xaxis.get_majorticklocs())
                    yticks = np.sort(self.yaxis.get_majorticklocs())
                    assert len(xticks) > 0 and len(yticks) > 0
                    yticks = check_fancy(yticks)

                    if threshold is None:
                        threshold = self._get_key("grid.major.fancy.threshold")

                    thr_x, thr_y = split_threshold(threshold)

                    # draw the 0 line
                    add_arc(yticks[0], 0, self._inf, "major", "imag")

                    tmp_yticks = yticks.copy()
                    for xs in xticks:
                        k = 1
                        while k < len(tmp_yticks):
                            y0, y1 = tmp_yticks[k - 1 : k + 1]
                            if abs(self.moebius_z(xs, y0) - self.moebius_z(xs, y1)) < thr_x:
                                add_arc(y1, 0, xs, "major", "imag")
                                add_arc(-y1, 0, xs, "major", "imag")
                                tmp_yticks = np.delete(tmp_yticks, k)
                            else:
                                k += 1

                    for i in range(1, len(yticks)):
                        y0, y1 = yticks[i - 1 : i + 1]
                        k = 1
                        while k < len(xticks):
                            x0, x1 = xticks[k - 1 : k + 1]
                            if abs(self.moebius_z(x0, y1) - self.moebius_z(x1, y1)) < thr_y:
                                add_arc(x1, -y0, y0, "major", "real")
                                xticks = np.delete(xticks, k)
                            else:
                                k += 1
                else:
                    draw_nonfancy("major")

        # plot minor grid
        if which in ["both", "minor"]:
            # remove the old grid
            for _, _, arc in self._minorarcs:
                arc.remove()
            self._minorarcs = []

            if visible:
                param = get_kwargs("minor")

                if fancy_minor:
                    # 1. Step: get x/y grid data
                    xticks = np.sort(self.xaxis.get_majorticklocs())
                    yticks = np.sort(self.yaxis.get_majorticklocs())
                    assert len(xticks) > 0 and len(yticks) > 0
                    yticks = check_fancy(yticks)

                    if dividers is None:
                        dividers = self._get_key("grid.minor.fancy.dividers")
                    assert len(dividers) > 0
                    dividers = np.sort(dividers)

                    if threshold is None:
                        threshold = self._get_key("grid.minor.fancy.threshold")

                    thr_x, thr_y = split_threshold(threshold)
                    len_x, len_y = len(xticks) - 1, len(yticks) - 1

                    # 2. Step: calculate optimal gridspacing for each quadrant
                    d_mat = np.ones((len_x, len_y, 2), dtype=int)

                    # TODO: optimize spacing algorithm
                    for i in range(len_x):
                        for k in range(len_y):
                            x0, x1 = xticks[i : i + 2]
                            y0, y1 = yticks[k : k + 2]

                            xm = self.real_interp1d([x0, x1], 2)[1]
                            ym = self.imag_interp1d([y0, y1], 2)[1]

                            x_div = y_div = dividers[0]

                            for div in dividers[1:]:
                                if (
                                    abs(self.moebius_z(x1 - (x1 - x0) / div, ym) - self.moebius_z(x1, ym))
                                    > thr_x
                                ):
                                    x_div = div
                                else:
                                    break

                            for div in dividers[1:]:
                                if (
                                    abs(self.moebius_z(xm, y1) - self.moebius_z(xm, y1 - (y1 - y0) / div))
                                    > thr_y
                                ):
                                    y_div = div
                                else:
                                    break

                            d_mat[i, k] = [x_div, y_div]

                    # 3. Steps: optimize spacing
                    # ensure the x-spacing declines towards infinity
                    d_mat[:-1, 0, 0] = list(map(np.max, zip(d_mat[:-1, 0, 0], d_mat[1:, 0, 0])))

                    # find the values which are near (0, 0.5) on the plot
                    idx = np.searchsorted(xticks, self.moebius_inv_z(0)) + 1
                    idy = np.searchsorted(yticks, self.moebius_inv_z(1j).imag)

                    # extend the values around the center towards the border
                    if idx > idy:
                        for d in range(idy):
                            delta = idx - idy + d
                            d_mat[delta, : d + 1] = d_mat[:delta, d] = d_mat[delta, 0]
                    else:
                        for d in range(idx):
                            delta = idy - idx + d
                            d_mat[: d + 1, delta] = d_mat[d, :delta] = d_mat[d, 0]

                    # 4. Step: gather and optimize the lines
                    x_lines, y_lines = [], []

                    for i in range(len_x):
                        x0, x1 = xticks[i : i + 2]

                        for k in range(len_y):
                            y0, y1 = yticks[k : k + 2]

                            x_div, y_div = d_mat[i, k]

                            for xs in np.linspace(x0, x1, x_div + 1)[1:]:
                                x_lines.append([xs, y0, y1])
                                x_lines.append([xs, -y1, -y0])

                            for ys in np.linspace(y0, y1, y_div + 1)[1:]:
                                y_lines.append([ys, x0, x1])
                                y_lines.append([-ys, x0, x1])

                    # round values to prevent float inaccuarcy
                    x_lines = np.round(np.array(x_lines), 7)
                    y_lines = np.round(np.array(y_lines), 7)

                    # Remove lines that overlap with the major grid
                    for tp, lines in [("real", x_lines), ("imag", y_lines)]:
                        # Ensure p0 is always less than p1 for each line
                        lines = np.array([[ps, min(p0, p1), max(p0, p1)] for ps, p0, p1 in lines])

                        # Remove overlapping lines
                        for tq, (qs, q0, q1), _ in self._majorarcs:
                            if tp == tq:
                                overlaps = (
                                    (abs(lines[:, 0] - qs) < EPSILON)
                                    & (lines[:, 2] > q0)
                                    & (lines[:, 1] < q1)
                                )
                                lines[overlaps] = np.nan

                        # Remove NaN entries and sort lines by ps, p0
                        lines = lines[~np.isnan(lines[:, 0])]
                        lines = lines[np.lexsort((lines[:, 1], lines[:, 0]))]

                        # Combine adjacent line segments
                        ps, p0, p1 = lines[0]
                        for qs, q0, q1 in lines[1:]:
                            if ps != qs or not np.isclose(p1, q0, atol=EPSILON):
                                add_arc(ps, p0, p1, "minor", tp)
                                ps, p0, p1 = qs, q0, q1
                            else:
                                p1 = q1

                else:
                    draw_nonfancy("minor")

    def hack_linedraw(self, line, rotate_marker):
        """
        Draw lines with different markers for start and end points.

        Modify the draw method of a `matplotlib.lines.Line2D` object to use
        different markers at the start and end points, optionally rotating the
        end marker to align with the path direction.

        This method customizes the appearance of lines by replacing the default
        marker behavior with dynamic start and end markers. It supports rotation
        of the end marker to follow the line's direction and ensures intermediate
        points retain the original marker style.

        Args:
            line (matplotlib.lines.Line2D):
                The line object to be modified.
            rotate_marker (bool):
                If `True`, the end marker is rotated to align with the tangent
                of the line's path. If `False`, the marker remains unrotated.

        Implementation Details:
            1. A nested `new_draw` method replaces the `Line2D.draw` method. This
               handles drawing start and end markers separately from intermediate points.
            2. If `rotate_marker` is enabled, the end marker is rotated to align
               with the path's direction using an affine transformation.
            3. The original `Line2D.draw` method is restored after rendering.
        """

        # Helper function to validate marker styles
        def to_marker_style(marker):
            if marker is None:
                return MarkerStyle("o")  # Default marker
            if isinstance(marker, MarkerStyle):
                return marker
            return MarkerStyle(marker)  # Convert string to MarkerStyle

        # Fetch and validate marker styles
        start_marker = self._get_key("plot.marker.start")
        end_marker = self._get_key("plot.marker.end")

        start = to_marker_style(start_marker)
        end = to_marker_style(end_marker)

        assert isinstance(line, Line2D)

        def new_draw(self_line, renderer):
            """
            Custom draw method for the line, allowing marker rotation and manipulation.

            Args:
                self_line (Line2D): The line object to draw.
                renderer: The renderer instance used to draw the line.
            """

            def new_draw_markers(_self_renderer, gc, _marker_path, _marker_trans, path, trans, rgbFace=None):
                """
                Custom draw method for markers on the line.

                Args:
                    self_renderer: Renderer for the markers.
                    gc: Graphics context.
                    marker_path: The path of the marker.
                    _marker_trans: (Unused) Transformation for the marker path.
                    path: Path for the line.
                    trans: Transformation for the path.
                    rgbFace: Fill color for the marker.
                """
                # Get the drawn path for determining the rotation angle
                # pylint: disable=protected-access
                line_vertices = self_line._get_transformed_path().get_fully_transformed_path().vertices
                # pylint: enable=protected-access
                vertices = path.vertices

                if len(vertices) == 1:
                    line_set = [[to_marker_style(line.get_marker()), vertices]]
                else:
                    if rotate_marker:
                        dx, dy = np.array(line_vertices[-1]) - np.array(line_vertices[-2])
                        end_rot = to_marker_style(end)
                        end_rot._transform += Affine2D().rotate(np.arctan2(dy, dx) - np.pi / 2)
                    else:
                        end_rot = to_marker_style(end)

                    if len(vertices) == 2:
                        line_set = [[start, vertices[0:1]], [end_rot, vertices[1:2]]]
                    else:
                        line_set = [
                            [start, vertices[0:1]],
                            [to_marker_style(line.get_marker()), vertices[1:-1]],
                            [end_rot, vertices[-1:]],
                        ]

                for marker, points in line_set:
                    marker = to_marker_style(marker)  # Ensure it's a MarkerStyle
                    transform = marker.get_transform() + Affine2D().scale(self_line.get_markersize())
                    old_draw_markers(gc, marker.get_path(), transform, Path(points), trans, rgbFace)

            old_draw_markers = renderer.draw_markers
            renderer.draw_markers = MethodType(new_draw_markers, renderer)
            old_draw(renderer)
            renderer.draw_markers = old_draw_markers

        # Validate default marker
        default_marker = to_marker_style(line.get_marker())
        if default_marker:
            start = to_marker_style(start)
            end = to_marker_style(end)

            if rotate_marker is None:
                rotate_marker = self._get_key("plot.marker.rotate")

            old_draw = line.draw
            line.draw = MethodType(new_draw, line)
            line.markers_hacked = True

    def _add_gridline(self, ps, p0, p1, arc_type, **kwargs):
        """
        Add a gridline to the Smith chart for the specified arc_type.

        This method creates and adds a gridline (real or imaginary) as a `matplotlib.lines.Line2D`
        object. Gridlines for the real axis are vertical lines (circles for constant resistance),
        while gridlines for the imaginary axis are horizontal lines (circles for constant reactance).

        For `arc_type='real'`, the gridline is drawn as a vertical line at the position `ps`.
        The start and end points of the line are defined by `p0` and `p1`.

        For `arc_type='imag'`, the gridline is drawn as a horizontal line at the position `ps`.
        The line spans between `p0` and `p1`.

        The `_interpolation_steps` property is set for efficient rendering,
        distinguishing between "x_gridline" and "y_gridline" types.

        Args:
            ps (float): The axis value for the gridline:
                - For `arc_type='real'`, this represents the resistance value.
                - For `arc_type='imag'`, this represents the reactance value.
            p0 (float): The start point of the gridline.
            p1 (float): The end point of the gridline.
            arc_type (str): The type of gridline to add. Must be either:
                - `'real'`: Gridline for the real axis (constant resistance).
                - `'imag'`: Gridline for the imaginary axis (constant reactance).
            **kwargs:
                Additional keyword arguments passed to the `matplotlib.lines.Line2D`
                constructor. These can be used to customize the gridline's appearance
                (e.g., color, linestyle, linewidth).
        """
        assert arc_type in ["real", "imag"]

        if arc_type == "real":
            assert ps >= 0
            line = Line2D(2 * [ps], [p0, p1], **kwargs)
            line.get_path()._interpolation_steps = "x_gridline"
        else:
            assert 0 <= p0 < p1
            line = Line2D([p0, p1], 2 * [ps], **kwargs)
            if abs(ps) > EPSILON:
                line.get_path()._interpolation_steps = "y_gridline"

        return self.add_artist(line)

    class MoebiusTransform(Transform):
        """
        Transform points and paths into Smith chart data space.

        This class implements the Möbius transformation required to map Cartesian
        coordinates to the Smith chart's complex data space. It supports point transformations
        and path transformations for visualizing data on the Smith chart.

        Attributes:
            input_dims (int): The number of input dimensions (always 2).
            output_dims (int): The number of output dimensions (always 2).
            is_separable (bool): Whether the transform is separable (always False).
        """

        input_dims = 2
        output_dims = 2
        is_separable = False

        def __init__(self, axes):
            """
            Initialize the Möbius transformation.

            Args:
                axes (SmithAxes): The Smith chart axes to which the transformation applies.

            Raises:
                AssertionError: If the provided axes is not an instance of `SmithAxes`.
            """
            assert isinstance(axes, SmithAxes)
            Transform.__init__(self)
            self._axes = axes

        def transform_non_affine(self, values):
            """
            Apply the non-affine Möbius transformation to input data.

            Args:
                data (array-like): The input data to transform. Can be a single point
                    (x, y) or an iterable of points.

            Returns:
                list or tuple: The transformed points in Smith chart data space.
            """

            def moebius_xy(_xy):
                return z_to_xy(self._axes.moebius_z(*_xy))

            if isinstance(values[0], Iterable):
                return list(map(moebius_xy, values))
            return moebius_xy(values)

        def transform_path_non_affine(self, path):
            """
            Transform a path using the Möbius transformation.

            This uses path._interpolation identify if the is a x or y gridline.

            This method generates arcs based on the Möbius transformation.

            The method supports linear interpolation (linetype=1) for non-gridline paths.

            Args:
                path (matplotlib.path.Path): The input path to transform.

            Returns:
                matplotlib.path.Path: The transformed path in Smith chart data space.
            """
            vertices = path.vertices
            codes = path.codes

            linetype = path._interpolation_steps
            if linetype in ["x_gridline", "y_gridline"]:
                assert len(vertices) == 2

                x, y = np.array(list(zip(*vertices)))
                z = self._axes.moebius_z(x, y)

                if linetype == "x_gridline":
                    assert x[0] == x[1]
                    zm = 0.5 * (1 + self._axes.moebius_z(x[0]))
                else:
                    assert y[0] == y[1]
                    if self._axes._normalize:
                        scale = 1j
                    else:
                        scale = 1j * self._axes._get_key("axes.impedance")
                    zm = 1 + scale / y[0]

                d = 2 * abs(zm - 1)
                ang0, ang1 = np.angle(z - zm, deg=True) % 360

                reverse = ang0 > ang1
                if reverse:
                    ang0, ang1 = ang1, ang0

                arc = Arc(
                    z_to_xy(zm),
                    d,
                    d,
                    theta1=ang0,
                    theta2=ang1,
                    transform=self._axes.transMoebius,
                )
                arc._path = Path.arc(ang0, ang1)  # fix for Matplotlib 2.1+
                arc_path = arc.get_patch_transform().transform_path(arc.get_path())

                if reverse:
                    new_vertices = arc_path.vertices[::-1]
                else:
                    new_vertices = arc_path.vertices

                new_codes = arc_path.codes
            elif linetype == 1:
                new_vertices = self.transform_non_affine(vertices)
                new_codes = codes
            else:
                raise NotImplementedError("Value for 'path_interpolation' cannot be interpreted.")

            return Path(new_vertices, new_codes)

        def inverted(self):
            """
            Return the inverse Möbius transformation.

            This method provides the inverse transformation for mapping points or paths
            back from the Smith chart's data space to Cartesian coordinates.

            Returns:
                SmithAxes.InvertedMoebiusTransform: The inverted transformation instance.

            Example:
                >>> transform = MoebiusTransform(axes)
                >>> inverted_transform = transform.inverted()
            """
            return SmithAxes.InvertedMoebiusTransform(self._axes)

    class InvertedMoebiusTransform(Transform):
        """
        Perform the inverse transformation for points and paths in Smith chart data space.

        This class implements the inverse Möbius transformation, which maps points and paths
        from the Smith chart's data space back to Cartesian coordinates. It is typically used
        as the inverse of the `MoebiusTransform` class.

        Attributes:
            input_dims (int): The number of input dimensions (always 2).
            output_dims (int): The number of output dimensions (always 2).
            is_separable (bool): Whether the transform is separable (always False).
        """

        input_dims = 2
        output_dims = 2
        is_separable = False

        def __init__(self, axes):
            """
            Initialize the inverse Möbius transformation.

            Args:
                axes (SmithAxes): The Smith chart axes associated with this transformation.

            Raises:
                AssertionError: If the provided `axes` is not an instance of `SmithAxes`.
            """
            assert isinstance(axes, SmithAxes)
            Transform.__init__(self)
            self._axes = axes

        def transform_non_affine(self, values):
            """
            Apply the non-affine inverse Möbius transformation to input data.

            Args:
                values (array-like):
                    The input data to transform, given as a list of (x, y) points.

            Returns:
                list: The transformed points, mapped from the Smith chart data space
                back to Cartesian coordinates.
            """

            def _moebius_inv_xy(_xy):
                return z_to_xy(self._axes.moebius_inv_z(*_xy))

            return list(map(_moebius_inv_xy, values))

        def inverted(self):
            """
            Return the forward Möbius transformation.

            This method provides the forward Möbius transformation to map points
            from Cartesian coordinates to Smith chart data space.

            Returns:
                SmithAxes.MoebiusTransform: The forward Möbius transformation instance.

            Example:
                >>> inverted_transform = InvertedMoebiusTransform(axes)
                >>> forward_transform = inverted_transform.inverted()
            """
            return SmithAxes.MoebiusTransform(self._axes)

    class PolarTranslateInverse(Transform):
        """
        Inverse transformation for `PolarTranslate`.

        This class reverses the effect of the radial translation applied by `PolarTranslate`.

        Attributes:
            input_dims (int): The number of input dimensions (always 2).
            output_dims (int): The number of output dimensions (always 2).
            is_separable (bool): Whether the transform is separable (always False).

        Args:
            axes (SmithAxes):
                The parent `SmithAxes` instance used for coordinate reference.
            pad (float):
                The radial distance to translate points inward toward the center.
            font_size (float):
                Additional y-axis translation, calculated as 0.5 * `font_size`.
        """

        input_dims = 2
        output_dims = 2
        is_separable = False

        def __init__(self, axes, pad, font_size):
            """
            Initialize the inverse polar translation transformation.

            Args:
                axes (SmithAxes):
                    The parent `SmithAxes` instance.
                pad (float):
                    The radial distance to translate points inward toward the center.
                font_size (float):
                    The font size used to calculate additional y-axis translation.
            """
            super().__init__(shorthand_name=None)
            self.axes = axes
            self.pad = pad
            self.font_size = font_size

        def transform_non_affine(self, values):
            """
            Apply the non-affine inverse polar translation transformation.

            Args:
                xy (array-like):
                    A single point (x, y) or a list of points to transform.

            Returns:
                list or tuple:
                    The transformed points, translated inward toward the center.
            """

            def _inverse_translate(_xy):
                x, y = _xy
                ang = np.angle(complex(x - x0, y - y0))
                return x - np.cos(ang) * self.pad, y - np.sin(ang) * (self.pad + 0.5 * self.font_size)

            # Get the center of the Smith chart in display coordinates
            x0, y0 = self.axes.transAxes.transform([0.5, 0.5])

            if isinstance(values[0], Iterable):
                return list(map(_inverse_translate, values))
            return _inverse_translate(values)

        def inverted(self):
            """
            Return the forward transformation (`PolarTranslate`).

            Returns:
                PolarTranslate:
                    The forward transformation.
            """
            return PolarTranslate(self.axes, self.pad, self.font_size)  # pylint: disable=undefined-variable

    class PolarTranslate(Transform):
        """
        Transformation for translating points radially outward from the center of the Smith chart.

        This transformation moves points away from the center of the Smith chart (typically at [0.5, 0.5]
        in axis coordinates) by a specified padding distance. The y-coordinate translation includes an
        additional adjustment based on the font size.

        Attributes:
            input_dims (int): The number of input dimensions (always 2).
            output_dims (int): The number of output dimensions (always 2).
            is_separable (bool): Whether the transform is separable (always False).

        Args:
            axes (SmithAxes):
                The parent `SmithAxes` instance used for coordinate reference.
            pad (float):
                The radial distance to translate points outward from the center.
            font_size (float):
                Additional y-axis translation, calculated as 0.5 * `font_size`.
        """

        input_dims = 2
        output_dims = 2
        is_separable = False

        def __init__(self, axes, pad, font_size):
            """
            Initialize the polar translation transformation.

            Args:
                axes (SmithAxes):
                    The parent `SmithAxes` instance.
                pad (float):
                    The radial distance to translate points outward from the center.
                font_size (float):
                    The font size used to calculate additional y-axis translation.
            """
            super().__init__(shorthand_name=None)
            self.axes = axes
            self.pad = pad
            self.font_size = font_size

        def transform_non_affine(self, values):
            """
            Apply the non-affine polar translation transformation.

            This method translates points radially outward from the center of the Smith chart by a
            specified padding distance. For the y-axis, an additional shift proportional to the font
            size is applied.

            The center of the Smith chart is assumed to be at [0.5, 0.5] in axis coordinates.
            For the y-coordinate, the translation is `pad + 0.5 * font_size`.

            Args:
                values (array-like):
                    A single point (x, y) or a list of points to transform.

            Returns:
                list or tuple:
                    The transformed points, translated outward from the center.
            """

            def _translate(_xy):
                x, y = _xy
                ang = np.angle(complex(x - x0, y - y0))
                return x + np.cos(ang) * self.pad, y + np.sin(ang) * (self.pad + 0.5 * self.font_size)

            # Get the center of the Smith chart in display coordinates
            x0, y0 = self.axes.transAxes.transform([0.5, 0.5])

            if isinstance(values[0], Iterable):
                return list(map(_translate, values))
            return _translate(values)

        # pylint: disable=undefined-variable
        def inverted(self):
            """
            Return the inverse transformation.

            The inverse transformation moves points radially inward toward the center of the Smith chart,
            reversing the effect of the outward translation applied by this transformation.

            Returns:
                PolarTranslateInverse:
                    An instance of the inverse transformation.
            """
            return PolarTranslateInverse(self.axes, self.pad, self.font_size)
        # pylint: enable=undefined-variable

    class RealMaxNLocator(Locator):
        """
        Locator for the real axis of a Smith chart.

        This class generates evenly spaced, nicely rounded tick values for the real axis
        of a Smith chart. It ensures that the transformed center value is always included
        and that the tick spacing remains consistent and visually appealing.

        Attributes:
            steps (int): The maximum number of divisions for the tick values.
            precision (int): The maximum number of significant decimals for tick rounding.
            ticks (list or None): Cached tick values, computed on demand.
            axes (SmithAxes): The parent `SmithAxes` instance for reference.

        Args:
            axes (SmithAxes):
                The parent Smith chart axes to which this locator applies.
            n (int):
                The maximum number of divisions for the real axis.
            precision (int, optional):
                The maximum number of significant decimals for tick rounding. If not provided,
                the value is retrieved from `axes._get_key("grid.locator.precision")`.
        """

        def __init__(self, axes, n, precision=None):
            """
            Initialize the RealMaxNLocator.

            Args:
                axes (SmithAxes):
                    The parent Smith chart axes to which this locator applies.
                n (int):
                    The maximum number of divisions for the real axis.
                precision (int, optional):
                    The maximum number of significant decimals for tick rounding. If not provided,
                    the value is retrieved from `axes._get_key("grid.locator.precision")`.

            Raises:
                AssertionError: If `axes` is not an instance of `SmithAxes`, if `n <= 0`,
                    or if `precision` is not greater than 0.
            """
            assert isinstance(axes, SmithAxes)
            assert n > 0

            Locator.__init__(self)
            self.steps = n
            self.precision = precision or axes._get_key("grid.locator.precision")
            assert self.precision > 0

            self.ticks = None
            self.axes = axes

        def __call__(self):
            """Compute or return cached tick values."""
            if self.ticks is None:
                self.ticks = self.tick_values(0, self.axes._inf)
            return self.ticks

        def nice_round(self, num, down=True):
            """
            Round a number to a nicely rounded value based on precision.

            The rounding behavior adapts dynamically to ensure ticks are visually
            consistent across different scales.

            Args:
                num (float): The number to round.
                down (bool, optional): Whether to round down. Defaults to `True`.

            Returns: A nicely rounded value.
            """
            exp = np.ceil(np.log10(np.abs(num) + EPSILON))
            if exp < 1:  # Fix for leading 0
                exp += 1
            norm = 10 ** -(exp - self.precision)

            num_normed = num * norm
            if num_normed < 3.3:
                norm *= 2
            elif num_normed > 50:
                norm /= 10

            if not 1 < num_normed % 10 < 9:
                if abs(num_normed % 10 - 1) < EPSILON:
                    num -= 0.5 / norm
                f_round = np.round
            else:
                f_round = np.floor if down else np.ceil

            return f_round(np.round(num * norm, 1)) / norm

        def tick_values(self, vmin, vmax):
            """
            Compute the tick values for the real axis.

            Includes the center value as a mandatory tick and dynamically
            adjusts spacing to ensure evenly distributed ticks.

            Args:
                vmin (float): The minimum value of the axis.
                vmax (float): The maximum value of the axis.

            Returns: he computed tick values for the real axis.
            """
            tmin, tmax = self.transform(vmin), self.transform(vmax)
            mean = self.transform(self.nice_round(self.invert(0.5 * (tmin + tmax))))

            result = [tmin, tmax, mean]
            d0 = abs(tmin - tmax) / (self.steps + 1)
            for sgn, side, end in [[1, False, tmax], [-1, True, tmin]]:
                d, d0 = d0, None
                last = mean
                while True:
                    new = last + d * sgn
                    if self.out_of_range(new) or abs(end - new) < d / 2:
                        break
                    new = self.transform(self.nice_round(self.invert(new), side))
                    d = abs(new - last)
                    if d0 is None:
                        d0 = d
                    last = new
                    result.append(last)

            return np.sort(self.invert(np.array(result)))

        def out_of_range(self, x):
            """Check if a value is outside the valid range for the real axis."""
            return abs(x) > 1

        def transform(self, x):
            """Apply the Möbius transformation to a value."""
            return self.axes.moebius_z(x)

        def invert(self, x):
            """Apply the inverse Möbius transformation to a value."""
            return self.axes.moebius_inv_z(x)

    class ImagMaxNLocator(RealMaxNLocator):
        """
        Locator for the imaginary axis of a Smith chart.

        This class generates evenly spaced, nicely rounded tick values for the imaginary
        axis of a Smith chart. It extends the `RealMaxNLocator` class and adapts it for
        handling reactance values.

        Attributes:
            steps (int): The maximum number of divisions for the imaginary axis, derived
                from half the divisions (`n`) of the parent locator.
            precision (int): The maximum number of significant decimals for tick rounding.
            ticks (list or None): Cached tick values, computed on demand.
            axes (SmithAxes): The parent `SmithAxes` instance for reference.

        Args:
            axes (SmithAxes):
                The parent Smith chart axes to which this locator applies.
            n (int):
                The maximum number of divisions for the imaginary axis. This value is divided
                by 2 for internal calculations.
            precision (int, optional):
                The maximum number of significant decimals for tick rounding. If not provided,
                the value is retrieved from `axes._get_key("grid.locator.precision")`.
        """

        def __init__(self, axes, n, precision=None):
            """
            Initialize the ImagMaxNLocator.

            Args:
                axes (SmithAxes):
                    The parent Smith chart axes to which this locator applies.
                n (int):
                    The maximum number of divisions for the imaginary axis. Internally,
                    this value is divided by 2 for tick calculations.
                precision (int, optional):
                    The maximum number of significant decimals for tick rounding. If not
                    provided, the value is retrieved from `axes._get_key("grid.locator.precision")`.
            """
            SmithAxes.RealMaxNLocator.__init__(self, axes, n // 2, precision)

        def __call__(self):
            """Compute or return cached tick values for the imaginary axis."""
            if self.ticks is None:
                tmp = self.tick_values(0, self.axes._inf)
                self.ticks = np.concatenate((-tmp[:0:-1], tmp))
            return self.ticks

        def out_of_range(self, x):
            """Check if a value is outside the valid range for the imaginary axis."""
            return not 0 <= x <= np.pi

        def transform(self, x):
            """Apply the Möbius transformation to a value on the imaginary axis."""
            return np.pi - np.angle(self.axes.moebius_z(x * 1j))

        def invert(self, x):
            """Apply the inverse Möbius transformation to a value."""
            return np.imag(-self.axes.moebius_inv_z(ang_to_c(np.pi + np.array(x))))

    class SmithAutoMinorLocator(AutoMinorLocator):
        """
        Automatic minor tick locator for Smith chart axes.

        This locator generates evenly spaced minor ticks between major tick values,
        specifically for use with `SmithAxes`. The number of minor ticks between
        major ticks can be customized.

        Attributes:
            ndivs (int): The number of intermediate ticks between major tick intervals.
            _ticks (numpy.ndarray or None): Cached array of computed minor tick values.

        Args:
            n (int, optional):
                The number of intermediate ticks between major tick values. Must be a positive integer.
                Defaults to 4.
        """

        def __init__(self, n=4):
            """
            Initialize the SmithAutoMinorLocator.

            Args:
                n (int, optional):
                    The number of intermediate ticks between major tick values. Must be a
                    positive integer. Defaults to 4.
            """
            assert isinstance(n, int) and n > 0
            super().__init__(n=n)  # Initialize the base AutoMinorLocator with n divisions
            self._ticks = None  # Cache for minor tick positions

        def tick_values(self, vmin, vmax):
            """
            Calculate minor tick positions within the range [vmin, vmax].

            This method overrides `tick_values` from `AutoMinorLocator` to compute minor
            ticks by interpolating between major tick values.

            Args:
                vmin (float): The minimum data value.
                vmax (float): The maximum data value.

            Returns:
                numpy.ndarray: Array of minor tick positions between vmin and vmax.
            """
            major_ticks = self.axis.get_majorticklocs()  # Retrieve major tick locations
            minor_ticks = []

            # Linearly interpolate minor ticks between each pair of major ticks
            for p0, p1 in zip(major_ticks[:-1], major_ticks[1:]):
                minor_ticks.extend(np.linspace(p0, p1, self.ndivs + 1)[1:-1])

            # Filter minor ticks to ensure they are within the [vmin, vmax] range
            return np.array([tick for tick in minor_ticks if vmin <= tick <= vmax])

        def __call__(self):
            """
            Compute or return cached minor tick values.

            Returns:
                numpy.ndarray: Array of minor tick positions.
            """
            if self._ticks is None:
                vmin, vmax = self.axis.get_view_interval()  # Get visible range
                self._ticks = self.tick_values(vmin, vmax)
            return self._ticks

    class RealFormatter(Formatter):
        """
        Formatter for the real axis of a Smith chart.

        This formatter formats tick values for the real axis by printing numbers
        as floats, removing trailing zeros and unnecessary decimal points.
        Special cases include returning an empty string '' for values near zero.

        Args:
            axes (SmithAxes):
                The parent `SmithAxes` instance associated with this formatter.

        Raises:
            AssertionError: If `axes` is not an instance of `SmithAxes`.

        Example:
            >>> formatter = RealFormatter(axes)
            >>> print(formatter(0.1))  # "0.1"
            >>> print(formatter(0))    # ""
        """

        def __init__(self, axes, *args, **kwargs):
            """
            Initialize the RealFormatter.

            Args:
                axes (SmithAxes):
                    The parent `SmithAxes` instance.
                *args:
                    Additional positional arguments passed to `Formatter`.
                **kwargs:
                    Additional keyword arguments passed to `Formatter`.
            """
            assert isinstance(axes, SmithAxes)
            Formatter.__init__(self, *args, **kwargs)
            self._axes = axes

        def __call__(self, x, pos=None):
            """
            Format the given tick value.

            Args:
                x (float):
                    The tick value to format.
                pos (int, optional):
                    The position of the tick value (ignored in this formatter).

            Returns:
                str: The formatted tick value as a string, or `''` for values near zero.
            """
            if x < EPSILON or x > self._axes._near_inf:
                return ""
            return ("%f" % x).rstrip("0").rstrip(".")

    class ImagFormatter(RealFormatter):
        """
        Formatter for the imaginary axis of a Smith chart.

        This formatter formats tick values for the imaginary axis by printing numbers
        as floats, removing trailing zeros and unnecessary decimal points, and appending
        "j" to indicate imaginary values. Special cases include:
            - `''` (empty string) for negative infinity.
            - `'symbol.infinity'` from `scParams` for positive infinity.
            - `'0'` for values near zero, ensuring `-0` is not displayed.

        Args:
            axes (SmithAxes):
                The parent `SmithAxes` instance associated with this formatter.
        """

        def __call__(self, x, pos=None):
            """
            Format the given tick value for the imaginary axis.

            Args:
                x (float):
                    The tick value to format.
                pos (int, optional):
                    The position of the tick value (ignored in this formatter).

            Returns:
                str: The formatted tick value as a string, with special handling for:
                    - `''` (empty string) for negative infinity.
                    - `'∞'` (UTF-8 infinity symbol) for positive infinity.
                    - `'0'` for values near zero.
                    - Appended "j" for imaginary values.
            """
            if x < -self._axes._near_inf:
                return ""
            if x > self._axes._near_inf:
                return self._axes._get_key("symbol.infinity")  # UTF-8 infinity symbol
            if abs(x) < EPSILON:
                return "0"
            return ("%f" % x).rstrip("0").rstrip(".") + "j"
