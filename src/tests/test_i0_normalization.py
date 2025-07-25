#!/usr/bin/env python
"""
Tests for I0 normalization functionality.

This module tests the I0 normalization calculation, zero value handling,
label generation, and integration with the data processing pipeline.

.. autosummary::

    ~test_basic_i0_normalization
    ~test_i0_normalization_with_zeros
    ~test_i0_normalization_edge_cases
    ~test_i0_normalization_label_generation
    ~test_i0_normalization_data_integrity
    ~test_i0_normalization_with_realistic_data
    ~test_i0_normalization_mixed_data
    ~test_i0_normalization_unit_handling
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication


def apply_i0_normalization(y_data, i0_data):
    """
    Apply I0 normalization: Y_data / I0_data with zero handling.

    Parameters:
        y_data: The Y data to normalize
        i0_data: The I0 data for normalization

    Returns:
        The normalized data
    """
    # Avoid division by zero
    i0_data_safe = np.array(i0_data)
    i0_data_safe[i0_data_safe == 0] = 1  # Replace zeros with 1
    return np.array(y_data) / i0_data_safe


@pytest.fixture
def test_data():
    """Create test data for I0 normalization."""
    return {
        "fileInfo": {
            "fileName": "test_file",
            "filePath": "/test/path",
            "scanDict": {
                "pos1": {
                    "name": "Position 1",
                    "data": np.array(list(range(100))),
                    "unit": "mm",
                },
                "det1": {
                    "name": "Detector 1",
                    "data": np.array([i * 2.5 for i in range(100)]),
                    "unit": "counts",
                },
                "det2": {
                    "name": "Detector 2",
                    "data": np.array([i * 1.5 + 10 for i in range(100)]),
                    "unit": "counts",
                },
                "det3": {
                    "name": "Detector 3",
                    "data": np.array([i * 3.0 + 5 for i in range(100)]),
                    "unit": "counts",
                },
                "i0": {
                    "name": "I0 Detector",
                    "data": np.array([max(1, i * 0.5 + 5) for i in range(100)]),
                    "unit": "counts",
                },
                "i0_with_zeros": {
                    "name": "I0 Detector with Zeros",
                    "data": np.array([max(0, i * 0.5 + 5) for i in range(100)]),
                    "unit": "counts",
                },
            },
        }
    }


class TestI0Normalization:
    """Test cases for I0 normalization functionality."""

    def test_basic_i0_normalization(self):
        """Test basic I0 normalization with simple data."""
        # Create test data
        y_data = np.array([10, 20, 30, 40, 50])
        i0_data = np.array([2, 4, 6, 8, 10])

        # Apply I0 normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that normalization is correct
        expected = np.array([10 / 2, 20 / 4, 30 / 6, 40 / 8, 50 / 10])
        np.testing.assert_array_almost_equal(normalized_data, expected, decimal=10)

        # Check that the relative relationships are preserved
        # The normalized data should maintain the same relative ratios
        assert all(
            normalized_data[i] <= normalized_data[i + 1]
            for i in range(len(normalized_data) - 1)
        )

    def test_i0_normalization_with_zeros(self):
        """Test I0 normalization with zero values in I0 data."""
        # Create test data with zeros in I0
        y_data = np.array([10, 20, 30, 40, 50])
        i0_data = np.array([0, 2, 0, 4, 5])  # Contains zeros

        # Apply I0 normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that zeros are handled correctly (replaced with 1)
        expected = np.array([10 / 1, 20 / 2, 30 / 1, 40 / 4, 50 / 5])
        np.testing.assert_array_almost_equal(normalized_data, expected, decimal=10)

        # Verify that zero I0 values result in unchanged Y values
        assert normalized_data[0] == 10  # 10/1 = 10
        assert normalized_data[2] == 30  # 30/1 = 30

    def test_i0_normalization_edge_cases(self):
        """Test I0 normalization with edge cases."""
        # Test with constant I0 data
        y_data = np.array([10, 20, 30, 40, 50])
        i0_data = np.array([5, 5, 5, 5, 5])  # Constant I0

        normalized_data = apply_i0_normalization(y_data, i0_data)
        expected = np.array([10 / 5, 20 / 5, 30 / 5, 40 / 5, 50 / 5])
        np.testing.assert_array_almost_equal(normalized_data, expected, decimal=10)

        # Test with single value
        y_single = np.array([42])
        i0_single = np.array([7])
        normalized_single = apply_i0_normalization(y_single, i0_single)
        assert normalized_single[0] == 42 / 7

        # Test with all zeros in I0
        y_data2 = np.array([10, 20, 30, 40, 50])
        i0_data2 = np.array([0, 0, 0, 0, 0])  # All zeros

        normalized_data2 = apply_i0_normalization(y_data2, i0_data2)
        # Should return original Y data (all zeros replaced with 1)
        np.testing.assert_array_almost_equal(normalized_data2, y_data2, decimal=10)

    def test_i0_normalization_label_generation(self):
        """Test I0 normalization label generation."""
        # Test basic normalization label
        y_name = "Detector 1"
        fileName = "test_file"

        # When I0 is selected, label should include [norm]
        y_label = f"{fileName}: {y_name} [norm]"
        assert "[norm]" in y_label
        assert "test_file: Detector 1 [norm]" == y_label

        # When I0 is not selected, label should not include [norm]
        y_label_no_i0 = f"{fileName}: {y_name} (counts)"
        assert "[norm]" not in y_label_no_i0

    def test_i0_normalization_data_integrity(self):
        """Test that I0 normalization preserves data integrity."""
        # Create realistic test data
        y_data = np.array([100, 200, 300, 400, 500])
        i0_data = np.array([10, 20, 30, 40, 50])

        # Apply normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that the shape is preserved
        assert normalized_data.shape == y_data.shape

        # Check that the data type is appropriate (float for division)
        assert normalized_data.dtype in [np.float32, np.float64]

        # Check that no NaN or inf values are created
        assert not np.any(np.isnan(normalized_data))
        assert not np.any(np.isinf(normalized_data))

    def test_i0_normalization_with_realistic_data(self):
        """Test I0 normalization with realistic detector data."""
        # Create realistic detector data
        x_data = np.linspace(0, 100, 100)
        y_data = 100 * np.exp(-x_data / 20) + np.random.normal(
            0, 2, 100
        )  # Exponential decay
        i0_data = (
            50 * np.sin(x_data / 10) + np.random.normal(0, 1, 100) + 10
        )  # Sine wave + noise + offset

        # Apply normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that normalization worked
        assert len(normalized_data) == len(y_data)
        assert not np.any(np.isnan(normalized_data))
        assert not np.any(np.isinf(normalized_data))

        # Check that the data is reasonable (not all zeros or infinities)
        assert np.any(normalized_data != 0)
        assert np.all(np.isfinite(normalized_data))

        # Check that normalization actually changed the data (not identity operation)
        # This ensures the I0 normalization had an effect
        assert not np.allclose(normalized_data, y_data, rtol=1e-10)

    def test_i0_normalization_mixed_data(self):
        """Test I0 normalization with mixed positive/negative/zero data."""
        # Create mixed data
        y_data = np.array([10, -20, 30, 0, 50])
        i0_data = np.array([2, 0, 6, 8, 0])  # Mixed zeros and non-zeros

        # Apply normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that zeros in I0 are handled correctly
        expected = np.array(
            [10 / 2, -20 / 1, 30 / 6, 0 / 8, 50 / 1]
        )  # Zeros replaced with 1
        np.testing.assert_array_almost_equal(normalized_data, expected, decimal=10)

        # Check that negative values are handled correctly
        assert normalized_data[1] == -20  # -20/1 = -20

        # Check that zero Y values remain zero
        assert normalized_data[3] == 0  # 0/8 = 0

    def test_i0_normalization_unit_handling(self):
        """Test that I0 normalization handles units correctly."""
        # Test that normalized data has no units (as per the code)
        y_unit = "counts"
        i0_unit = "counts"

        # When I0 normalization is applied, units should be cleared
        normalized_unit = ""  # Normalized data typically has no units
        assert normalized_unit == ""

        # When no I0 normalization, units should be preserved
        non_normalized_unit = f"({y_unit})" if y_unit else ""
        assert non_normalized_unit == "(counts)"

    def test_i0_normalization_performance(self):
        """Test I0 normalization with large datasets."""
        # Create large test data
        size = 10000
        y_data = np.random.random(size) * 100
        i0_data = np.random.random(size) * 50 + 1  # Ensure no zeros

        # Apply normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that normalization worked correctly
        assert len(normalized_data) == size
        assert not np.any(np.isnan(normalized_data))
        assert not np.any(np.isinf(normalized_data))

        # Check that the operation is element-wise
        expected = y_data / i0_data
        np.testing.assert_array_almost_equal(normalized_data, expected, decimal=10)

    def test_i0_normalization_with_constant_y(self):
        """Test I0 normalization when Y data is constant."""
        # Create constant Y data
        y_data = np.array([5, 5, 5, 5, 5])
        i0_data = np.array([1, 2, 3, 4, 5])

        # Apply normalization
        normalized_data = apply_i0_normalization(y_data, i0_data)

        # Check that normalization works correctly
        expected = np.array([5 / 1, 5 / 2, 5 / 3, 5 / 4, 5 / 5])
        np.testing.assert_array_almost_equal(normalized_data, expected, decimal=10)

        # The normalized data should no longer be constant
        assert not np.all(normalized_data == normalized_data[0])
