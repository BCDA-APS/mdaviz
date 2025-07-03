"""
Tests for cursor nearest point finding and cursor range functionality.
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch

from src.mdaviz.chartview import ChartView


class TestNearestPointFinding:
    """Test nearest point finding functionality."""

    def test_find_nearest_point_basic(self):
        """Test basic nearest point finding."""
        # Create a mock chart view
        chart_view = ChartView(Mock())

        # Mock curve data
        x_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

        # Mock curve manager and data
        chart_view.curveManager = Mock()
        chart_view.curveManager.curves.return_value = {"test_curve": "exists"}
        chart_view.curveManager.getCurveData.return_value = {
            "ds": [x_data, y_data],
            "factor": 1.0,
            "offset": 0.0,
        }

        # Mock getSelectedCurveID
        chart_view.getSelectedCurveID = Mock(return_value="test_curve")

        # Test finding nearest point
        result = chart_view.findNearestPoint(2.5, 25.0)

        assert result is not None
        x_nearest, y_nearest = result
        assert x_nearest == 3.0  # Should find the closest x value
        assert y_nearest == 30.0  # Corresponding y value

    def test_find_nearest_point_with_offset_factor(self):
        """Test nearest point finding with offset and factor applied."""
        chart_view = ChartView(Mock())

        x_data = np.array([1.0, 2.0, 3.0])
        y_data = np.array([10.0, 20.0, 30.0])

        chart_view.curveManager = Mock()
        chart_view.curveManager.curves.return_value = {"test_curve": "exists"}
        chart_view.curveManager.getCurveData.return_value = {
            "ds": [x_data, y_data],
            "factor": 2.0,  # Multiply y by 2
            "offset": 5.0,  # Add 5 to y
        }

        chart_view.getSelectedCurveID = Mock(return_value="test_curve")

        # With factor=2 and offset=5, y values become: [25, 45, 65]
        result = chart_view.findNearestPoint(2.0, 50.0)

        assert result is not None
        x_nearest, y_nearest = result
        assert x_nearest == 2.0
        assert y_nearest == 45.0  # 20 * 2 + 5

    def test_find_nearest_point_no_curve_selected(self):
        """Test nearest point finding when no curve is selected."""
        chart_view = ChartView(Mock())
        chart_view.getSelectedCurveID = Mock(return_value="")

        result = chart_view.findNearestPoint(1.0, 1.0)
        assert result is None

    def test_find_nearest_point_curve_not_found(self):
        """Test nearest point finding when curve is not found."""
        chart_view = ChartView(Mock())
        chart_view.curveManager = Mock()
        chart_view.curveManager.curves.return_value = {}
        chart_view.getSelectedCurveID = Mock(return_value="nonexistent_curve")

        result = chart_view.findNearestPoint(1.0, 1.0)
        assert result is None

    def test_find_nearest_point_no_curve_data(self):
        """Test nearest point finding when curve has no data."""
        chart_view = ChartView(Mock())
        chart_view.curveManager = Mock()
        chart_view.curveManager.curves.return_value = {"test_curve": "exists"}
        chart_view.curveManager.getCurveData.return_value = None
        chart_view.getSelectedCurveID = Mock(return_value="test_curve")

        result = chart_view.findNearestPoint(1.0, 1.0)
        assert result is None

    def test_find_nearest_point_invalid_data(self):
        """Test nearest point finding with invalid data structure."""
        chart_view = ChartView(Mock())
        chart_view.curveManager = Mock()
        chart_view.curveManager.curves.return_value = {"test_curve": "exists"}
        chart_view.curveManager.getCurveData.return_value = {
            "ds": [np.array([1.0])],  # Only x data, no y data
            "factor": 1.0,
            "offset": 0.0,
        }
        chart_view.getSelectedCurveID = Mock(return_value="test_curve")

        result = chart_view.findNearestPoint(1.0, 1.0)
        assert result is None


class TestCursorRange:
    """Test cursor range functionality."""

    def test_get_cursor_range_both_cursors_set(self):
        """Test getting cursor range when both cursors are set."""
        chart_view = ChartView(Mock())

        # Set up cursors
        chart_view.cursors = {
            1: Mock(),
            "pos1": (1.0, 10.0),
            2: Mock(),
            "pos2": (5.0, 50.0),
        }

        result = chart_view.getCursorRange()
        assert result == (1.0, 5.0)  # Should return (min_x, max_x)

    def test_get_cursor_range_reversed_order(self):
        """Test getting cursor range when cursors are in reverse order."""
        chart_view = ChartView(Mock())

        chart_view.cursors = {
            1: Mock(),
            "pos1": (5.0, 50.0),
            2: Mock(),
            "pos2": (1.0, 10.0),
        }

        result = chart_view.getCursorRange()
        assert result == (1.0, 5.0)  # Should still return (min_x, max_x)

    def test_get_cursor_range_one_cursor_missing(self):
        """Test getting cursor range when one cursor is missing."""
        chart_view = ChartView(Mock())

        chart_view.cursors = {1: Mock(), "pos1": (1.0, 10.0), 2: None, "pos2": None}

        result = chart_view.getCursorRange()
        assert result is None

    def test_get_cursor_range_no_cursors(self):
        """Test getting cursor range when no cursors are set."""
        chart_view = ChartView(Mock())

        chart_view.cursors = {1: None, "pos1": None, 2: None, "pos2": None}

        result = chart_view.getCursorRange()
        assert result is None


class TestCursorIntegration:
    """Test integration of cursor functionality with fitting."""

    @patch("src.mdaviz.chartview.ChartView.findNearestPoint")
    def test_onclick_uses_nearest_point(self, mock_find_nearest):
        """Test that onclick uses nearest point finding."""
        chart_view = ChartView(Mock())

        # Mock the nearest point finding
        mock_find_nearest.return_value = (2.5, 25.0)

        # Mock matplotlib event
        event = Mock()
        event.inaxes = chart_view.main_axes
        event.button = 2  # Middle button
        event.xdata = 2.3
        event.ydata = 23.0

        # Mock cursor storage
        chart_view.cursors = {1: None, "pos1": None, 2: None, "pos2": None}

        # Mock matplotlib plotting
        mock_line = Mock()
        chart_view.main_axes.plot.return_value = [mock_line]

        # Call onclick
        chart_view.onclick(event)

        # Verify nearest point was called
        mock_find_nearest.assert_called_once_with(2.3, 23.0)

        # Verify cursor was placed at nearest point
        assert chart_view.cursors["pos1"] == (2.5, 25.0)

    @patch("src.mdaviz.chartview.ChartView.findNearestPoint")
    def test_onclick_no_nearest_point(self, mock_find_nearest):
        """Test onclick behavior when no nearest point is found."""
        chart_view = ChartView(Mock())

        # Mock no nearest point found
        mock_find_nearest.return_value = None

        event = Mock()
        event.inaxes = chart_view.main_axes
        event.button = 2
        event.xdata = 2.3
        event.ydata = 23.0

        chart_view.cursors = {1: None, "pos1": None, 2: None, "pos2": None}

        chart_view.main_axes.plot.return_value = [Mock()]

        # Call onclick
        chart_view.onclick(event)

        # Verify no cursor was placed
        assert chart_view.cursors["pos1"] is None
        assert chart_view.cursors["pos2"] is None


if __name__ == "__main__":
    pytest.main([__file__])
