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

pysmithchart
============

|pypi| |github| |conda| |license| |test| |docs| |downloads|

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

    import matplotlib.pyplot as plt
    from pysmithchart import S_PARAMETER

    # Create a subplot with the custom Smith chart projection.
    plt.subplot(1, 1, 1, projection="smith")
    
    # Plot a couple of complex reflection coefficients.
    plt.plot([0.5 + 0.3j, -0.2 - 0.1j], 'o', datatype=S_PARAMETER,
            label="Reflection Coefficients")
    
    plt.show()

**Example 2: Plotting Impedance Data**

Here we plot a set of normalized impedance values on the Smith chart:

.. code-block:: python

    import matplotlib.pyplot as plt
    from pysmithchart import Z_PARAMETER

    # Sample impedance data (normalized)
    ZL = [30 + 30j, 50 + 50j, 100 + 100j]

    # Create a Smith chart subplot.
    plt.subplot(1, 1, 1, projection="smith")
    
    # Plot impedance data using a blue line with circle markers.
    plt.plot(ZL, "b-o")  # default datatype is Z_PARAMETER
    
    plt.show()

**Example 3: Advanced Plot Customization**

Customize grid styles, marker behavior, and apply interpolation:

.. code-block:: python

    import matplotlib.pyplot as plt
    from pysmithchart import Z_PARAMETER

    ZL = [40 + 20j, 60 + 80j, 90 + 30j]
    
    plt.subplot(1, 1, 1, projection="smith", axes_impedance=200)

    plt.plot([40 + 20j, 60 + 80j, 90 + 30j],
            linestyle='--', marker='s', markersize=8,
            interpolate=2, markerhack=True, rotate_marker=True,
            )

    plt.title('Interpolated data and custom markers')
    plt.show()

Documentation
-------------

For more details on the API, configuration options, and advanced usage, please refer
to the full documentation at `pysmithchart.readthedocs.io <https://pysmithchart.readthedocs.io>`_.

License
-------

pysmithchart is licensed under the terms of the BSD license. See the
:download:`LICENSE file <LICENSE.txt>` for details.
