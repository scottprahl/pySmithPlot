from collections.abc import Iterable
import numpy as np

INF = 1e9
EPSILON = 1e-7
TWO_PI = 2 * np.pi

def cs(z, N=5):
    """Convert complex number to string for printing."""
    if z.imag < 0:
        form = "(%% .%df - %%.%dfj)" % (N, N)
    else:
        form = "(%% .%df + %%.%dfj)" % (N, N)
    return form % (z.real, abs(z.imag))


def to_float(value):
    if isinstance(value, (int, np.integer, np.unsignedinteger)):
        return float(value)
    return value

def xy_to_z(*xy):
    """
    Converts input arguments representing either complex numbers or separate real and imaginary components into a complex number or array of complex numbers.

    Parameters
    ----------
    *xy : tuple
        - If a single argument is passed:
            - If the argument is a complex number or an array-like of complex numbers, it is returned as-is.
            - If the argument is an iterable with two rows (e.g., shape `(2, N)`), it is interpreted as real and imaginary parts, and a complex array is returned.
            - If the argument has more than two dimensions, a `ValueError` is raised.
        - If two arguments are passed:
            - The first argument represents the real part (`x`), and the second represents the imaginary part (`y`).
            - Both arguments must be scalars or iterable objects of the same size. If they are iterable, they are combined to form a complex array.
            - If the sizes of `x` and `y` do not match, a `ValueError` is raised.

    Returns
    -------
    z : complex or numpy.ndarray
        The complex number or array of complex numbers created from the input.
    """
    if len(xy) == 1:
        z = xy[0]
        if isinstance(z, Iterable):
            z = np.array(z)
            if len(z.shape) == 2:
                if z.shape[0] == 2:  # Ensure the first dimension has size 2
                    z0 = z[0]  # handle case when line.get_data() returns [['0.0'],['']]
                    z0 = np.where(z0 == '', '0.0', z0.astype(object)).astype(float)
                    z1 = z[1]
                    z1= np.where(z1 == '', '0.0', z1.astype(object)).astype(float)
                    z = z0 + 1j * z1
                else:
                    raise ValueError("Input array must have shape (2, N) for 2D arrays.")
            elif len(z.shape) > 2:
                raise ValueError("Input array has too many dimensions.")
    elif len(xy) == 2:
        x, y = xy
        if isinstance(x, Iterable):
            x = np.array(x)
            y = np.array(y)
            if len(x) == len(y):
                z = x + 1j * y
            else:
                raise ValueError("x and y vectors don't match in type and/or size.")
        else:
            z = float(x) + 1j * float(y)  # Cast scalars to float
    else:
        raise ValueError(
            "Arguments are not valid - specify either complex number/vector z or real and imaginary number/vector x, y"
        )

    return z


def z_to_xy(z):
    """Convert complex to pair of real numbers."""
    return z.real, z.imag


def moebius_z(*args, norm):
    """
    Computes the Möbius transformation of the input, typically used in Smith chart computations.

    Parameters
    ----------
    *args : tuple
        Input arguments passed to the `xy_to_z` function:
        - A single complex number or an iterable representing complex values.
        - Two arguments representing the real and imaginary parts of a complex number or array of complex numbers.
        Refer to `xy_to_z` for detailed input handling.

    norm : float
        The normalization constant used in the Möbius transformation.  Typically 50Ω

    Returns
    -------
    transformed_z : complex or numpy.ndarray
        The Möbius-transformed complex number or array of complex numbers.
    """
    z = xy_to_z(*args)
    return 1 - 2 * norm / (z + norm)


def moebius_inv_z(*args, norm):
    """
    Computes the inverse Möbius transformation of the input, typically used in Smith chart computations.

    Parameters
    ----------
    *args : tuple
        Input arguments passed to the `xy_to_z` function:
        - A single complex number or an iterable representing complex values.
        - Two arguments representing the real and imaginary parts of a complex number or array of complex numbers.
        Refer to `xy_to_z` for detailed input handling.

    norm : float
        The normalization constant used in the inverse Möbius transformation.  Typically 50Ω

    Returns
    -------
    inverse_transformed_z : complex or numpy.ndarray
        The inverse Möbius-transformed complex number or array of complex numbers.
    """
    z = xy_to_z(*args)
    z = np.where(z==1, 1-EPSILON, z)  # avoid division by 0
    return norm * (1 + z) / (1 - z)


def ang_to_c(ang, radius=1):
    return radius * (np.cos(ang) + np.sin(ang) * 1j)


def lambda_to_rad(lmb):
    return lmb * 4 * np.pi


def rad_to_lambda(rad):
    return rad * 0.25 / np.pi
