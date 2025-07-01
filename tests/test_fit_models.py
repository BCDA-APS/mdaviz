"""
Tests for fit models functionality.

This module contains tests for the fit models used in the mdaviz application.
"""

from typing import TYPE_CHECKING
import numpy as np
import pytest
from unittest.mock import Mock, patch

from mdaviz.fit_models import (
    FitModel, FitResult, GaussianFit, LorentzianFit, 
    LinearFit, ExponentialFit, PolynomialFit, get_available_models
)

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestFitResult:
    """Test FitResult class."""
    
    def test_fit_result_initialization(self) -> None:
        """Test FitResult initialization with valid parameters."""
        parameters = {"a": 1.0, "b": 2.0}
        uncertainties = {"a": 0.1, "b": 0.2}
        r_squared = 0.95
        chi_squared = 10.5
        reduced_chi_squared = 1.05
        fit_curve = np.array([1.0, 2.0, 3.0])
        x_fit = np.array([0.0, 1.0, 2.0])
        
        result = FitResult(
            parameters=parameters,
            uncertainties=uncertainties,
            r_squared=r_squared,
            chi_squared=chi_squared,
            reduced_chi_squared=reduced_chi_squared,
            fit_curve=fit_curve,
            x_fit=x_fit
        )
        
        assert result.parameters == parameters
        assert result.uncertainties == uncertainties
        assert result.r_squared == r_squared
        assert result.chi_squared == chi_squared
        assert result.reduced_chi_squared == reduced_chi_squared
        np.testing.assert_array_equal(result.fit_curve, fit_curve)
        np.testing.assert_array_equal(result.x_fit, x_fit)


class TestFitModel:
    """Test base FitModel class."""
    
    def test_fit_model_initialization(self) -> None:
        """Test FitModel initialization."""
        def test_function(x, a, b):
            return a * x + b
        
        model = FitModel("Test", test_function, ["a", "b"])
        
        assert model.name == "Test"
        assert model.function == test_function
        assert model.parameters == ["a", "b"]
    
    def test_get_default_initial_guess(self) -> None:
        """Test default initial guess method."""
        def test_function(x, a, b):
            return a * x + b
        
        model = FitModel("Test", test_function, ["a", "b"])
        x_data = np.array([1, 2, 3])
        y_data = np.array([2, 4, 6])
        
        guess = model._get_default_initial_guess(x_data, y_data)
        
        assert guess == {"a": 1.0, "b": 1.0}


class TestGaussianFit:
    """Test GaussianFit class."""
    
    def test_gaussian_fit_initialization(self) -> None:
        """Test GaussianFit initialization."""
        fit = GaussianFit()
        
        assert fit.name == "Gaussian"
        assert fit.parameters == ["amplitude", "center", "sigma", "offset"]
    
    def test_gaussian_function(self) -> None:
        """Test Gaussian function calculation."""
        fit = GaussianFit()
        x = np.array([0, 1, 2])
        amplitude = 2.0
        center = 1.0
        sigma = 0.5
        offset = 1.0
        
        result = fit._gaussian_function(x, amplitude, center, sigma, offset)
        
        assert len(result) == 3
        assert result[1] > result[0]  # Peak should be at center
        assert result[1] > result[2]  # Peak should be at center
    
    def test_gaussian_fit_with_synthetic_data(self) -> None:
        """Test Gaussian fit with synthetic data."""
        fit = GaussianFit()
        
        # Create synthetic Gaussian data
        x = np.linspace(-5, 5, 100)
        true_params = {"amplitude": 2.0, "center": 0.0, "sigma": 1.0, "offset": 0.5}
        y = fit._gaussian_function(x, **true_params) + 0.1 * np.random.normal(size=len(x))
        
        # Perform fit
        result = fit.fit(x, y)
        
        # Check that fit parameters are close to true values
        assert abs(result.parameters["amplitude"] - true_params["amplitude"]) < 0.5
        assert abs(result.parameters["center"] - true_params["center"]) < 0.5
        assert abs(result.parameters["sigma"] - true_params["sigma"]) < 0.5
        assert abs(result.parameters["offset"] - true_params["offset"]) < 0.5
        
        # Check quality metrics
        assert result.r_squared > 0.8
        assert result.chi_squared > 0
        assert result.reduced_chi_squared > 0


class TestLorentzianFit:
    """Test LorentzianFit class."""
    
    def test_lorentzian_fit_initialization(self) -> None:
        """Test LorentzianFit initialization."""
        fit = LorentzianFit()
        
        assert fit.name == "Lorentzian"
        assert fit.parameters == ["amplitude", "center", "gamma", "offset"]
    
    def test_lorentzian_function(self) -> None:
        """Test Lorentzian function calculation."""
        fit = LorentzianFit()
        x = np.array([0, 1, 2])
        amplitude = 2.0
        center = 1.0
        gamma = 0.5
        offset = 1.0
        
        result = fit._lorentzian_function(x, amplitude, center, gamma, offset)
        
        assert len(result) == 3
        assert result[1] > result[0]  # Peak should be at center
        assert result[1] > result[2]  # Peak should be at center


