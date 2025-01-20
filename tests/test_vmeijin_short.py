import os
import numpy as np
import pytest
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pysmithplot import SmithAxes

# have matplotlib legend include three markers instead of one
rcParams.update({"legend.numpoints": 3})

@pytest.fixture
def setup_test_environment(tmp_path):
    """Fixture to set up a test environment with paths for data and charts."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path11 = os.path.join(script_dir, "data/s11.csv")
    data_path22 = os.path.join(script_dir, "data/s22.csv")

    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)
    return data_path11, data_path22, chart_dir


def test_smith_chart_plot(setup_test_environment):
    """Test for plotting data on a Smith chart using various configurations."""
    data_path11, data_path22, chart_dir = setup_test_environment

    # Load data
    data = np.loadtxt(data_path11, delimiter=",", skiprows=1)[::100]
    val1 = data[:, 1] + data[:, 2] * 1j

    data = np.loadtxt(data_path22, delimiter=",", skiprows=1)[::100]
    val2 = data[:, 1] + data[:, 2] * 1j

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
    export_path = os.path.join(chart_dir, "export.pdf")
    plt.savefig(export_path, format="pdf", bbox_inches="tight")
    plt.close()

    # Verify output
    assert os.path.exists(export_path), "Exported chart file does not exist."
