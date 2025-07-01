"""
Integration tests for fit functionality.

This module contains integration tests to verify that the fit functionality
works end-to-end with the UI components.
"""

from typing import TYPE_CHECKING
import numpy as np
import pytest
from unittest.mock import Mock, patch
from PyQt5 import QtWidgets

from mdaviz.fit_models import get_available_models
from mdaviz.fit_manager import FitManager

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestFitIntegration:
    """Test fit functionality integration."""
    
    def test_available_models_integration(self) -> None:
        """Test that all expected fit models are available."""
        models = get_available_models()
        
        # Check that all expected models are present
        expected_models = ["Gaussian", "Lorentzian", "Linear", "Exponential", "Quadratic", "Cubic"]
        for model_name in expected_models:
            assert model_name in models
            model = models[model_name]
            assert hasattr(model, 'name')
            assert hasattr(model, 'parameters')
            assert hasattr(model, 'fit')
    
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
        y_data = (true_amplitude * np.exp(-(x_data - true_center)**2 / (2 * true_sigma**2)) + 
                  true_offset + 0.1 * np.random.normal(size=len(x_data)))
        
        # Perform fit
        curve_id = "test_curve"
        fit_id = manager.addFit(curve_id, "Gaussian", x_data, y_data)
        
        # Verify fit was successful
        assert fit_id.startswith("Gaussian_")
        assert manager.hasFits(curve_id)
        assert manager.getFitCount(curve_id) == 1
        
        # Get fit results
        fit_data = manager.getFitData(curve_id, fit_id)
        assert fit_data is not None
        assert fit_data.model_name == "Gaussian"
        assert fit_data.visible is True
        
        # Check fit parameters are reasonable
        parameters = manager.getFitParameters(curve_id, fit_id)
        assert parameters is not None
        assert "amplitude" in parameters
        assert "center" in parameters
        assert "sigma" in parameters
        assert "offset" in parameters
        
        # Check that parameters are close to true values
        assert abs(parameters["amplitude"] - true_amplitude) < 0.5
        assert abs(parameters["center"] - true_center) < 0.5
        assert abs(parameters["sigma"] - true_sigma) < 0.5
        assert abs(parameters["offset"] - true_offset) < 0.5
        
        # Check quality metrics
        metrics = manager.getFitQualityMetrics(curve_id, fit_id)
        assert metrics is not None
        assert metrics["r_squared"] > 0.8  # Should fit well
        assert metrics["chi_squared"] > 0
        assert metrics["reduced_chi_squared"] > 0
    
    def test_multiple_fits_on_same_curve(self) -> None:
        """Test multiple fits on the same curve."""
        manager = FitManager()
        
        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))
        
        curve_id = "test_curve"
        
        # Add multiple fits
        fit_id1 = manager.addFit(curve_id, "Linear", x_data, y_data)
        fit_id2 = manager.addFit(curve_id, "Quadratic", x_data, y_data)
        
        # Verify both fits exist
        assert manager.getFitCount(curve_id) == 2
        assert manager.hasFits(curve_id)
        
        fits = manager.getCurveFits(curve_id)
        assert len(fits) == 2
        assert fit_id1 in fits
        assert fit_id2 in fits
        
        # Verify different model names
        assert fits[fit_id1].model_name == "Linear"
        assert fits[fit_id2].model_name == "Quadratic"
    
    def test_fit_with_range_selection(self) -> None:
        """Test fit with x range selection."""
        manager = FitManager()
        
        # Create synthetic data
        x_data = np.linspace(0, 10, 100)
        y_data = np.sin(x_data) + 0.1 * np.random.normal(size=len(x_data))
        
        # Define fit range
        x_range = (2.0, 8.0)
        
        curve_id = "test_curve"
        fit_id = manager.addFit(curve_id, "Linear", x_data, y_data, x_range=x_range)
        
        # Verify fit data
        fit_data = manager.getFitData(curve_id, fit_id)
        assert fit_data.x_range == x_range
        
        # Get fit curve data and verify it's within range
        curve_data = manager.getFitCurveData(curve_id, fit_id)
        assert curve_data is not None
        x_fit, y_fit = curve_data
        
        # Check that fit data is within the specified range
        assert np.all(x_fit >= x_range[0])
        assert np.all(x_fit <= x_range[1])
    
    def test_fit_visibility_control(self) -> None:
        """Test fit visibility control."""
        manager = FitManager()
        
        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))
        
        curve_id = "test_curve"
        fit_id = manager.addFit(curve_id, "Linear", x_data, y_data)
        
        # Initially visible
        assert manager.isFitVisible(curve_id, fit_id) is True
        
        # Hide fit
        manager.setFitVisibility(curve_id, fit_id, False)
        assert manager.isFitVisible(curve_id, fit_id) is False
        
        # Show fit again
        manager.setFitVisibility(curve_id, fit_id, True)
        assert manager.isFitVisible(curve_id, fit_id) is True
    
    def test_fit_removal(self) -> None:
        """Test fit removal functionality."""
        manager = FitManager()
        
        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))
        
        curve_id = "test_curve"
        fit_id = manager.addFit(curve_id, "Linear", x_data, y_data)
        
        # Verify fit exists
        assert manager.hasFits(curve_id)
        assert manager.getFitData(curve_id, fit_id) is not None
        
        # Remove fit
        manager.removeFit(curve_id, fit_id)
        
        # Verify fit is gone
        assert not manager.hasFits(curve_id)
        assert manager.getFitData(curve_id, fit_id) is None
        assert manager.getFitCount(curve_id) == 0
    
    def test_clear_all_fits(self) -> None:
        """Test clearing all fits."""
        manager = FitManager()
        
        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))
        
        # Add fits to multiple curves
        manager.addFit("curve1", "Linear", x_data, y_data)
        manager.addFit("curve1", "Quadratic", x_data, y_data)
        manager.addFit("curve2", "Gaussian", x_data, y_data)
        
        # Verify fits exist
        assert manager.getFitCount("curve1") == 2
        assert manager.getFitCount("curve2") == 1
        
        # Clear all fits
        manager.clearAllFits()
        
        # Verify all fits are gone
        assert len(manager._fits) == 0
        assert not manager.hasFits("curve1")
        assert not manager.hasFits("curve2")
    
    def test_fit_parameter_uncertainties(self) -> None:
        """Test that fit parameter uncertainties are provided."""
        manager = FitManager()
        
        # Create synthetic data
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1 + 0.1 * np.random.normal(size=len(x_data))
        
        curve_id = "test_curve"
        fit_id = manager.addFit(curve_id, "Linear", x_data, y_data)
        
        # Get uncertainties
        uncertainties = manager.getFitUncertainties(curve_id, fit_id)
        assert uncertainties is not None
        assert "slope" in uncertainties
        assert "intercept" in uncertainties
        
        # Uncertainties should be positive numbers
        assert uncertainties["slope"] >= 0
        assert uncertainties["intercept"] >= 0
    
    def test_fit_quality_metrics(self) -> None:
        """Test that fit quality metrics are reasonable."""
        manager = FitManager()
        
        # Create synthetic data with good signal-to-noise
        x_data = np.linspace(0, 10, 100)
        y_data = 2 * x_data + 1 + 0.01 * np.random.normal(size=len(x_data))  # Low noise
        
        curve_id = "test_curve"
        fit_id = manager.addFit(curve_id, "Linear", x_data, y_data)
        
        # Get quality metrics
        metrics = manager.getFitQualityMetrics(curve_id, fit_id)
        assert metrics is not None
        
        # R-squared should be very high for this clean data
        assert metrics["r_squared"] > 0.99
        
        # Chi-squared should be positive
        assert metrics["chi_squared"] > 0
        
        # Reduced chi-squared should be reasonable (very small for excellent fit with low noise)
        assert metrics["reduced_chi_squared"] > 0
        assert metrics["reduced_chi_squared"] < 10.0  # Allow for very good fits
    
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
            fit_id = manager.addFit(curve_id, model_name, x_data, y_data)
            
            # Verify fit was successful
            fit_data = manager.getFitData(curve_id, fit_id)
            assert fit_data.model_name == model_name
            
            # Get parameters
            parameters = manager.getFitParameters(curve_id, fit_id)
            assert parameters is not None
            
            # Get quality metrics
            metrics = manager.getFitQualityMetrics(curve_id, fit_id)
            assert metrics is not None
            assert metrics["r_squared"] > 0.8  # Should fit reasonably well 