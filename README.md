pySmithPlot
===========

This is a fork of **pySmithPlot** that works with matplotlib versions greater than 3.4.

**pySmithPlot** is a matplotlib extension providing a projection class for creating high quality Smith Charts with Python. The generated plots blend seamless into matplotlib's style and support almost the full range of customization options. 

This Library allows the fully automatic generation of Smith Charts with various customizable parameters and well selected default values. It also provides the following modifications and extensions:

- circle shaped drawing area with labels placed around 
- plot() accepts real and complex numbers as well as numpy.ndarray's
- lines can be automatically interpolated to improve the optical appearance 
- data ranges can be interpolated to an equidistant spacing
- start/end markers of lines can be modified and rotate tangential
- gridlines are 3-point arcs to improve space efficiency of exported plots
- 'fancy' option for adaptive grid generation
- own tick locators for nice axis labels

For making a Smith Chart plot, it is sufficient to `import smithplot` and create a new subplot with projection set to 'smith'. (Requires matplotlib version 1.2)

A short example can be found in the `testbenches` directory and started with:

    python3 smith_short_test.py
    
For more details and documentation, take a look into `smithplot/smithaxes.py`. 

`testbenches/smith_full_test.py` runs various testbenches and gives a comparison for almost all parameters. These are the generated sample plots: 

![Grid Styles](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_grid_styles.png)
[Grid Styles - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_grid_styles.pdf)

![Fancy Threshold](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_fancy_grid.png)
[Fancy Threshold - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_fancy_grid.pdf)

![Grid Locators](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_grid_locators.png)
[Grid Locators - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_grid_locators.pdf)

![Marker Modification](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_markers.png)
[Marker Modification - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_markers.pdf)

![Interpolation](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_interpolation.png)
[Interpolation - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_interpolation.pdf)

![Normalize](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_normalize.png)
[Normalize - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_normalize.pdf)

![Miscellaneous](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_miscellaneous.png)
[Miscellaneous - PDF](https://github.com/vMeijin/pySmithPlot/wiki/images/examples/sample_miscellaneous.pdf)
