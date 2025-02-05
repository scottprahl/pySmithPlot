.. |pypi| image:: https://img.shields.io/pypi/v/pysmithchart?color=68CA66
   :target: https://pypi.org/project/pysmithchart/
   :alt: PyPI

.. |github| image:: https://img.shields.io/github/v/tag/scottprahl/pysmithchart?label=github&color=68CA66
   :target: https://github.com/scottprahl/pysmithchart
   :alt: GitHub

.. |conda| image:: https://img.shields.io/conda/vn/conda-forge/pysmithchart?label=conda&color=68CA66
   :target: https://github.com/conda-forge/pysmithchart-feedstock
   :alt: Conda

.. |license| image:: https://img.shields.io/github/license/scottprahl/pysmithchart?color=68CA66
   :target: https://github.com/scottprahl/pysmithchart/blob/main/LICENSE.txt
   :alt: License

.. |test| image:: https://github.com/scottprahl/pysmithchart/actions/workflows/test.yaml/badge.svg
   :target: https://github.com/scottprahl/pysmithchart/actions/workflows/test.yaml
   :alt: Testing

.. |docs| image:: https://readthedocs.org/projects/pysmithchart/badge?color=68CA66
   :target: https://pysmithchart.readthedocs.io
   :alt: Docs

.. |downloads| image:: https://img.shields.io/pypi/dm/pysmithchart?color=68CA66
   :target: https://pypi.org/project/pysmithchart/
   :alt: Downloads

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: code style: black


pysmithchart
============

|pypi| |github| |conda| |downloads|

|license| |test| |docs| |black|

Overview
--------

**pysmithchart** is a matplotlib extension that adds a custom projection for creating
Smith Charts in Python. Originally forked from `pysmithplot <https://github.com/vMeijin/pySmithPlot>`_,
this library has been updated to work with modern matplotlib versions while preserving
a rich set of features for RF and microwave engineering applications.

The package enables visualization and analysis of reflection coefficients,
impedances, and admittances. It seamlessly integrates into the matplotlib ecosystem,
providing full control over plot appearance, grid customizations, interpolation
of complex data, and even advanced marker handling.

Key Capabilities
----------------

- **Smith Projection:** Plot data on a Smith chart using the `SmithAxes` projection.
- **Multiple Data Types:** Easily plot S-parameters, normalized impedances (Z) and admittances (Y).
- **Grid Customization:** Draw major/minor gridlines as arcs with "fancy" adaptive
  spacing and styling options.
- **Interpolation & Equidistant Points:** Optionally smooth or resample plotted data.
- **Marker Customization:** Manipulate start and end markers (with optional rotation)
  to emphasize data endpoints.
- **Full Matplotlib Integration:** Use matplotlib’s standard API along with extra keywords
  for specialized Smith chart plotting.

Installation
------------

Install pysmithchart with pip:

.. code-block:: bash

    pip install pysmithchart

Or install via conda:

.. code-block:: bash

    conda install -c conda-forge pysmithchart

Quick Start Examples
--------------------

Below are a few examples to help you get started quickly.

**Example 1: Plotting a Reflection Coefficient (S-parameter)**

This example creates a Smith chart and plots a simple reflection coefficient:

.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from pysmithchart import S_PARAMETER

    # array of reflection coefficients
    S = [0.5 + 0.3j, -0.2 - 0.1j]

    # Create a subplot that will use the Smith projection.
    plt.figure(figsize=(6,6))
    plt.subplot(1, 1, 1, projection="smith", grid_major_color_x='red', grid_major_color_y='blue')

    # Plot the reflection (scattering) coefficients
    plt.plot(S, ls='', markersize=10, datatype=S_PARAMETER)

    plt.title('Plotting 0.5 + 0.3j and -0.2 - 0.1j')
    plt.show()

.. image:: https://raw.githubusercontent.com/scottprahl/pysmithchart/main/docs/readme_fig1.svg
   :alt: Colored Smith Chart

**Example 2: Plotting Impedance Data**

Here we plot a set of normalized impedance values on the Smith chart:

.. code-block:: python

    import matplotlib.pyplot as plt
    import pysmithchart

    # Sample impedance data (normalized)
    ZL = [30 + 30j, 50 + 50j, 100 + 100j]

    # Create a subplot that will use the Smith projection and include the minor grid
    plt.figure(figsize=(6,6))
    plt.subplot(1, 1, 1, projection="smith", axes_impedance=200, grid_minor_enable=True)
    
    plt.plot(ZL, "b-o", markersize=10)   # default datatype is Z_PARAMETER
    plt.title('Plotting Impedances Assuming Z₀=200Ω')
    plt.show()

.. image:: https://raw.githubusercontent.com/scottprahl/pysmithchart/main/docs/readme_fig2.svg
   :alt: Colored Smith Chart

**Example 3: Advanced Plot Customization**

Customize grid styles, marker behavior, and apply interpolation:

.. code-block:: python

    import matplotlib.pyplot as plt
    import pysmithchart

    ZL = [40 + 20j, 60 + 80j, 90 + 30j]

    plt.figure(figsize=(6,6))
    plt.subplot(1, 1, 1, projection="smith")

    plt.plot(ZL, markersize=16, ls='--', markerhack=True, rotate_marker=True)
    plt.title('Custom markers')
    plt.savefig("readme_fig3.svg", format='svg')
    plt.show()

.. image:: https://raw.githubusercontent.com/scottprahl/pysmithchart/main/docs/readme_fig3.svg
   :alt: Custom Markers

Documentation
-------------

For more details on the API, configuration options, and advanced usage, please refer
to the full documentation at `pysmithchart.readthedocs.io <https://pysmithchart.readthedocs.io>`_.

License
-------

pysmithchart is distributed under the 
`BSD LICENSE <https://raw.githubusercontent.com/scottprahl/pysmithchart/main/LICENSE.txt>`.
