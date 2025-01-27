"""This module contains the implementation for parameter type."""

from enum import Enum


class ParameterType(Enum):
    """Defines parameter types for use with Smith charts."""

    S_PARAMETER = "S"
    Z_PARAMETER = "Z"
    Y_PARAMETER = "Y"


S_PARAMETER = ParameterType.S_PARAMETER
Z_PARAMETER = ParameterType.Z_PARAMETER
Y_PARAMETER = ParameterType.Y_PARAMETER

SC_INFINITY = 1e9
SC_EPSILON = 1e-7
