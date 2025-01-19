#!/usr/bin/env python3
import os
import numpy as np
import matplotlib.pyplot as plt
from pysmithplot import SmithAxes

script_dir = os.path.dirname(os.path.abspath(__file__))
chart_dir = os.path.join(script_dir, "charts")


#
# Plot empty Smith Chart
#
plt.figure(figsize=(8,8))
plt.subplot(1, 1, 1, projection='smith', grid_major_enable=True)
image_path = os.path.join(chart_dir, "plain_smith.pdf")
plt.savefig(image_path, format="pdf", bbox_inches="tight")
plt.show()

#
# Plot single Load
#
ZL = 75 + 50j
Z0 = 50
plt.figure(figsize=(8,8))
plt.subplot(1, 1, 1, projection='smith', grid_major_enable=True)
plt.plot([ZL], 'ob', markersize=10, datatype=SmithAxes.Z_PARAMETER)
image_path = os.path.join(chart_dir, "one_point.pdf")
plt.savefig(image_path, format="pdf", bbox_inches="tight")
plt.show()


#
# VSWR Circle
#
Z0 = 50
ZL = 30 + 30j

Gamma = (ZL - Z0) / (ZL + Z0)
R = np.abs(Gamma)  # Radius of the VSWR circle
theta = np.linspace(0, 2 * np.pi, 100)
Gamma_d = R * np.exp(1j * theta)
z = (1 + Gamma_d) / (1 - Gamma_d) # Convert new reflection to normalized impedance
Zd = z * Z0 # de-normalize to actual impedances

plt.figure(figsize=(8,8))
plt.subplot(1, 1, 1, projection='smith', grid_major_enable=True)
plt.plot([ZL], 'ob', markersize=10, datatype=SmithAxes.Z_PARAMETER)
plt.plot(Zd, color='red', markersize=5, datatype=SmithAxes.Z_PARAMETER)
image_path = os.path.join(chart_dir, "vswr.pdf")
plt.savefig(image_path, format="pdf", bbox_inches="tight")
plt.show()
