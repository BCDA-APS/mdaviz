#!/usr/bin/env python
"""
Tests for the mdaviz chartview module.

Covers ChartView widget functionality including curve management,
backend switching, and performance optimization.
"""

from typing import TYPE_CHECKING
import pytest
from unittest.mock import MagicMock, patch, Mock
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

from mdaviz.chartview import ChartView, MATPLOTLIB_AVAILABLE, PYQTGRAPH_AVAILABLE

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.capture import CaptureFixture
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def qt_app() -> QApplication:
    """Create QApplication instance for tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def chart_view(qt_app: QApplication) -> ChartView:
    """Create a ChartView instance for testing."""
    with patch('mdaviz.chartview.MATPLOTLIB_AVAILABLE', True), \
         patch('mdaviz.chartview.Figure') as mock_figure, \
         patch('mdaviz.chartview.FigureCanvas') as mock_canvas, \
         patch('mdaviz.chartview.plt'):
        
        # Setup mocks
        mock_fig_instance = Mock()
        mock_figure.return_value = mock_fig_instance
        mock_fig_instance.add_subplot.return_value = Mock()
        mock_fig_instance.patch.set_facecolor = Mock()
        mock_fig_instance.set_constrained_layout = Mock()
        
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        mock_canvas_instance.setParent = Mock()
        mock_canvas_instance.draw = Mock()
        
        return ChartView()


@pytest.fixture
def sample_data() -> tuple[list[float], list[float]]:
    """Create sample data for testing curves."""
    x_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_data = [1.0, 4.0, 9.0, 16.0, 25.0]
    return x_data, y_data


class TestChartViewInitialization:
    """Test ChartView initialization and setup."""

    @patch('mdaviz.chartview.MATPLOTLIB_AVAILABLE', True)
    @patch('mdaviz.chartview.Figure')
    @patch('mdaviz.chartview.FigureCanvas')
    @patch('mdaviz.chartview.plt')
    def test_default_initialization(self, mock_plt: Mock, mock_canvas: Mock, mock_figure: Mock, qt_app: QApplication) -> None:
        """Test ChartView with default parameters."""
        # Setup mocks
        mock_fig_instance = Mock()
        mock_figure.return_value = mock_fig_instance
        mock_fig_instance.add_subplot.return_value = Mock()
        
        chart = ChartView()
        
        assert chart.backend == "matplotlib"
        assert chart.max_curves == 50
        assert chart.enable_lazy_rendering is True
        assert chart.memory_limit_mb == 200.0
        assert chart._curve_count == 0
        assert len(chart._curves) == 0
        assert len(chart._curve_data) == 0

    @patch('mdaviz.chartview.MATPLOTLIB_AVAILABLE', True)
    @patch('mdaviz.chartview.Figure')
    @patch('mdaviz.chartview.FigureCanvas')
    @patch('mdaviz.chartview.plt')
    def test_custom_initialization(self, mock_plt: Mock, mock_canvas: Mock, mock_figure: Mock, qt_app: QApplication) -> None:
        """Test ChartView with custom parameters."""
        # Setup mocks
        mock_fig_instance = Mock()
        mock_figure.return_value = mock_fig_instance
        mock_fig_instance.add_subplot.return_value = Mock()
        
        chart = ChartView(
            backend="matplotlib",  # Force matplotlib since we're mocking it
            max_curves=25,
            enable_lazy_rendering=False,
            memory_limit_mb=100.0
        )
        
        assert chart.max_curves == 25
        assert chart.enable_lazy_rendering is False
        assert chart.memory_limit_mb == 100.0

    @patch('mdaviz.chartview.MATPLOTLIB_AVAILABLE', True)
    @patch('mdaviz.chartview.Figure')
    @patch('mdaviz.chartview.FigureCanvas')
    @patch('mdaviz.chartview.plt')
    def test_parent_widget(self, mock_plt: Mock, mock_canvas: Mock, mock_figure: Mock, qt_app: QApplication) -> None:
        """Test ChartView with parent widget."""
        # Setup mocks
        mock_fig_instance = Mock()
        mock_figure.return_value = mock_fig_instance
        mock_fig_instance.add_subplot.return_value = Mock()
        
        parent = QWidget()
        chart = ChartView(parent=parent)
        
        assert chart.parent() == parent

    @patch('mdaviz.chartview.MATPLOTLIB_AVAILABLE', False)
    @patch('mdaviz.chartview.PYQTGRAPH_AVAILABLE', False)
    def test_no_backend_available(self, qt_app: QApplication) -> None:
        """Test initialization when no plotting backend is available."""
        with pytest.raises(RuntimeError, match="No plotting backend available"):
            ChartView()


class TestChartViewCurveManagement:
    """Test curve addition, removal, and management."""

    def test_add_curve_success(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test successful curve addition."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            
            result = chart_view.add_curve("test_curve", x_data, y_data)
            
            assert result is True
            assert "test_curve" in chart_view._curves
            assert "test_curve" in chart_view._curve_data
            assert chart_view._curve_count == 1

    def test_add_curve_with_kwargs(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test curve addition with plotting kwargs."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            
            result = chart_view.add_curve("test_curve", x_data, y_data, color="red", linestyle="--")
            
            assert result is True
            assert "test_curve" in chart_view._curves

    def test_add_multiple_curves(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test adding multiple curves."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            
            result1 = chart_view.add_curve("curve1", x_data, y_data)
            result2 = chart_view.add_curve("curve2", x_data, [y * 2 for y in y_data])
            
            assert result1 is True
            assert result2 is True
            assert chart_view._curve_count == 2
            assert len(chart_view._curves) == 2

    def test_memory_limit_exceeded(self, chart_view: ChartView) -> None:
        """Test curve addition when memory limit is exceeded."""
        # Create large data that exceeds memory limit
        large_data = [0.0] * 10000000  # 10M points should exceed 200MB limit
        
        with patch.object(chart_view, 'memory_warning') as mock_warning:
            result = chart_view.add_curve("large_curve", large_data, large_data)
            
            assert result is False
            mock_warning.emit.assert_called()

    def test_max_curves_limit(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test behavior when max curves limit is reached."""
        chart_view.max_curves = 2
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            
            # Add curves up to limit
            chart_view.add_curve("curve1", x_data, y_data)
            chart_view.add_curve("curve2", x_data, y_data)
            
            # Adding third curve should remove oldest
            with patch.object(chart_view, '_remove_oldest_curve') as mock_remove:
                chart_view.add_curve("curve3", x_data, y_data)
                mock_remove.assert_called_once()

    def test_remove_curve_success(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test successful curve removal."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            chart_view.add_curve("test_curve", x_data, y_data)
            
            # Now test removal
            mock_line.remove = Mock()
            result = chart_view.remove_curve("test_curve")
            
            assert result is True
            assert "test_curve" not in chart_view._curves
            assert "test_curve" not in chart_view._curve_data
            assert chart_view._curve_count == 0

    def test_remove_nonexistent_curve(self, chart_view: ChartView) -> None:
        """Test removing a curve that doesn't exist."""
        result = chart_view.remove_curve("nonexistent")
        
        assert result is False

    def test_clear_all_curves(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test clearing all curves."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            chart_view.add_curve("curve1", x_data, y_data)
            chart_view.add_curve("curve2", x_data, y_data)
            
            # Now test clearing
            mock_axes.clear = Mock()
            mock_axes.grid = Mock()
            chart_view.clear_all_curves()
            
            assert len(chart_view._curves) == 0
            assert len(chart_view._curve_data) == 0
            assert chart_view._curve_count == 0

    def test_remove_oldest_curve(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test removing the oldest curve."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            mock_line.remove = Mock()
            
            chart_view.add_curve("oldest", x_data, y_data)
            chart_view.add_curve("newer", x_data, y_data)
            
            chart_view._remove_oldest_curve()
            
            assert "oldest" not in chart_view._curves
            assert "newer" in chart_view._curves


class TestChartViewBackendManagement:
    """Test backend switching and management."""

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
    @patch('mdaviz.chartview.MATPLOTLIB_AVAILABLE', True)
    @patch('mdaviz.chartview.Figure')
    @patch('mdaviz.chartview.FigureCanvas')
    @patch('mdaviz.chartview.plt')
    def test_matplotlib_backend_setup(self, mock_plt: Mock, mock_canvas: Mock, mock_figure: Mock, qt_app: QApplication) -> None:
        """Test setting up matplotlib backend."""
        # Setup mocks
        mock_fig_instance = Mock()
        mock_figure.return_value = mock_fig_instance
        mock_fig_instance.add_subplot.return_value = Mock()
        
        chart = ChartView(backend="matplotlib")
        
        assert chart.backend == "matplotlib"
        assert hasattr(chart, 'figure')
        assert hasattr(chart, 'canvas')
        assert hasattr(chart, 'axes')

    @pytest.mark.skipif(not PYQTGRAPH_AVAILABLE, reason="PyQtGraph not available")
    @patch('mdaviz.chartview.PYQTGRAPH_AVAILABLE', True)
    @patch('mdaviz.chartview.pg')
    def test_pyqtgraph_backend_setup(self, mock_pg: Mock, qt_app: QApplication) -> None:
        """Test setting up pyqtgraph backend."""
        # Setup mock
        mock_plot_widget = Mock()
        mock_pg.PlotWidget.return_value = mock_plot_widget
        
        chart = ChartView(backend="pyqtgraph")
        
        assert chart.backend == "pyqtgraph"
        assert hasattr(chart, 'plot_widget')

    def test_switch_backend_same(self, chart_view: ChartView) -> None:
        """Test switching to the same backend."""
        current_backend = chart_view.backend
        result = chart_view.switch_backend(current_backend)
        
        assert result is True
        assert chart_view.backend == current_backend

    @pytest.mark.skipif(not (MATPLOTLIB_AVAILABLE and PYQTGRAPH_AVAILABLE), 
                       reason="Both backends needed for switching test")
    def test_switch_backend_different(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test switching to a different backend."""
        x_data, y_data = sample_data
        original_backend = chart_view.backend
        target_backend = "pyqtgraph" if original_backend == "matplotlib" else "matplotlib"
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            
            # Add curve before switching
            chart_view.add_curve("test_curve", x_data, y_data)
            
            # Mock the backend switch
            with patch.object(chart_view, 'backend_switched') as mock_signal, \
                 patch.object(chart_view, '_setup_backend'):
                result = chart_view.switch_backend(target_backend)
                
                assert result is True
                # Curve should be restored in curve_data
                assert "test_curve" in chart_view._curve_data


class TestChartViewPerformance:
    """Test performance monitoring and optimization features."""

    def test_get_performance_info(self, chart_view: ChartView) -> None:
        """Test getting performance information."""
        info = chart_view.get_performance_info()
        
        assert isinstance(info, dict)
        assert "curve_count" in info
        assert "memory_usage_mb" in info
        assert "backend" in info
        assert "memory_limit_mb" in info
        assert "max_curves" in info
        assert "lazy_rendering" in info
        
        assert info["curve_count"] == chart_view._curve_count
        assert info["backend"] == chart_view.backend

    def test_lazy_rendering_schedule(self, chart_view: ChartView) -> None:
        """Test lazy rendering scheduling."""
        chart_view.enable_lazy_rendering = True
        
        chart_view._schedule_render("test_curve")
        
        assert "test_curve" in chart_view._pending_renders
        assert chart_view._render_timer.isActive()

    def test_delayed_render(self, chart_view: ChartView) -> None:
        """Test delayed rendering execution."""
        chart_view._pending_renders = ["curve1", "curve2"]
        
        with patch.object(chart_view, 'canvas') as mock_canvas:
            mock_canvas.draw = Mock()
            chart_view._delayed_render()
            
            assert len(chart_view._pending_renders) == 0

    @patch('mdaviz.chartview.psutil')
    def test_update_performance_stats_with_psutil(self, mock_psutil: Mock, chart_view: ChartView) -> None:
        """Test performance stats update with psutil available."""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_psutil.Process.return_value = mock_process
        
        # Force update by setting last check time to 0
        chart_view._last_performance_check = 0.0
        
        with patch.object(chart_view, 'performance_stats') as mock_signal:
            chart_view._update_performance_stats()
            
            assert chart_view._memory_usage_mb == 100.0
            mock_signal.emit.assert_called()

    @patch('mdaviz.chartview.psutil', side_effect=ImportError)
    def test_update_performance_stats_no_psutil(self, mock_psutil: Mock, chart_view: ChartView) -> None:
        """Test performance stats update without psutil."""
        chart_view._last_performance_check = 0.0
        
        chart_view._update_performance_stats()
        
        assert chart_view._memory_usage_mb == 0.0


class TestChartViewSignals:
    """Test signal emission from ChartView."""

    def test_curve_added_signal(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test curve_added signal emission."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes, \
             patch.object(chart_view, 'curve_added') as mock_signal:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            
            chart_view.add_curve("test_curve", x_data, y_data)
            mock_signal.emit.assert_called_with("test_curve")

    def test_curve_removed_signal(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test curve_removed signal emission."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes, \
             patch.object(chart_view, 'curve_removed') as mock_signal:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            mock_line.remove = Mock()
            
            chart_view.add_curve("test_curve", x_data, y_data)
            chart_view.remove_curve("test_curve")
            mock_signal.emit.assert_called_with("test_curve")


class TestChartViewCleanup:
    """Test cleanup and resource management."""

    def test_cleanup_method(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test cleanup method."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            chart_view.add_curve("test_curve", x_data, y_data)
            
            chart_view.cleanup()
            
            assert len(chart_view._curves) == 0
            assert len(chart_view._curve_data) == 0
            assert not chart_view._render_timer.isActive()

    def test_close_event(self, chart_view: ChartView) -> None:
        """Test close event handling."""
        mock_event = Mock()
        
        with patch.object(chart_view, 'cleanup') as mock_cleanup:
            chart_view.closeEvent(mock_event)
            mock_cleanup.assert_called_once()


class TestChartViewErrorHandling:
    """Test error handling in ChartView."""

    def test_add_curve_error_handling(self, chart_view: ChartView) -> None:
        """Test error handling during curve addition."""
        # Test with invalid data that might cause errors
        with patch.object(chart_view, '_curves', side_effect=Exception("Test error")):
            result = chart_view.add_curve("error_curve", [1, 2], [3, 4])
            assert result is False

    def test_remove_curve_error_handling(self, chart_view: ChartView, sample_data: tuple) -> None:
        """Test error handling during curve removal."""
        x_data, y_data = sample_data
        
        with patch.object(chart_view, 'axes') as mock_axes:
            mock_line = Mock()
            mock_axes.plot.return_value = [mock_line]
            mock_axes.legend = Mock()
            chart_view.add_curve("test_curve", x_data, y_data)
            
            # Mock an error during removal
            with patch.object(chart_view._curves, '__delitem__', side_effect=Exception("Test error")):
                result = chart_view.remove_curve("test_curve")
                assert result is False

    def test_clear_curves_error_handling(self, chart_view: ChartView) -> None:
        """Test error handling during curve clearing."""
        with patch.object(chart_view, '_curves', side_effect=Exception("Test error")):
            # Should not raise exception
            chart_view.clear_all_curves()

    def test_switch_backend_error_handling(self, chart_view: ChartView) -> None:
        """Test error handling during backend switching."""
        with patch.object(chart_view, '_setup_backend', side_effect=Exception("Test error")):
            result = chart_view.switch_backend("matplotlib")
            assert result is False

    def test_cleanup_error_handling(self, chart_view: ChartView) -> None:
        """Test error handling during cleanup."""
        with patch.object(chart_view, 'clear_all_curves', side_effect=Exception("Test error")):
            # Should not raise exception
            chart_view.cleanup()
