from matplotlib.projections import register_projection

from .smithaxes import SmithAxes

# add smith projection to available projections
register_projection(SmithAxes)
