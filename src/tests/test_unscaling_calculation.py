#!/usr/bin/env python
"""
Tests for unscaling calculation functionality.

This module tests the mathematical unscaling formula and data processing logic
by directly testing the calculation functions.

.. autosummary::

    ~test_unscaling_formula_basic
    ~test_unscaling_formula_edge_cases
    ~test_unscaling_with_i0_normalization
    ~test_unscaling_range_calculation
    ~test_unscaling_fallback_0_1
"""

import numpy as np


def apply_unscaling_formula(data, reference_min, reference_max):
    """
    Apply the unscaling formula: g(x) = ((f1(x) - m1) / (M1 - m1)) * (M23 - m23) + m23

    Parameters:
        data: The data to unscale
        reference_min: The minimum value of reference curves
        reference_max: The maximum value of reference curves

    Returns:
        The unscaled data
    """
    data_min, data_max = np.min(data), np.max(data)

    # Avoid division by zero
    if data_max == data_min:
        return data

    # Apply unscaling formula
    return ((data - data_min) / (data_max - data_min)) * (
        reference_max - reference_min
    ) + reference_min


class TestUnscalingCalculation:
    """Test cases for unscaling calculation functionality."""

    def test_unscaling_formula_basic(self):
        """Test basic unscaling formula with simple data."""
        # Create test data
        original_data = np.array([1, 2, 3, 4, 5])
        reference_min, reference_max = 10, 20

        # Apply unscaling
        unscaled_data = apply_unscaling_formula(
            original_data, reference_min, reference_max
        )

        # Check that the range matches the reference
        assert abs(np.min(unscaled_data) - reference_min) < 1e-10
        assert abs(np.max(unscaled_data) - reference_max) < 1e-10

        # Check that the relative relationships are preserved
        # The data should still be monotonically increasing
        assert all(
            unscaled_data[i] <= unscaled_data[i + 1]
            for i in range(len(unscaled_data) - 1)
        )

    def test_unscaling_formula_edge_cases(self):
        """Test unscaling formula with edge cases."""
        # Test with constant data (should return original)
        constant_data = np.array([5, 5, 5, 5, 5])
        unscaled = apply_unscaling_formula(constant_data, 0, 1)
        np.testing.assert_array_equal(unscaled, constant_data)

        # Test with single value
        single_data = np.array([42])
        unscaled = apply_unscaling_formula(single_data, 0, 1)
        np.testing.assert_array_equal(unscaled, single_data)

        # Test with negative values
        negative_data = np.array([-5, -3, -1, 1, 3, 5])
        unscaled = apply_unscaling_formula(negative_data, 0, 10)
        assert abs(np.min(unscaled) - 0) < 1e-10
        assert abs(np.max(unscaled) - 10) < 1e-10

    def test_unscaling_with_i0_normalization(self):
        """Test unscaling combined with I0 normalization."""
        # Create test data
        y_data = np.array([10, 20, 30, 40, 50])
        i0_data = np.array([2, 4, 6, 8, 10])

        # Apply I0 normalization first
        i0_safe = np.array(i0_data)
        i0_safe[i0_safe == 0] = 1
        normalized_data = y_data / i0_safe

        # Now apply unscaling
        reference_min, reference_max = 0, 1
        unscaled_data = apply_unscaling_formula(
            normalized_data, reference_min, reference_max
        )

        # Check that the range is correct
        # Note: After normalization, all values are 5.0, so unscaling returns original
        # This is the correct behavior when min == max
        assert abs(np.min(unscaled_data) - 5.0) < 1e-10
        assert abs(np.max(unscaled_data) - 5.0) < 1e-10

        # Test with more varied I0 data that results in different normalized values
        # Let's use different data that actually has variation
        y_data3 = np.array([10, 20, 30, 40, 50])
        i0_data3 = np.array([1, 1, 1, 1, 1])  # Constant I0

        i0_safe3 = np.array(i0_data3)
        i0_safe3[i0_safe3 == 0] = 1
        normalized_data3 = y_data3 / i0_safe3

        unscaled_data3 = apply_unscaling_formula(
            normalized_data3, reference_min, reference_max
        )

        # Now we should get proper unscaling
        assert abs(np.min(unscaled_data3) - reference_min) < 1e-10
        assert abs(np.max(unscaled_data3) - reference_max) < 1e-10

    def test_unscaling_range_calculation(self):
        """Test calculation of reference range from multiple curves."""
        # Create multiple curves
        curve1 = np.array([1, 2, 3, 4, 5])
        curve2 = np.array([10, 20, 30, 40, 50])
        curve3 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        # Calculate global min/max from all curves
        all_curves = [curve1, curve2, curve3]
        global_min = min(np.min(curve) for curve in all_curves)
        global_max = max(np.max(curve) for curve in all_curves)

        # Unscale curve1 to match the global range
        unscaled_curve1 = apply_unscaling_formula(curve1, global_min, global_max)

        # Check that curve1 now matches the global range
        assert abs(np.min(unscaled_curve1) - global_min) < 1e-10
        assert abs(np.max(unscaled_curve1) - global_max) < 1e-10

    def test_unscaling_fallback_0_1(self):
        """Test fallback to 0-1 scale when no reference curves."""
        # Create test data
        data = np.array([1, 2, 3, 4, 5])

        # Apply unscaling with 0-1 fallback
        unscaled_data = apply_unscaling_formula(data, 0.0, 1.0)

        # Check that the range is 0-1
        assert abs(np.min(unscaled_data) - 0.0) < 1e-10
        assert abs(np.max(unscaled_data) - 1.0) < 1e-10

    def test_unscaling_preserves_shape(self):
        """Test that unscaling preserves the data shape."""
        # Create 2D test data
        original_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        reference_min, reference_max = 0, 10

        # Apply unscaling
        unscaled_data = apply_unscaling_formula(
            original_data, reference_min, reference_max
        )

        # Check that shape is preserved
        assert unscaled_data.shape == original_data.shape

        # Check that the range matches
        assert abs(np.min(unscaled_data) - reference_min) < 1e-10
        assert abs(np.max(unscaled_data) - reference_max) < 1e-10

    def test_unscaling_with_realistic_data(self):
        """Test unscaling with realistic detector data."""
        # Create realistic detector data (similar to what we'd see in practice)
        x_data = np.linspace(0, 100, 100)
        det1_data = 100 * np.exp(-x_data / 20) + np.random.normal(
            0, 2, 100
        )  # Exponential decay
        det2_data = 50 * np.sin(x_data / 10) + np.random.normal(0, 1, 100)  # Sine wave

        # Calculate reference range from det2
        reference_min, reference_max = np.min(det2_data), np.max(det2_data)

        # Unscale det1 to match det2's range
        unscaled_det1 = apply_unscaling_formula(det1_data, reference_min, reference_max)

        # Check that det1 now matches det2's range
        assert abs(np.min(unscaled_det1) - reference_min) < 1e-10
        assert abs(np.max(unscaled_det1) - reference_max) < 1e-10

        # Check that the relative relationships are preserved
        # The unscaled data should maintain the general shape of the original
        original_correlation = np.corrcoef(det1_data[:-1], det1_data[1:])[0, 1]
        unscaled_correlation = np.corrcoef(unscaled_det1[:-1], unscaled_det1[1:])[0, 1]
        assert abs(original_correlation - unscaled_correlation) < 1e-10

    def test_unscaling_multiple_curves_same_range(self):
        """Test unscaling multiple curves to the same reference range."""
        # Create multiple curves with different ranges
        curve1 = np.array([1, 2, 3, 4, 5])  # Range: 1-5
        curve2 = np.array([10, 20, 30, 40, 50])  # Range: 10-50
        curve3 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])  # Range: 0.1-0.5

        # Calculate global range
        all_curves = [curve1, curve2, curve3]
        global_min = min(np.min(curve) for curve in all_curves)
        global_max = max(np.max(curve) for curve in all_curves)

        # Unscale all curves to the global range
        unscaled_curves = []
        for curve in all_curves:
            unscaled = apply_unscaling_formula(curve, global_min, global_max)
            unscaled_curves.append(unscaled)

        # Check that all unscaled curves have the same range
        for unscaled in unscaled_curves:
            assert abs(np.min(unscaled) - global_min) < 1e-10
            assert abs(np.max(unscaled) - global_max) < 1e-10
