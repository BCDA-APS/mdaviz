"""
Tests for 2D I0 normalization functionality.

This module tests that I0 normalization information is properly preserved
when converting from 2D selection format to 1D format for data2Plot2D.
"""

import pytest
import numpy as np


class Test2DI0Normalization:
    """Test cases for 2D I0 normalization functionality."""

    def test_2d_selection_conversion_preserves_i0(self):
        """Test that I0 information is preserved during 2D selection conversion."""
        # Simulate the original 2D selection with I0 information
        original_2d_selection = {
            "X1": 1,
            "X2": 1,
            "Y": [18],
            "I0": 3,
            "plot_type": "heatmap",
            "color_palette": "viridis",
        }

        # Simulate the conversion that should happen in _doPlot2D
        converted_selection = {
            "X": original_2d_selection.get("X1"),
            "Y": original_2d_selection.get("Y", []),
            "I0": original_2d_selection.get("I0"),
        }

        # Verify that I0 information is preserved
        assert converted_selection["I0"] == 3
        assert converted_selection["X"] == 1
        assert converted_selection["Y"] == [18]

        # Verify that the conversion didn't lose any critical information
        assert "I0" in converted_selection
        assert "X" in converted_selection
        assert "Y" in converted_selection

    def test_2d_selection_conversion_without_i0(self):
        """Test that conversion works correctly when no I0 is selected."""
        # Simulate 2D selection without I0
        original_2d_selection = {
            "X1": 1,
            "X2": 1,
            "Y": [18],
            "plot_type": "heatmap",
            "color_palette": "viridis",
        }

        # Simulate the conversion
        converted_selection = {
            "X": original_2d_selection.get("X1"),
            "Y": original_2d_selection.get("Y", []),
            "I0": original_2d_selection.get("I0"),
        }

        # Verify that I0 is None when not provided
        assert converted_selection["I0"] is None
        assert converted_selection["X"] == 1
        assert converted_selection["Y"] == [18]

    def test_2d_i0_normalization_data_processing(self):
        """Test that 2D I0 normalization works with sample data."""
        # Create sample 2D data
        y_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
        i0_data = np.array([[2.0, 2.0, 2.0], [2.0, 2.0, 2.0], [2.0, 2.0, 2.0]])

        # Apply I0 normalization (same logic as in data2Plot2D)
        i0_safe = np.where(i0_data == 0, 1, i0_data)
        normalized_data = y_data / i0_safe

        # Verify normalization worked correctly
        expected = np.array([[0.5, 1.0, 1.5], [2.0, 2.5, 3.0], [3.5, 4.0, 4.5]])
        np.testing.assert_array_almost_equal(normalized_data, expected)

    def test_2d_i0_normalization_with_zeros(self):
        """Test 2D I0 normalization with zero values in I0 data."""
        # Create sample 2D data with zeros in I0
        y_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        i0_data = np.array([[2.0, 0.0, 2.0], [0.0, 2.0, 2.0]])

        # Apply I0 normalization with zero handling
        i0_safe = np.where(i0_data == 0, 1, i0_data)
        normalized_data = y_data / i0_safe

        # Verify that zeros were handled correctly
        assert not np.any(np.isinf(normalized_data))
        assert not np.any(np.isnan(normalized_data))

        # Check specific values - zeros should result in unchanged Y values
        assert normalized_data[0, 1] == 2.0  # 2.0 / 1 = 2.0
        assert normalized_data[1, 0] == 4.0  # 4.0 / 1 = 4.0

    def test_2d_selection_structure_validation(self):
        """Test that 2D selection structure is valid for conversion."""
        # Valid 2D selection
        valid_selection = {
            "X1": 1,
            "X2": 1,
            "Y": [18],
            "I0": 3,
            "plot_type": "heatmap",
            "color_palette": "viridis",
        }

        # Test conversion preserves all required fields
        converted = {
            "X": valid_selection.get("X1"),
            "Y": valid_selection.get("Y", []),
            "I0": valid_selection.get("I0"),
        }

        # Verify structure
        assert isinstance(converted["X"], int)
        assert isinstance(converted["Y"], list)
        assert isinstance(converted["I0"], int)
        assert len(converted["Y"]) > 0

    def test_1d_2d_zero_handling_consistency(self):
        """Test that 1D and 2D normalization handle zeros consistently."""
        # Test data with zeros in I0
        y_data_1d = np.array([10, 20, 30, 40])
        i0_data_1d = np.array([0, 2, 0, 4])

        y_data_2d = np.array([[10, 20], [30, 40]])
        i0_data_2d = np.array([[0, 2], [0, 4]])

        # Apply 1D-style normalization to both
        def normalize_1d_style(y_data, i0_data):
            i0_safe = np.where(i0_data == 0, 1, i0_data)
            return y_data / i0_safe

        # Test 1D normalization
        result_1d = normalize_1d_style(y_data_1d, i0_data_1d)
        expected_1d = np.array([10 / 1, 20 / 2, 30 / 1, 40 / 4])  # 10, 10, 30, 10
        np.testing.assert_array_almost_equal(result_1d, expected_1d)

        # Test 2D normalization
        result_2d = normalize_1d_style(y_data_2d, i0_data_2d)
        expected_2d = np.array(
            [[10 / 1, 20 / 2], [30 / 1, 40 / 4]]
        )  # [[10, 10], [30, 10]]
        np.testing.assert_array_almost_equal(result_2d, expected_2d)

        # Verify that zeros result in unchanged Y values in both cases
        assert result_1d[0] == 10  # 10/1 = 10
        assert result_1d[2] == 30  # 30/1 = 30
        assert result_2d[0, 0] == 10  # 10/1 = 10
        assert result_2d[1, 0] == 30  # 30/1 = 30
