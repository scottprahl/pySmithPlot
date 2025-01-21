# from https://github.com/soerenbnoergaard/pySmithPlot
import os
import numpy as np
import matplotlib.pyplot as plt
from pysmithchart import SmithAxes

def test_vswr_circle():
    """Test plotting a VSWR circle on the Smith chart."""

    # Create VSWR circle
    G = 0.5 * np.exp(2j * np.pi * np.linspace(0, 1, 100))
    ZL = -(G + 1) / (G - 1)

    plt.figure(figsize=(6, 6))
    ax = plt.subplot(1, 1, 1, projection="smith")
    SmithAxes.update_scParams(instance=ax, 
                              reset=True, 
                              grid_major_enable=True, 
                              axes_impedance=1, 
                              plot_default_datatype=SmithAxes.Z_PARAMETER)

    plt.plot(ZL, "k", label="VSWR Circle")
    plt.plot(1 + 0j, 'b', marker="o", label="$1+0j$")
    plt.plot(1 + 1j, 'r', marker="o", label="$1+1j$")
    plt.plot(0.5 - 0.5j, 'g', marker="o", label="$0.5-0.5j$")

    plt.legend()
    plt.tight_layout()
    
    # Save the output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)
    output_path = os.path.join(chart_dir, "vswr_circle.pdf")
    plt.savefig(output_path, format='pdf')
    plt.close()

if __name__ == "__main__":
    test_vswr_circle()