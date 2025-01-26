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
