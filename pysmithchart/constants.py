"""This module contains the implementation for parameter type."""

from enum import Enum
import numpy as np


class ParameterType(Enum):
    """Defines parameter types for use with Smith charts."""

    S_PARAMETER = "S"
    Z_PARAMETER = "Z"
    Y_PARAMETER = "Y"


S_PARAMETER = ParameterType.S_PARAMETER
Z_PARAMETER = ParameterType.Z_PARAMETER
Y_PARAMETER = ParameterType.Y_PARAMETER

INF = 1e9
EPSILON = 1e-7
TWO_PI = 2 * np.pi