class TestLinearFit:
    """Test LinearFit class."""
    
    def test_linear_fit_initialization(self) -> None:
        """Test LinearFit initialization."""
        fit = LinearFit()
        
        assert fit.name == "Linear"
        assert fit.parameters == ["slope", "intercept"]
    
    def test_linear_function(self) -> None:
        """Test linear function calculation."""
        fit = LinearFit()
        x = np.array([0, 1, 2])
        slope = 2.0
        intercept = 1.0
        
        result = fit._linear_function(x, slope, intercept)
        
        expected = np.array([1.0, 3.0, 5.0])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_linear_fit_with_synthetic_data(self) -> None:
        """Test linear fit with synthetic data."""
        fit = LinearFit()
        
        # Create synthetic linear data
        x = np.linspace(0, 10, 50)
        true_slope = 2.0
        true_intercept = 1.0
        y = true_slope * x + true_intercept + 0.1 * np.random.normal(size=len(x))
        
        # Perform fit
        result = fit.fit(x, y)
        
        # Check that fit parameters are close to true values
        assert abs(result.parameters["slope"] - true_slope) < 0.1
        assert abs(result.parameters["intercept"] - true_intercept) < 0.1
        
        # Check quality metrics
        assert result.r_squared > 0.9
        assert result.chi_squared > 0
        assert result.reduced_chi_squared > 0


class TestExponentialFit:
    """Test ExponentialFit class."""
    
    def test_exponential_fit_initialization(self) -> None:
        """Test ExponentialFit initialization."""
        fit = ExponentialFit()
        
        assert fit.name == "Exponential"
        assert fit.parameters == ["amplitude", "decay", "offset"]
    
    def test_exponential_function(self) -> None:
        """Test exponential function calculation."""
        fit = ExponentialFit()
        x = np.array([0, 1, 2])
        amplitude = 2.0
        decay = 1.0
        offset = 0.5
        
        result = fit._exponential_function(x, amplitude, decay, offset)
        
        assert len(result) == 3
        assert result[0] > result[1]  # Should decay
        assert result[1] > result[2]  # Should decay


class TestPolynomialFit:
    """Test PolynomialFit class."""
    
    def test_polynomial_fit_initialization(self) -> None:
        """Test PolynomialFit initialization."""
        fit = PolynomialFit(degree=2)
        
        assert fit.name == "Polynomial (deg=2)"
        assert fit.parameters == ["coeff_0", "coeff_1", "coeff_2"]
        assert fit.degree == 2
    
    def test_polynomial_function(self) -> None:
        """Test polynomial function calculation."""
        fit = PolynomialFit(degree=2)
        x = np.array([0, 1, 2])
        coeff_0 = 1.0
        coeff_1 = 2.0
        coeff_2 = 3.0
        
        result = fit._polynomial_function(x, coeff_0, coeff_1, coeff_2)
        
        # Should be 1 + 2*x + 3*x^2
        expected = np.array([1.0, 6.0, 17.0])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_polynomial_fit_with_synthetic_data(self) -> None:
        """Test polynomial fit with synthetic data."""
        fit = PolynomialFit(degree=2)
        
        # Create synthetic quadratic data
        x = np.linspace(-2, 2, 50)
        true_coeffs = [1.0, 2.0, 3.0]  # 1 + 2x + 3x^2
        y = true_coeffs[0] + true_coeffs[1] * x + true_coeffs[2] * x**2 + 0.1 * np.random.normal(size=len(x))
        
        # Perform fit
        result = fit.fit(x, y)
        
        # Check that fit parameters are close to true values
        for i, true_coeff in enumerate(true_coeffs):
            param_name = f"coeff_{i}"
            assert abs(result.parameters[param_name] - true_coeff) < 0.2
        
        # Check quality metrics
        assert result.r_squared > 0.9
        assert result.chi_squared > 0
        assert result.reduced_chi_squared > 0


class TestFitModelsIntegration:
    """Test integration of fit models."""
    
    def test_get_available_models(self) -> None:
        """Test get_available_models function."""
        models = get_available_models()
        
        # Check that expected models are available
        expected_models = ["Gaussian", "Lorentzian", "Linear", "Exponential", "Quadratic", "Cubic"]
        for model_name in expected_models:
            assert model_name in models
            assert isinstance(models[model_name], FitModel)
    
    def test_fit_with_nan_values(self) -> None:
        """Test that fit handles NaN values correctly."""
        fit = LinearFit()
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, np.nan, 6, 8, 10])  # One NaN value
        
        # Should not raise an error
        result = fit.fit(x, y)
        
        assert result.r_squared > 0.8  # Should still fit well to valid data
    
    def test_fit_with_insufficient_data(self) -> None:
        """Test that fit raises error with insufficient data."""
        fit = LinearFit()
        
        x = np.array([1])  # Only one data point
        y = np.array([2])
        
        with pytest.raises(ValueError, match="Not enough data points"):
            fit.fit(x, y)
    
    def test_fit_with_bounds(self) -> None:
        """Test fit with parameter bounds."""
        fit = LinearFit()
        
        x = np.array([0, 1, 2, 3, 4])
        y = np.array([1, 3, 5, 7, 9])
        
        bounds = {"slope": (1.5, 2.5), "intercept": (0.5, 1.5)}
        
        result = fit.fit(x, y, bounds=bounds)
        
        # Check that parameters are within bounds
        assert 1.5 <= result.parameters["slope"] <= 2.5
        assert 0.5 <= result.parameters["intercept"] <= 1.5
    
    def test_fit_with_initial_guess(self) -> None:
        """Test fit with initial parameter guesses."""
        fit = LinearFit()
        
        x = np.array([0, 1, 2, 3, 4])
        y = np.array([1, 3, 5, 7, 9])
        
        initial_guess = {"slope": 2.1, "intercept": 0.9}
        
        result = fit.fit(x, y, initial_guess=initial_guess)
        
        # Should converge to reasonable values
        assert abs(result.parameters["slope"] - 2.0) < 0.1
        assert abs(result.parameters["intercept"] - 1.0) < 0.1 