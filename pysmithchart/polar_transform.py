"""This module contains the implementation for polar transform."""

from collections.abc import Iterable
from matplotlib.transforms import Transform
import numpy as np

__all__ = ["PolarTranslate", "PolarTranslateInverse"]


class BasePolarTransform(Transform):
    """Abstract class to work around circular imports.

    Attributes:
        axes (SmithAxes): The parent `SmithAxes` instance.
        pad (float): The radial distance to translate points inward toward the center.
        font_size (float): The font size used to calculate additional y-axis translation.
    """

    #: The number of input dimensions (always 2).
    input_dims = 2
    #: The number of output dimensions (always 2).
    output_dims = 2
    #: Whether the transform is separable (always False).
    is_separable = False

    def __init__(self, axes, pad, font_size, *args, **kwargs):
        """Initialize the inverse polar translation transformation."""
        super().__init__(*args, **kwargs)
        self.axes = axes
        self.pad = pad
        self.font_size = font_size

    def inverted(self):
        """To be implemented in subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")


class PolarTranslateInverse(BasePolarTransform):
    """
    Inverse transformation for `PolarTranslate`.

    This class reverses the effect of the radial translation applied by `PolarTranslate`.
    """

    def transform_non_affine(self, values):
        """
        Apply the non-affine inverse polar translation transformation.

        Args:
            values (array-like):
                A single point (x, y) or a list of points to transform.

        Returns:
            list or tuple:
                The transformed points, translated inward toward the center.
        """

        def _inverse_translate(_xy):
            x, y = _xy
            ang = np.angle(complex(x - x0, y - y0))
            return (
                x - np.cos(ang) * self.pad,
                y - np.sin(ang) * (self.pad + 0.5 * self.font_size),
            )

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
        return PolarTranslate(self.axes, self.pad, self.font_size)


class PolarTranslate(BasePolarTransform):
    """
    Transformation for translating points radially outward from the center of the Smith chart.

    This transformation moves points away from the center of the Smith chart (typically at [0.5, 0.5]
    in axis coordinates) by a specified padding distance. The y-coordinate translation includes an
    additional adjustment based on the font size.
    """

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
            return (
                x + np.cos(ang) * self.pad,
                y + np.sin(ang) * (self.pad + 0.5 * self.font_size),
            )

        x0, y0 = self.axes.transAxes.transform([0.5, 0.5])
        if isinstance(values[0], Iterable):
            return list(map(_translate, values))
        return _translate(values)

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
