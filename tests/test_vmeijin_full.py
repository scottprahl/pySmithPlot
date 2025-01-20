import os
import shutil
import pytest
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pysmithplot.smithaxes import SmithAxes
from pysmithplot import smithhelper

# Configure Matplotlib settings
rcParams.update({"legend.numpoints": 3, "axes.axisbelow": True})


@pytest.fixture
def setup_environment(tmp_path):
    """Fixture to set up the test environment."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path11 = os.path.join(script_dir, "data/s11.csv")
    data = load_complex_data(data_path11)

    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)
    return data, chart_dir

def load_complex_data(file_path, step=40):
    """
    Load and process complex data from a CSV file.

    Parameters
    ----------
    file_path : str
        Path to the CSV file containing the data.
    step : int, optional
        Step size for slicing the data (default is 40).

    Returns
    -------
    numpy.ndarray
        Processed complex data as a 1D numpy array.
    """
    data = np.loadtxt(file_path, delimiter=",", skiprows=1)[::step]
    return data[:, 1] + 1j * data[:, 2]

def plot_example(title, sp_data, z_data, **kwargs):
    """Helper function to plot examples."""
    kwargs.setdefault("markevery", 1)
    plt.plot(smithhelper.moebius_inv_z(sp_data, norm=50), datatype="Z", **kwargs)
    plt.plot(z_data, datatype="Z", **kwargs)
    plt.plot(100, datatype="Z", **kwargs)
    plt.plot(25 + 25j, datatype="Z", **kwargs)
    plt.title(title)


def save_figure(chart_dir, test_name):
    """Helper function to save figures in multiple formats."""
    for ext in ["pdf", "png"]:
        plt.savefig(
            os.path.join(chart_dir, f"{test_name.lower().replace(' ', '_')}.{ext}"),
            format=ext,
        )
    plt.close()


def test_grid_styles(setup_environment):
    """Test for various grid styles."""
    sp_data, chart_dir = setup_environment
    z_data = sp_data * 50

    fig = plt.figure(figsize=(18, 12))
    fig.set_layout_engine("tight")
    i = 0
    for major_fancy in [False, True]:
        for minor in [False, True]:
            for minor_fancy in [False, True]:
                if minor or not minor_fancy:
                    i += 1
                    plt.subplot(
                        2, 3, i, projection="smith",
                        grid_major_fancy=major_fancy,
                        grid_minor_enable=minor,
                        grid_minor_fancy=minor_fancy,
                    )
                    major_str = "fancy" if major_fancy else "standard"
                    minor_str = "off" if not minor else "fancy" if minor_fancy else "standard"
                    plot_example(f"Major: {major_str} - Minor: {minor_str}", sp_data, z_data)

    save_figure(chart_dir, "grid_styles")


def test_fancy_grids(setup_environment):
    """Test for fancy grids with various thresholds."""
    sp_data, chart_dir = setup_environment
    z_data = sp_data * 50

    fig = plt.figure(figsize=(18, 12))
    fig.set_layout_engine("tight")
    i = 0
    for threshold in [(50, 50), (100, 50), (125, 100)]:
        i += 1
        plt.subplot(2, 3, i, projection="smith", grid_major_fancy_threshold=threshold)
        plot_example(f"Major Threshold=({threshold[0]}, {threshold[1]})", sp_data, z_data)

    for threshold in [15, 30, 60]:
        i += 1
        plt.subplot(
            2, 3, i, projection="smith",
            grid_minor_fancy=True,
            grid_minor_enable=True,
            grid_minor_fancy_threshold=threshold,
        )
        plot_example(f"Minor Threshold={threshold}", sp_data, z_data)

    save_figure(chart_dir, "fancy_grids")


def test_grid_locators(setup_environment):
    """Test for grid locators with varying step counts."""
    sp_data, chart_dir = setup_environment
    z_data = sp_data * 50

    fig = plt.figure(figsize=(24, 12))
    fig.set_layout_engine("tight")
    i = 0
    for num in [5, 8, 14, 20]:
        i += 1
        plt.subplot(2, 4, i, projection="smith", grid_major_xmaxn=num)
        plot_example(f"Max real steps: {num}", sp_data, z_data)

    for num in [6, 14, 25, 50]:
        i += 1
        plt.subplot(2, 4, i, projection="smith", grid_major_ymaxn=num)
        plot_example(f"Max imaginary steps: {num}", sp_data, z_data)

    save_figure(chart_dir, "grid_locators")


def test_normalize(setup_environment):
    """Test for normalization with various impedances."""
    sp_data, chart_dir = setup_environment
    z_data = sp_data * 50

    fig = plt.figure(figsize=(18, 12))
    fig.set_layout_engine("tight")
    i = 0
    for normalize in [False, True]:
        for impedance in [10, 50, 200]:
            i += 1
            plt.subplot(
                2, 3, i, projection="smith",
                axes_impedance=impedance,
                axes_normalize=normalize,
            )
            plot_example(f"Impedance: {impedance} Ω — Normalize: {normalize}", sp_data, z_data)

    save_figure(chart_dir, "normalize")


def test_markers(setup_environment):
    """Test for marker styles and configurations."""
    _, chart_dir = setup_environment

    VStartMarker = np.array([[0, 0], [0.5, 0.5], [0, -0.5], [-0.5, 0.5], [0, 0]])
    XEndMarker = np.array(
        [
            [0, 0],
            [0.5, 0.5],
            [0.25, 0],
            [0.5, -0.5],
            [0, 0],
            [-0.5, -0.5],
            [-0.25, 0],
            [-0.5, 0.5],
            [0, 0],
        ]
    )

    fig = plt.figure(figsize=(24, 12))
    fig.set_layout_engine("tight")
    i = 0
    for hackline, startmarker, endmarker, rotate_marker in [
        [False, None, None, False],
        [True, "s", "^", False],
        [True, "s", None, False],
        [True, VStartMarker, XEndMarker, False],
        [True, "s", "^", True],
        [True, None, "^", False],
    ]:
        i += 1
        ax = plt.subplot(
            2, 3, i, projection="smith",
            plot_marker_hack=hackline,
            plot_marker_rotate=rotate_marker,
        )
        SmithAxes.update_scParams(
            instance=ax, plot_marker_start=startmarker, plot_marker_end=endmarker
        )
        plot_example(
            f"HackLines: {hackline} - StartMarker: {startmarker}\nEndMarker: {endmarker} - Rotate: {rotate_marker}",
            sp_data=np.array([50]),
            z_data=np.array([25]),
            markersize=10,
        )

    save_figure(chart_dir, "markers")


def test_interpolation(setup_environment):
    """Test for interpolation and equipoint configurations."""
    sp_data, chart_dir = setup_environment
    z_data = sp_data * 50

    fig = plt.figure(figsize=(18, 12))
    fig.set_layout_engine("tight")
    i = 0
    for interpolation, equipoints in [
        [False, False],
        [10, False],
        [False, 10],
        [False, 50],
    ]:
        i += 1
        plt.subplot(2, 2, i, projection="smith")
        plot_example(
            f"Interpolation: {interpolation} — Equipoints: {equipoints}",
            sp_data,
            z_data,
            interpolate=interpolation,
            equipoints=equipoints,
        )

    save_figure(chart_dir, "interpolation")

def test_miscellaneous(setup_environment):
    """Test for miscellaneous Smith chart settings."""
    sp_data, chart_dir = setup_environment
    z_data = sp_data * 50

    fig = plt.figure(figsize=(18, 12))
    fig.set_layout_engine("tight")
    plt.subplot(2, 3, 1, projection="smith", plot_marker_hack=True)
    plot_example("Legend", sp_data, z_data)
    plt.legend(["S11", "S22", "Polyline", "Z → 0.125λ"])

    divs = [1, 3, 7]
    plt.subplot(
        2, 3, 2, projection="smith",
        grid_minor_enable=True,
        grid_minor_fancy=True,
        grid_minor_fancy_dividers=divs,
    )
    plot_example(f"Minor fancy dividers={divs}", sp_data, z_data)

    save_figure(chart_dir, "miscellaneous")