# Fit Functionality in mdaviz

This document describes the curve fitting functionality implemented in mdaviz.

## Overview

The fit functionality allows users to perform mathematical curve fitting on plotted data curves. It provides a comprehensive set of fit models and tools for analyzing experimental data.

## Features

### Available Fit Models

The following fit models are available:

1. **Gaussian** - Fits a Gaussian (normal) distribution
   - Parameters: amplitude, center, sigma, offset
   - Useful for: Peak analysis, spectroscopy data

2. **Lorentzian** - Fits a Lorentzian (Cauchy) distribution
   - Parameters: amplitude, center, gamma, offset
   - Useful for: Resonance peaks, spectral lines

3. **Linear** - Fits a straight line
   - Parameters: slope, intercept
   - Useful for: Trend analysis, calibration curves

4. **Exponential** - Fits an exponential decay/growth
   - Parameters: amplitude, decay, offset
   - Useful for: Decay processes, growth curves

5. **Quadratic** - Fits a second-degree polynomial
   - Parameters: coeff_0, coeff_1, coeff_2
   - Useful for: Curved trends, parabolic data

6. **Cubic** - Fits a third-degree polynomial
   - Parameters: coeff_0, coeff_1, coeff_2, coeff_3
   - Useful for: Complex curved trends

7. **Error Function** - Fits an error function (erf) with scaling and offset
   - Parameters: amplitude, center, sigma, offset
   - Useful for: Step functions, cumulative distributions, edge detection

### Fit Range Selection

- **Full Range**: Fit to all data points in the curve
- **Cursor Range**: Use cursor positions to define a specific x-range for fitting
  - Set cursor 1 (middle click) and cursor 2 (right click) to define range
  - Check "Use cursor range" option before fitting

### Fit Results

For each fit, the following information is provided:

- **Fit Parameters**: Best-fit values with uncertainties
- **Quality Metrics**:
  - R-squared (R²): Goodness of fit (0-1, higher is better)
  - Chi-squared (χ²): Sum of squared residuals
  - Reduced Chi-squared: χ² normalized by degrees of freedom

## How to Use

### Basic Fitting

1. **Load Data**: Open an MDA file and plot the desired curves
2. **Select Curve**: Choose the curve to fit from the curve dropdown
3. **Choose Model**: Select a fit model from the "Fit Model" dropdown
4. **Set Range** (optional): Check "Use cursor range" if you want to fit only a portion of the data
5. **Perform Fit**: Click the "Fit" button
6. **View Results**: The fit results will appear in the "Fit Results" section

### Multiple Fits

- You can perform multiple fits on the same curve
- Each fit will be listed in the fit list
- Click on a fit in the list to view its detailed results
- Fit curves are displayed as dashed lines on the plot

### Managing Fits

- **View Fit Details**: Select a fit from the list to see parameters and quality metrics
- **Clear Individual Fits**: Remove specific fits (future enhancement)
- **Clear All Fits**: Click "Clear All" to remove all fits from the current curve

## Technical Details

### Fit Implementation

- Uses `scipy.optimize.curve_fit` for robust curve fitting
- Automatic initial parameter estimation based on data characteristics
- Support for parameter bounds and initial guesses (future enhancement)
- Handles NaN and infinite values gracefully

### Data Processing

- Applies current offset and factor settings to data before fitting
- Supports x-range selection for focused fitting
- Automatic data cleaning (removes invalid values)

### Quality Assessment

- R-squared calculation for goodness of fit
- Chi-squared analysis for fit quality
- Parameter uncertainties from covariance matrix
- Reduced chi-squared for model comparison

## Best Practices

### Choosing a Fit Model

1. **Examine the Data**: Look at the shape and characteristics of your data
2. **Consider Physics**: Choose models that match the underlying physical process
3. **Start Simple**: Begin with simpler models (linear, Gaussian) before trying complex ones
4. **Check Quality**: Use R-squared and reduced chi-squared to assess fit quality

### Range Selection

- Use cursor range when you want to focus on a specific region
- Ensure sufficient data points in the selected range
- Consider the physical meaning of the selected range

### Interpreting Results

- **R-squared > 0.9**: Excellent fit
- **R-squared 0.7-0.9**: Good fit
- **R-squared < 0.7**: Poor fit, consider different model
- **Reduced χ² ≈ 1**: Good fit with appropriate uncertainties
- **Reduced χ² >> 1**: Poor fit or underestimated uncertainties

## Future Enhancements

Planned improvements include:

- **Advanced Parameter Control**: Manual initial guesses and bounds
- **Fit Comparison**: Side-by-side comparison of different fits
- **Residual Analysis**: Plot and analyze fit residuals
- **Export Functionality**: Save fit results to files
- **Custom Models**: User-defined fit functions
- **Batch Fitting**: Fit multiple curves simultaneously

## Troubleshooting

### Common Issues

1. **Fit Fails**:
   - Check that you have enough data points
   - Try a different fit model
   - Ensure data doesn't contain too many invalid values

2. **Poor Fit Quality**:
   - Examine the data shape and choose appropriate model
   - Consider using a range selection to focus on relevant data
   - Check for systematic errors in the data

3. **Unreasonable Parameters**:
   - Verify the fit model is appropriate for your data
   - Check units and scaling of your data
   - Consider using parameter bounds (future feature)

### Error Messages

- **"Not enough data points"**: Increase the number of data points or reduce the number of fit parameters
- **"Fit failed"**: The optimization algorithm couldn't converge, try different initial conditions or model
- **"Model not available"**: Check that the selected model is properly loaded

## API Reference

For developers, the fit functionality is implemented in the following modules:

- `fit_models.py`: Fit model definitions and implementations
- `fit_manager.py`: Fit management and coordination
- `chartview.py`: Integration with plotting system
- `mda_file_viz.py`: UI integration

Key classes:
- `FitModel`: Base class for fit models
- `FitResult`: Container for fit results
- `FitManager`: Manages fit operations and state
- `FitData`: Stores fit information and metadata
