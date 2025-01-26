"""
This module registers the matplotlib projection "smith".

The `pysmithchart` package provides tools for working with Smith charts, enabling visualization and
analysis of reflection coefficients, impedances, and admittances in RF and microwave engineering.

Modules:
    smithaxes: Defines the `SmithAxes` class, which implements the custom Smith chart projection.

Constants:
    S_PARAMETER: Scattering parameter (S-parameter) type, used for plotting reflection coefficients.
    Z_PARAMETER: Impedance parameter (Z-parameter) type, used for plotting normalized impedances.
    Y_PARAMETER: Admittance parameter (Y-parameter) type, used for plotting normalized admittances.

Public API:
    - SmithAxes: The custom projection class for Smith charts.
    - S_PARAMETER: Constant for S-parameter plotting.
    - Z_PARAMETER: Constant for Z-parameter plotting.
    - Y_PARAMETER: Constant for Y-parameter plotting.

Example:
    Import the module and plot a reflection coefficient using the Smith chart projection:

    >>> import matplotlib.pyplot as plt
    >>> from pysmithchart import Z_PARAMETER
    >>> plt.subplot(1, 1, 1, projection="smith")
    >>> plt.plot([0.5 + 0.3j, -0.2 - 0.1j], 'o', datatype=Z_PARAMETER)
    >>> plt.show()
"""

from matplotlib.projections import register_projection
from .smithaxes import SmithAxes, S_PARAMETER, Z_PARAMETER, Y_PARAMETER

# Register the Smith projection
register_projection(SmithAxes)

# Expose constants in the module-level namespace
S_PARAMETER = S_PARAMETER
Z_PARAMETER = Z_PARAMETER
Y_PARAMETER = Y_PARAMETER

# Public API for wildcard imports
__all__ = ["SmithAxes", "S_PARAMETER", "Z_PARAMETER", "Y_PARAMETER"]
