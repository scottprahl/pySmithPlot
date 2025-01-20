"""
Test basic Smith chart functionality.

This test was forked from https://github.com/schang412/mpl-smithchart

Tests:
------
- `test_plot_point`: Verifies the ability to plot individual points
- `test_plot_s_param`: Tests the plotting of S-parameters on the Smith chart.
- `test_plot_labels`: Ensures plots with labels and legends render correctly.
- `test_plot_normalized_axes`: Normalized and non-normalized axes different impedances.
- `test_plot_grid_styles`: Examines various grid style configurations.
"""

from itertools import product
import os
import numpy as np
import pytest
import matplotlib.pyplot as plt
from pysmithplot import SmithAxes


@pytest.fixture
def start_figure():
    """Fixture to create a Smith chart figure with a subplot."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)
    plt.figure(figsize=(6, 6))
    plt.subplot(1, 1, 1, projection='smith')
    yield chart_dir


def s11_of_cap(freq):
    """Calculate S11 for a capacitor connected to ground."""
    return (1 - 1j * freq * 1e-9) / (1 + 1j * freq * 1e-9)


def s11_of_parallel_cap_res(freq, z0=50):
    """Calculate S11 for a capacitor in parallel with a resistor to ground."""
    s = 2j * np.pi * freq
    return (50 - z0 * (1 + s * 1e-9 * 50)) / (50 + z0 * (1 + s * 1e-9 * 50))


@pytest.mark.parametrize(
    "point",
    (
        200 + 100j,
        50.0,
        50 - 10j,
    ),
)
def test_plot_point(start_figure, point):
    """Test plotting a single point on the Smith chart."""
    chart_dir = start_figure
    plt.plot(point, datatype=SmithAxes.Z_PARAMETER)
    plt.title(f"Plot of a Single Point: {point}")
    plt.savefig(os.path.join(chart_dir, "schang_point.pdf"), format="pdf")


def test_plot_s_param(start_figure):
    """Test plotting S-parameters on the Smith chart."""
    chart_dir = start_figure
    freqs = np.logspace(0, 9, 200)
    s11 = s11_of_cap(freqs)
    plt.plot(s11, markevery=1, datatype=SmithAxes.S_PARAMETER)
    plt.title("S-Parameters of a Capacitor")
    plt.savefig(os.path.join(chart_dir, "schang_s_param.pdf"), format="pdf")


def test_plot_labels(start_figure):
    """Test plotting with labels and a legend."""
    chart_dir = start_figure
    freqs = np.logspace(0, 9, 200)
    s11 = s11_of_cap(freqs)
    plt.plot(s11, markevery=1, datatype=SmithAxes.S_PARAMETER, label="s11")
    plt.legend()
    plt.title("S-Parameters with Labels and Legend")
    plt.savefig(os.path.join(chart_dir, "schang_labels.pdf"), format="pdf")


def test_plot_normalized_axes(start_figure):
    """Test plotting with normalized and non-normalized axes."""
    chart_dir = start_figure
    freqs = np.logspace(0, 9, 200)
    plt.figure(figsize=(18, 12)).set_layout_engine("tight")

    for i, (do_normalize_axes, impedance) in enumerate(product([True, False], [10, 50, 200])):
        s11 = s11_of_parallel_cap_res(freqs, z0=impedance)
        plt.subplot(
            2, 3, i + 1,
            projection='smith',
            axes_impedance=impedance,
            axes_normalize=do_normalize_axes,
        )
        plt.plot(s11)
        plt.title(f"Impedance: {impedance} Ω — Normalized: {do_normalize_axes}")

    plt.suptitle("Normalized vs. Non-Normalized Axes")
    plt.savefig(os.path.join(chart_dir, "schang_normalized_axes.pdf"), format="pdf")


def test_plot_grid_styles(start_figure):
    """Test plotting with various grid styles."""
    chart_dir = start_figure
    freqs = np.logspace(0, 9, 200)
    s11 = s11_of_parallel_cap_res(freqs)
    plt.figure(figsize=(18, 12)).set_layout_engine("tight")

    offset = 0
    for i, (major_fancy, minor_enable, minor_fancy) in enumerate(
        product(
            [True, False],
            [True, False],
            [True, False],
        ),
    ):
        if not minor_enable and minor_fancy:
            offset += 1
            continue
        plt.subplot(
            2, 3, i + 1 - offset,
            projection='smith',
            grid_major_fancy=major_fancy,
            grid_minor_enable=minor_enable,
            grid_minor_fancy=minor_fancy,
        )
        major_str = "fancy" if major_fancy else "standard"
        minor_str = "off" if not minor_enable else ("fancy" if minor_fancy else "standard")
        plt.plot(s11)
        plt.title(f"Major Grid: {major_str}, Minor Grid: {minor_str}")

    plt.suptitle("Grid Style Variations")
    plt.savefig(os.path.join(chart_dir, "schang_grid_styles.pdf"), format="pdf")
