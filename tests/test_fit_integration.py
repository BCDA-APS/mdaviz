"""
Integration tests for fit functionality.

This module tests the integration between different fit components.
"""

import numpy as np
from mdaviz.fit_manager import FitManager


class TestFitIntegration:
    """Test integration of fit functionality."""

    def test_fit_manager_with_real_data(self) -> None:
        """Test FitManager with real synthetic data."""
        manager = FitManager()

        # Create synthetic Gaussian data
        x_data = np.linspace(-5, 5, 100)
        true_amplitude = 2.0
        true_center = 0.0
        true_sigma = 1.0
        true_offset = 0.5

        # Generate data with noise
        y_data = (
            true_amplitude
            * np.exp(-((x_data - true_center) ** 2) / (2 * true_sigma**2))
            + true_offset
            + 0.1 * np.random.normal(size=len(x_data))
        )

        # Perform fit
        curve_id = "test_curve"
        manager.addFit(curve_id, "Gaussian", x_data, y_data)

        # Verify fit was successful
        fit_data = manager.getFitData(curve_id)
        assert fit_data is not None
        assert fit_data.model_name == "Gaussian"

    def test_multiple_fits_on_same_curve(self) -> None:
        """Test multiple fits on the same curve (replaces previous fit)."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        curve_id = "test_curve"

        # Add first fit
        manager.addFit(curve_id, "Linear", x_data, y_data)
        assert manager.getFitCount(curve_id) == 1

        # Add second fit (replaces first)
        manager.addFit(curve_id, "Quadratic", x_data, y_data)
        assert manager.getFitCount(curve_id) == 1  # Still only one fit

        # Verify the fit was replaced
        fit_data = manager.getFitData(curve_id)
        assert fit_data.model_name == "Quadratic"

    def test_fit_with_range_selection(self) -> None:
        """Test fit with x range selection."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 100)
        y_data = np.sin(x_data) + 0.1 * np.random.normal(size=len(x_data))

        # Define fit range
        x_range = (2.0, 8.0)

        curve_id = "test_curve"
        manager.addFit(curve_id, "Linear", x_data, y_data, x_range=x_range)

        # Verify fit data
        fit_data = manager.getFitData(curve_id)
        assert fit_data is not None
        assert fit_data.x_range == x_range

    def test_fit_visibility_control(self) -> None:
        """Test fit visibility control."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        curve_id = "test_curve"
        manager.addFit(curve_id, "Linear", x_data, y_data)

        # Initially visible
        assert manager.isFitVisible(curve_id) is True

        # Set to invisible
        manager.setFitVisibility(curve_id, False)
        assert manager.isFitVisible(curve_id) is False

    def test_fit_removal(self) -> None:
        """Test fit removal functionality."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        curve_id = "test_curve"
        manager.addFit(curve_id, "Linear", x_data, y_data)

        # Verify fit exists
        assert manager.hasFits(curve_id)
        assert manager.getFitData(curve_id) is not None

        # Remove fit
        manager.removeFit(curve_id)

        # Verify fit was removed
        assert not manager.hasFits(curve_id)
        assert manager.getFitData(curve_id) is None

    def test_clear_all_fits(self) -> None:
        """Test clearing all fits."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        # Add fits to multiple curves
        manager.addFit("curve1", "Linear", x_data, y_data)
        manager.addFit("curve2", "Gaussian", x_data, y_data)

        # Verify fits exist
        assert manager.getFitCount("curve1") == 1
        assert manager.getFitCount("curve2") == 1

        # Clear all fits
        manager.clearAllFits()

        # Verify all fits were removed
        assert manager.getFitCount("curve1") == 0
        assert manager.getFitCount("curve2") == 0

    def test_fit_parameter_uncertainties(self) -> None:
        """Test that fit parameter uncertainties are provided."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        curve_id = "test_curve"
        manager.addFit(curve_id, "Linear", x_data, y_data)

        # Get uncertainties
        uncertainties = manager.getFitUncertainties(curve_id)
        assert uncertainties is not None
        assert isinstance(uncertainties, dict)

    def test_fit_quality_metrics(self) -> None:
        """Test that fit quality metrics are reasonable."""
        manager = FitManager()

        # Create synthetic data with good signal-to-noise
        x_data = np.linspace(0, 10, 100)
        y_data = 2 * x_data + 1 + 0.01 * np.random.normal(size=len(x_data))  # Low noise

        curve_id = "test_curve"
        manager.addFit(curve_id, "Linear", x_data, y_data)

        # Get quality metrics
        metrics = manager.getFitQualityMetrics(curve_id)
        assert metrics is not None
        assert isinstance(metrics, dict)

    def test_fit_with_different_models(self) -> None:
        """Test that different fit models work correctly."""
        manager = FitManager()

        # Create synthetic data
        x_data = np.linspace(0, 10, 100)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))

        curve_id = "test_curve"

        # Test different models
        models_to_test = ["Linear", "Quadratic", "Cubic"]

        for model_name in models_to_test:
            manager.addFit(curve_id, model_name, x_data, y_data)

            # Verify fit was successful
            fit_data = manager.getFitData(curve_id)
            assert fit_data is not None
            assert fit_data.model_name == model_name
