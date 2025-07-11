"""
Tests for fit manager functionality.

This module tests the FitManager class and related functionality.
"""

import numpy as np
from unittest.mock import Mock

from mdaviz.fit_manager import FitManager, FitData
from mdaviz.fit_models import FitResult


class TestFitData:
    """Test FitData class."""

    def test_fit_data_initialization(self) -> None:
        """Test FitData initialization with valid parameters."""
        model_name = "Gaussian"
        fit_result = Mock(spec=FitResult)
        x_range = (0.0, 10.0)
        visible = True

        fit_data = FitData(
            model_name=model_name,
            fit_result=fit_result,
            x_range=x_range,
            visible=visible,
        )

        assert fit_data.model_name == model_name
        assert fit_data.fit_result == fit_result
        assert fit_data.x_range == x_range
        assert fit_data.visible == visible

    def test_fit_data_defaults(self) -> None:
        """Test FitData initialization with default values."""
        model_name = "Gaussian"
        fit_result = Mock(spec=FitResult)

        fit_data = FitData(model_name=model_name, fit_result=fit_result)

        assert fit_data.model_name == model_name
        assert fit_data.fit_result == fit_result
        assert fit_data.x_range is None
        assert fit_data.visible is True


class TestFitManager:
    """Test FitManager class."""

    def test_fit_manager_initialization(self) -> None:
        """Test FitManager initialization."""
        manager = FitManager()

        assert manager._fits == {}
        assert hasattr(manager, "_models")

    def test_add_fit_success(self) -> None:
        """Test successful fit addition."""
        manager = FitManager()

        # Create test data
        curve_id = "test_curve"
        model_name = "Gaussian"
        x_data = np.linspace(-5, 5, 100)
        y_data = np.exp(-(x_data**2) / 2) + 0.1 * np.random.normal(size=len(x_data))

        # Add fit
        manager.addFit(curve_id, model_name, x_data, y_data)

        # Check that fit was added
        fit_data = manager.getFitData(curve_id)
        assert fit_data is not None
        assert fit_data.model_name == model_name

    def test_add_fit_with_range(self) -> None:
        """Test fit addition with x range."""
        manager = FitManager()

        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))
        x_range = (2.0, 8.0)

        manager.addFit(curve_id, model_name, x_data, y_data, x_range=x_range)

        fit_data = manager.getFitData(curve_id)
        assert fit_data is not None
        assert fit_data.x_range == x_range

    def test_remove_fit(self) -> None:
        """Test fit removal."""
        manager = FitManager()

        # Add a fit first
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Remove the fit
        manager.removeFit(curve_id)

        # Check that fit was removed
        assert manager.getFitData(curve_id) is None

    def test_remove_nonexistent_fit(self) -> None:
        """Test removing a fit that doesn't exist."""
        manager = FitManager()

        # Should not raise an error
        manager.removeFit("nonexistent_curve")

    def test_get_fit_data(self) -> None:
        """Test getting fit data."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Get fit data
        fit_data = manager.getFitData(curve_id)

        assert fit_data is not None
        assert fit_data.model_name == model_name

    def test_get_nonexistent_fit_data(self) -> None:
        """Test getting fit data that doesn't exist."""
        manager = FitManager()

        fit_data = manager.getFitData("nonexistent_curve")
        assert fit_data is None

    def test_get_curve_fits(self) -> None:
        """Test getting all fits for a curve."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Get all fits for the curve
        fits = manager.getCurveFits(curve_id)

        assert len(fits) == 1
        assert "single_fit" in fits

    def test_get_all_fits(self) -> None:
        """Test getting all fits for all curves."""
        manager = FitManager()

        # Add fits to multiple curves
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit("curve1", model_name, x_data, y_data)
        manager.addFit("curve2", model_name, x_data, y_data)

        # Get all fits
        all_fits = manager.getAllFits()

        assert "curve1" in all_fits
        assert "curve2" in all_fits
        assert "single_fit" in all_fits["curve1"]
        assert "single_fit" in all_fits["curve2"]

    def test_set_fit_visibility(self) -> None:
        """Test setting fit visibility."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Set visibility to False
        manager.setFitVisibility(curve_id, False)

        # Check that visibility was changed
        assert manager.isFitVisible(curve_id) is False

    def test_is_fit_visible(self) -> None:
        """Test checking fit visibility."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Check visibility
        assert manager.isFitVisible(curve_id) is True

    def test_get_fit_curve_data(self) -> None:
        """Test getting fit curve data."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Get fit curve data
        curve_data = manager.getFitCurveData(curve_id)

        assert curve_data is not None
        assert len(curve_data) == 2  # (x, y) arrays

    def test_get_fit_parameters(self) -> None:
        """Test getting fit parameters."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Get fit parameters
        parameters = manager.getFitParameters(curve_id)

        assert parameters is not None
        assert isinstance(parameters, dict)

    def test_get_fit_uncertainties(self) -> None:
        """Test getting fit parameter uncertainties."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Get fit uncertainties
        uncertainties = manager.getFitUncertainties(curve_id)

        assert uncertainties is not None
        assert isinstance(uncertainties, dict)

    def test_get_fit_quality_metrics(self) -> None:
        """Test getting fit quality metrics."""
        manager = FitManager()

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Get quality metrics
        metrics = manager.getFitQualityMetrics(curve_id)

        assert metrics is not None
        assert isinstance(metrics, dict)

    def test_has_fits(self) -> None:
        """Test checking if a curve has fits."""
        manager = FitManager()

        curve_id = "test_curve"

        # Initially no fits
        assert manager.hasFits(curve_id) is False

        # Add a fit
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Now has fits
        assert manager.hasFits(curve_id) is True

    def test_get_fit_count(self) -> None:
        """Test getting fit count for a curve."""
        manager = FitManager()

        curve_id = "test_curve"

        # Initially no fits
        assert manager.getFitCount(curve_id) == 0

        # Add a fit
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Now has 1 fit (only one fit per curve is supported)
        assert manager.getFitCount(curve_id) == 1

    def test_clear_all_fits(self) -> None:
        """Test clearing all fits."""
        manager = FitManager()

        # Add fits to multiple curves
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit("curve1", model_name, x_data, y_data)
        manager.addFit("curve2", model_name, x_data, y_data)

        # Clear all fits
        manager.clearAllFits()

        # Check that all fits were removed
        assert manager.getFitData("curve1") is None
        assert manager.getFitData("curve2") is None


