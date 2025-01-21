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
                    z0 = np.where(z0 == "", "0.0", z0.astype(object)).astype(float)
                    z1 = z[1]
                    z1 = np.where(z1 == "", "0.0", z1.astype(object)).astype(float)
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
    z = np.where(z == 1, 1 - EPSILON, z)  # avoid division by 0
    return norm * (1 + z) / (1 - z)


def ang_to_c(ang, radius=1):
    return radius * (np.cos(ang) + np.sin(ang) * 1j)


def lambda_to_rad(lmb):
    return lmb * 4 * np.pi


def rad_to_lambda(rad):
    return rad * 0.25 / np.pi


def split_complex(z):
    return [np.real(z), np.imag(z)]


def vswr_rotation(
    x, y, impedance=1, real=None, imag=None, lambda_rotation=None, solution2=True, direction="clockwise"
):
    """
    Rotates a point `(x, y)` on the Smith chart to a specified destination or orientation.

    This function computes the rotation needed to move a point `p = (x, y)` to a specified destination on 
    the Smith chart. The destination can be defined by matching the real part, the imaginary part, 
    or a specified rotation angle. If no destination is defined, the function computes a full rotation.

    Multiple solutions may exist, and you can specify which solution to use. If no solution exists, 
    a `ValueError` is raised.

    Args:
        x (float): Real part of the input point.
        y (float): Imaginary part of the input point.
        impedance (float, optional): Impedance value for normalization. Defaults to 1.
        real (float, optional): Rotate until the real part of the input matches this value.
            Must be a non-negative float. Defaults to None.
        imag (float, optional): Rotate until the imaginary part of the input matches this value.
            Can be any float. Defaults to None.
        lambda_rotation (float, optional): Specify a fixed rotation angle in terms of wavelengths
            (e.g., 0.25 corresponds to 180 degrees). Defaults to None.
        solution2 (bool, optional): Determines which solution to use when `real` or `imag` is specified:
            - If `real` is set: Selects the solution with a negative imaginary part if `solution2` is True.
            - If `imag` is set: Selects the solution closer to infinity if `solution2` is True.
            Has no effect if `lambda_rotation` is set. Defaults to True.
        direction (str, optional): Rotation direction. Must be one of:
            - `'clockwise'` or `'cw'`: Rotate in the clockwise direction.
            - `'counterclockwise'` or `'ccw'`: Rotate in the counterclockwise direction.
            Defaults to `'clockwise'`.

    Raises:
        ValueError: If:
            - The rotation destination is unreachable.
            - More than one destination is specified (e.g., both `real` and `imag` are set).
            - An invalid `direction` value is provided.

    Returns:
        tuple: A tuple `(z0, z1, lambda_rotation)` containing:
            - `z0 (complex)`: The input point converted to a complex number, `z0 = x + y * 1j`.
            - `z1 (complex)`: The destination point as a complex number after rotation.
            - `lambda_rotation (float)`: The rotation angle in terms of wavelengths (e.g., 0.5 for 180 degrees).

    Notes:
        - If no destination is set (`real`, `imag`, or `lambda_rotation`), a full turn is performed.
        - If multiple destinations are set, a `ValueError` is raised.
    """
    if direction in ["clockwise", "cw"]:
        cw = True
    elif direction in ["counterclockwise", "ccw"]:
        cw = False
    else:
        raise ValueError("Direction must be 'clockwise', 'cw', 'counterclockwise', or 'ccw'")

    # Default cases for rotation angle calculations
    invert = False
    ang_0 = 0.0
    ang = 0.0
    check = 0
    z = x + y * 1j
    z0 = moebius_z(z, impedance)

    if real is not None or imag is not None:
        a = np.abs(z0)

        if real is not None:
            assert real > 0, "Real destination must be positive."
            check += 1

            b = 0.5 * (1 - moebius_z(real, impedance))
            c = 1 - b
            ang_0 = 0

            if real < 0 or abs(moebius_z(real, impedance)) > a:
                raise ValueError("The specified real destination is not reachable.")

            invert = solution2

        if imag is not None:
            check += 1

            b = impedance / imag if imag != 0 else float("inf")
            c = np.sqrt(1 + b**2)
            ang_0 = np.arctan(b)

            if c > a + abs(b):
                raise ValueError("The specified imaginary destination is not reachable.")

            invert = solution2 != (imag < 0)

        gamma = np.arccos((a**2 + c**2 - b**2) / (2 * a * c)) % TWO_PI
        if invert:
            gamma = -gamma
        gamma = (ang_0 + gamma) % TWO_PI

        ang_z = np.angle(z0) % TWO_PI
        ang = (gamma - ang_z) % TWO_PI

        if cw:
            ang -= 2 * np.pi

    if lambda_rotation is not None:
        check += 1
        ang = lambda_to_rad(lambda_rotation)
        if cw:
            ang = -ang

    if check > 1:
        raise ValueError("Too many destinations specified. Specify only one of `real`, `imag`, or `lambda_rotation`.")

    if check == 0:
        ang = TWO_PI

    return (z, moebius_inv_z(z0 * ang_to_c(ang), impedance), rad_to_lambda(ang))
