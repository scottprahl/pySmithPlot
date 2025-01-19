#!/usr/bin/env python3

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams.update({"legend.numpoints": 3})

sys.path.append("..")
from pysmithplot import SmithAxes

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path11 = os.path.join(script_dir, "data/s11.csv")
data_path22 = os.path.join(script_dir, "data/s22.csv")
chart_dir = os.path.join(script_dir, "charts")

data = np.loadtxt(data_path11, delimiter=",", skiprows=1)[::100]
val1 = data[:, 1] + data[:, 2] * 1j

data = np.loadtxt(data_path22, delimiter=",", skiprows=1)[::100]
val2 = data[:, 1] + data[:, 2] * 1j

# plot data
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

leg = plt.legend(loc="lower right", fontsize=12)
plt.title("Matplotlib Smith Chart Projection")

plt.savefig(chart_dir + "export.pdf", format="pdf", bbox_inches="tight")
plt.show()