class TestFitManagerSignals:
    """Test FitManager signal emissions."""

    def test_fit_added_signal(self, qtbot) -> None:
        """Test that fitAdded signal is emitted when adding a fit."""
        manager = FitManager()

        # Connect to signal
        signal_received = False
        received_curve_id = None

        def on_fit_added(curve_id):
            nonlocal signal_received, received_curve_id
            signal_received = True
            received_curve_id = curve_id

        manager.fitAdded.connect(on_fit_added)

        # Add a fit
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Check that signal was emitted
        assert signal_received
        assert received_curve_id == curve_id

    def test_fit_removed_signal(self, qtbot) -> None:
        """Test that fitRemoved signal is emitted when removing a fit."""
        manager = FitManager()

        # Add a fit first
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Connect to signal
        signal_received = False
        received_curve_id = None

        def on_fit_removed(curve_id):
            nonlocal signal_received, received_curve_id
            signal_received = True
            received_curve_id = curve_id

        manager.fitRemoved.connect(on_fit_removed)

        # Remove the fit
        manager.removeFit(curve_id)

        # Check that signal was emitted
        assert signal_received
        assert received_curve_id == curve_id

    def test_fit_visibility_changed_signal(self, qtbot) -> None:
        """Test that fitVisibilityChanged signal is emitted when changing visibility."""
        manager = FitManager()

        # Add a fit first
        curve_id = "test_curve"
        model_name = "Linear"
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        manager.addFit(curve_id, model_name, x_data, y_data)

        # Connect to signal
        signal_received = False
        received_curve_id = None
        received_visible = None

        def on_visibility_changed(curve_id, visible):
            nonlocal signal_received, received_curve_id, received_visible
            signal_received = True
            received_curve_id = curve_id
            received_visible = visible

        manager.fitVisibilityChanged.connect(on_visibility_changed)

        # Change visibility
        manager.setFitVisibility(curve_id, False)

        # Check that signal was emitted
        assert signal_received
        assert received_curve_id == curve_id
        assert received_visible is False
