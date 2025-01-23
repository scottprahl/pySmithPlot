import os
import numpy as np
import pytest
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pysmithchart import SmithAxes

# have matplotlib legend include three markers instead of one
rcParams.update({"legend.numpoints": 3})


@pytest.fixture
def setup_environment(tmp_path):
    """
    Fixture to provide the directory for saving charts.
    - Locally: Saves charts in the `charts` folder within the `tests` directory.
    - On GitHub Actions: Uses the provided `tmpdir`.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path11 = os.path.join(script_dir, os.path.join("data", "s11.csv"))
    data11 = load_complex_data(data_path11)
    data_path22 = os.path.join(script_dir, "data/s22.csv")
    data22 = load_complex_data(data_path22)

    if os.getenv("GITHUB_ACTIONS") == "true":
        chart_dir = tmpdir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chart_dir = os.path.join(script_dir, "charts")
        os.makedirs(chart_dir, exist_ok=True)

    return data11, data22, chart_dir


def load_complex_data(file_path, step=100):
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


def test_smith_chart_plot(setup_environment):
    """Test for plotting data on a Smith chart using various configurations."""
    val1, val2, chart_dir = setup_environment

    # Plot data
    plt.figure(figsize=(6, 6))
    ax = plt.subplot(1, 1, 1, projection="smith")
    plt.plot([10, 100], markevery=1)
    plt.plot(200 + 100j, datatype=SmithAxes.Z_PARAMETER)
    plt.plot(50 * val1, label="default", datatype=SmithAxes.Z_PARAMETER)
    plt.plot(
        50 * val2,
        markevery=1,
        label="interpolate=3",
        interpolate=3,
        datatype=SmithAxes.Z_PARAMETER,
    )
    plt.plot(
        val1,
        markevery=1,
        label="equipoints=22",
        equipoints=22,
        datatype=SmithAxes.S_PARAMETER,
    )
    plt.plot(
        val2,
        markevery=3,
        label="equipoints=22, \nmarkevery=3",
        equipoints=22,
        datatype=SmithAxes.S_PARAMETER,
    )

    # Add legend and title
    plt.legend(loc="lower right", fontsize=12)
    plt.title("Matplotlib Smith Chart Projection")

    # Save plot
    export_path = os.path.join(chart_dir, "vmeijin_short.pdf")
    plt.savefig(export_path, format="pdf")
    plt.close()
