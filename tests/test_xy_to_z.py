import numpy as np
import pytest
from collections.abc import Iterable
from pysmithchart.smithhelper import xy_to_z

def test_single_complex_number():
    """Test a single complex number input."""
    assert xy_to_z(3 + 4j) == 3 + 4j

def test_single_iterable_of_complex_numbers():
    """Test a single iterable of complex numbers."""
    assert np.array_equal(
        xy_to_z([1 + 2j, 3 + 4j]),
        np.array([1 + 2j, 3 + 4j])
    )

def test_iterable_with_two_rows():
    """Test an iterable with two rows representing real and imaginary parts."""
    assert np.array_equal(
        xy_to_z([[1, 2, 3], [4, 5, 6]]),
        np.array([1 + 4j, 2 + 5j, 3 + 6j])
    )

def test_iterable_with_two_rows_integers():
    """Test an iterable with two rows of integers."""
    assert np.array_equal(
        xy_to_z([[1, 2, 3], [4, 5, 6]]),
        np.array([1 + 4j, 2 + 5j, 3 + 6j])
    )

def test_invalid_shape():
    """Test input with more than two dimensions."""
    with pytest.raises(ValueError, match="Input array has too many dimensions."):
        xy_to_z(np.zeros((3, 3, 3)))

def test_two_arguments_scalars():
    """Test two scalar arguments."""
    assert xy_to_z(3, 4) == 3 + 4j

def test_two_arguments_iterables():
    """Test two iterables with matching lengths."""
    assert np.array_equal(
        xy_to_z([1, 2, 3], [4, 5, 6]),
        np.array([1 + 4j, 2 + 5j, 3 + 6j])
    )

def test_two_arguments_iterables_integers():
    """Test two iterables of integers with matching lengths."""
    assert np.array_equal(
        xy_to_z([1, 2, 3], [4, 5, 6]),
        np.array([1 + 4j, 2 + 5j, 3 + 6j])
    )

def test_two_arguments_mismatched_lengths():
    """Test two iterables with mismatched lengths."""
    with pytest.raises(ValueError, match="x and y vectors don't match in type and/or size"):
        xy_to_z([1, 2], [3, 4, 5])

def test_invalid_number_of_arguments():
    """Test invalid number of arguments."""
    with pytest.raises(ValueError, match="Arguments are not valid"):
        xy_to_z(1, 2, 3)

def test_empty_input():
    """Test empty input."""
    with pytest.raises(ValueError, match="Arguments are not valid"):
        xy_to_z()

def test_single_empty_iterable():
    """Test a single empty iterable."""
    assert np.array_equal(xy_to_z([]), np.array([]))

def test_weird_zero():
    """Test weird value from line.get_data()."""
    assert np.array_equal(
        xy_to_z([[0.0],['']]), np.array([0.0+0.0j]))

