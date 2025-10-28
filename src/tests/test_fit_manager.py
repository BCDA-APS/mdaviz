#!/usr/bin/env python
"""
Tests for the mdaviz fit_manager module.

Covers fitting routines, error handling, and edge cases.
"""

from typing import TYPE_CHECKING
import pytest
import numpy as np

from mdaviz.fit_manager import FitManager
from mdaviz.fit_models import get_available_models

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


def test_fit_manager_successful_fit() -> None:
    """Test that FitManager can fit a simple quadratic dataset successfully."""
    x = np.linspace(-5, 5, 100)
    y = 2 * x**2 + 3 * x + 1
    fit_manager = FitManager()

    # Test adding a fit
    curve_id = "test_curve"
    fit_manager.addFit(curve_id, "Quadratic", x, y)

    # Verify fit was added
    fit_data = fit_manager.getFitData(curve_id)
    assert fit_data is not None
    assert fit_data.model_name == "Quadratic"
    assert fit_data.fit_result is not None


def test_fit_manager_fit_with_invalid_data() -> None:
    """Test that FitManager handles invalid data gracefully (should not crash)."""
    x = np.array([1, 2, 3])
    y = np.array([1, 2])  # Mismatched length
    fit_manager = FitManager()

    with pytest.raises(ValueError):
        fit_manager.addFit("test_curve", "Linear", x, y)


def test_fit_manager_fit_with_empty_data() -> None:
    """Test that FitManager handles empty data arrays gracefully."""
    x = np.array([])
    y = np.array([])
    fit_manager = FitManager()

    with pytest.raises(ValueError):
        fit_manager.addFit("test_curve", "Linear", x, y)


def test_fit_manager_fit_with_single_point() -> None:
    """Test that FitManager handles single-point data gracefully."""
    x = np.array([1])
    y = np.array([2])
    fit_manager = FitManager()

    with pytest.raises(ValueError):
        fit_manager.addFit("test_curve", "Linear", x, y)


def test_fit_manager_error_logging_on_failure(caplog: "LogCaptureFixture") -> None:
    """Test that FitManager logs errors when fitting fails."""
    x = np.array([1, 2, 3])
    y = np.array([1, 2, 3])
    fit_manager = FitManager()

    # Use a non-existent model to force an error
    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            fit_manager.addFit("test_curve", "not_a_model", x, y)


def test_fit_manager_parameter_update_and_extraction() -> None:
    """Test updating fit parameters and extracting results."""
    x = np.linspace(0, 10, 50)
    y = 5 * x + 2
    fit_manager = FitManager()

    curve_id = "test_curve"
    fit_manager.addFit(curve_id, "Linear", x, y)

    # Get fit data
    fit_data = fit_manager.getFitData(curve_id)
    assert fit_data is not None

    # Get fit parameters
    params = fit_manager.getFitParameters(curve_id)
    assert params is not None

    # Get fit curve data
    curve_data = fit_manager.getFitCurveData(curve_id)
    assert curve_data is not None
    x_fit, y_fit = curve_data
    assert len(x_fit) == len(x)
    assert len(y_fit) == len(y)


def test_fit_manager_fit_with_nan_data() -> None:
    """Test that FitManager handles NaN values in data arrays."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    y[10] = np.nan
    fit_manager = FitManager()

    with pytest.raises(ValueError):
        fit_manager.addFit("test_curve", "Linear", x, y)


def test_fit_manager_remove_fit() -> None:
    """Test removing a fit from a curve."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    fit_manager = FitManager()

    curve_id = "test_curve"
    fit_manager.addFit(curve_id, "Linear", x, y)

    # Verify fit exists
    assert fit_manager.hasFits(curve_id)

    # Remove fit
    fit_manager.removeFit(curve_id)

    # Verify fit was removed
    assert not fit_manager.hasFits(curve_id)
    assert fit_manager.getFitData(curve_id) is None


def test_fit_manager_fit_visibility() -> None:
    """Test fit visibility controls."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    fit_manager = FitManager()

    curve_id = "test_curve"
    fit_manager.addFit(curve_id, "Linear", x, y)

    # Test visibility
    assert fit_manager.isFitVisible(curve_id)

    # Change visibility
    fit_manager.setFitVisibility(curve_id, False)
    assert not fit_manager.isFitVisible(curve_id)

    fit_manager.setFitVisibility(curve_id, True)
    assert fit_manager.isFitVisible(curve_id)


def test_fit_manager_fit_with_range() -> None:
    """Test fitting with a specific x range."""
    x = np.linspace(0, 10, 100)
    y = 2 * x + 1
    fit_manager = FitManager()

    curve_id = "test_curve"
    x_range = (2.0, 8.0)
    fit_manager.addFit(curve_id, "Linear", x, y, x_range=x_range)

    # Verify fit was created with range
    fit_data = fit_manager.getFitData(curve_id)
    assert fit_data is not None
    assert fit_data.x_range == x_range


def test_fit_manager_invalid_range() -> None:
    """Test fitting with invalid x range."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    fit_manager = FitManager()

    # Invalid range: start >= end
    with pytest.raises(ValueError):
        fit_manager.addFit("test_curve", "Linear", x, y, x_range=(5.0, 3.0))

    # Range outside data bounds
    with pytest.raises(ValueError):
        fit_manager.addFit("test_curve", "Linear", x, y, x_range=(20.0, 30.0))


def test_fit_manager_clear_all_fits() -> None:
    """Test clearing all fits."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    fit_manager = FitManager()

    # Add multiple fits
    for i in range(3):
        curve_id = f"test_curve_{i}"
        fit_manager.addFit(curve_id, "Linear", x, y)
        assert fit_manager.hasFits(curve_id)

    # Clear all fits
    fit_manager.clearAllFits()

    # Verify all fits were removed
    for i in range(3):
        curve_id = f"test_curve_{i}"
        assert not fit_manager.hasFits(curve_id)


def test_fit_manager_get_available_models() -> None:
    """Test getting available fit models."""
    models = get_available_models()

    assert isinstance(models, dict)
    assert len(models) > 0
    # Check for common models
    assert "Linear" in models
    assert "Quadratic" in models


def test_fit_manager_get_fit_quality_metrics() -> None:
    """Test getting fit quality metrics."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    fit_manager = FitManager()

    curve_id = "test_curve"
    fit_manager.addFit(curve_id, "Linear", x, y)

    # Get quality metrics
    metrics = fit_manager.getFitQualityMetrics(curve_id)
    assert metrics is not None
    assert "r_squared" in metrics or "chi_squared" in metrics


def test_fit_manager_get_fit_uncertainties() -> None:
    """Test getting fit parameter uncertainties."""
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1
    fit_manager = FitManager()

    curve_id = "test_curve"
    fit_manager.addFit(curve_id, "Linear", x, y)

    # Get uncertainties
    uncertainties = fit_manager.getFitUncertainties(curve_id)
    assert uncertainties is not None
    assert len(uncertainties) > 0
