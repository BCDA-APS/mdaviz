"""
Advanced chart view with dual plotting backends.

This module provides an advanced chart view with support for both Matplotlib
and PyQt6 native plotting backends, optimized for performance and memory usage.

.. autosummary::

    ~ChartView
"""

import gc
import weakref
from typing import Any, Optional, List, Dict, Tuple
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

# Conditional imports for performance
try:
    import matplotlib

    matplotlib.use("qtagg")  # Set backend before importing pyplot (Qt6Agg -> qtagg)
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt6agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    FigureCanvas = None
    Figure = None

try:
    import pyqtgraph as pg

    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    pg = None


class ChartView(QWidget):
    """
    Advanced chart view with dual plotting backends and performance optimizations.

    This widget provides high-performance data visualization with support for both
    Matplotlib and PyQtGraph backends. It includes automatic memory management,
    curve optimization, and lazy rendering for large datasets.

    Attributes:
        backend (str): Current plotting backend ('matplotlib' or 'pyqtgraph')
        max_curves (int): Maximum number of curves to display simultaneously
        enable_lazy_rendering (bool): Whether to use lazy rendering for large datasets
        memory_limit_mb (float): Memory limit for plotting data in megabytes
    """

    # Signals
    curve_added = pyqtSignal(str)  # curve name
    curve_removed = pyqtSignal(str)  # curve name
    backend_switched = pyqtSignal(str)  # new backend name
    memory_warning = pyqtSignal(float)  # memory usage in MB
    performance_stats = pyqtSignal(dict)  # performance statistics

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        backend: str = "matplotlib",
        max_curves: int = 50,
        enable_lazy_rendering: bool = True,
        memory_limit_mb: float = 200.0,
    ) -> None:
        """
        Initialize the advanced chart view.

        Parameters:
            parent (Optional[QWidget]): Parent widget
            backend (str): Initial plotting backend ('matplotlib' or 'pyqtgraph')
            max_curves (int): Maximum number of curves to display
            enable_lazy_rendering (bool): Whether to enable lazy rendering
            memory_limit_mb (float): Memory limit for plotting data
        """
        super().__init__(parent)

        self.backend = backend
        self.max_curves = max_curves
        self.enable_lazy_rendering = enable_lazy_rendering
        self.memory_limit_mb = memory_limit_mb

        # Performance tracking
        self._curve_count = 0
        self._render_time_ms = 0.0
        self._memory_usage_mb = 0.0
        self._last_performance_check = 0.0

        # Curve management
        self._curves: Dict[str, Any] = {}
        self._curve_data: Dict[str, Tuple[List[float], List[float]]] = {}
        self._weak_references: List[weakref.ReferenceType] = []

        # Performance optimization
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._delayed_render)
        self._pending_renders: List[str] = []

        self._setup_ui()
        self._setup_backend()

    def _setup_ui(self) -> None:
        """Set up the user interface with proper layout and sizing."""
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def _setup_backend(self) -> None:
        """
        Set up the plotting backend with fallback options.

        This method initializes the selected backend and provides fallbacks
        if the preferred backend is not available.
        """
        if self.backend == "matplotlib" and MATPLOTLIB_AVAILABLE:
            self._setup_matplotlib_backend()
        elif self.backend == "pyqtgraph" and PYQTGRAPH_AVAILABLE:
            self._setup_pyqtgraph_backend()
        else:
            # Fallback logic
            if MATPLOTLIB_AVAILABLE:
                self.backend = "matplotlib"
                self._setup_matplotlib_backend()
            elif PYQTGRAPH_AVAILABLE:
                self.backend = "pyqtgraph"
                self._setup_pyqtgraph_backend()
            else:
                raise RuntimeError(
                    "No plotting backend available. Install matplotlib or pyqtgraph."
                )

    def _setup_matplotlib_backend(self) -> None:
        """Set up Matplotlib backend with memory optimizations."""
        self.figure = Figure(figsize=(8, 6), dpi=100, tight_layout=True)
        self.figure.patch.set_facecolor("white")

        # Optimize matplotlib for performance
        self.figure.set_constrained_layout(True)

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)

        # Enable interactive navigation
        try:
            from matplotlib.backends.backend_qt6agg import NavigationToolbar2QT

            self.toolbar = NavigationToolbar2QT(self.canvas, self)
            self.layout.addWidget(self.toolbar)
        except ImportError:
            pass  # Navigation toolbar optional

        self.layout.addWidget(self.canvas)

        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True, alpha=0.3)

        # Set up weak reference for cleanup
        self._weak_references.append(weakref.ref(self.canvas))

    def _setup_pyqtgraph_backend(self) -> None:
        """Set up PyQtGraph backend with performance optimizations."""
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Y Axis")
        self.plot_widget.setLabel("bottom", "X Axis")

        # Enable automatic range adjustment
        self.plot_widget.enableAutoRange()

        # Optimize for performance
        self.plot_widget.setDownsampling(mode="peak")
        self.plot_widget.setClipToView(True)

        self.layout.addWidget(self.plot_widget)

        # Set up weak reference for cleanup
        self._weak_references.append(weakref.ref(self.plot_widget))

    def add_curve(
        self, name: str, x_data: List[float], y_data: List[float], **kwargs
    ) -> bool:
        """
        Add a new curve to the plot with performance optimization.

        Parameters:
            name (str): Unique name for the curve
            x_data (List[float]): X-axis data points
            y_data (List[float]): Y-axis data points
            **kwargs: Additional plotting parameters (color, linestyle, etc.)

        Returns:
            bool: True if curve was added successfully, False otherwise
        """
        try:
            # Check memory limits
            estimated_size_mb = (
                (len(x_data) + len(y_data)) * 8 / (1024 * 1024)
            )  # 8 bytes per float
            if estimated_size_mb > self.memory_limit_mb * 0.5:  # 50% of limit per curve
                self.memory_warning.emit(estimated_size_mb)
                return False

            # Check curve limits
            if len(self._curves) >= self.max_curves:
                self._remove_oldest_curve()

            # Store curve data for potential re-rendering
            self._curve_data[name] = (x_data.copy(), y_data.copy())

            if self.backend == "matplotlib":
                (line,) = self.axes.plot(x_data, y_data, label=name, **kwargs)
                self._curves[name] = line
                self.axes.legend()

                if self.enable_lazy_rendering:
                    self._schedule_render(name)
                else:
                    self.canvas.draw()

            elif self.backend == "pyqtgraph":
                curve = self.plot_widget.plot(x_data, y_data, name=name, **kwargs)
                self._curves[name] = curve

            self._curve_count += 1
            self.curve_added.emit(name)
            self._update_performance_stats()

            return True

        except Exception as e:
            print(f"Error adding curve {name}: {e}")
            return False

    def remove_curve(self, name: str) -> bool:
        """
        Remove a curve from the plot.

        Parameters:
            name (str): Name of the curve to remove

        Returns:
            bool: True if curve was removed successfully, False otherwise
        """
        try:
            if name not in self._curves:
                return False

            if self.backend == "matplotlib":
                line = self._curves[name]
                line.remove()
                self.axes.legend()
                self.canvas.draw()
            elif self.backend == "pyqtgraph":
                curve = self._curves[name]
                self.plot_widget.removeItem(curve)

            # Clean up data
            del self._curves[name]
            if name in self._curve_data:
                del self._curve_data[name]

            self._curve_count -= 1
            self.curve_removed.emit(name)
            self._update_performance_stats()

            return True

        except Exception as e:
            print(f"Error removing curve {name}: {e}")
            return False

    def clear_all_curves(self) -> None:
        """Remove all curves and clean up memory."""
        try:
            if self.backend == "matplotlib":
                self.axes.clear()
                self.axes.grid(True, alpha=0.3)
                self.canvas.draw()
            elif self.backend == "pyqtgraph":
                self.plot_widget.clear()

            self._curves.clear()
            self._curve_data.clear()
            self._curve_count = 0

            # Force garbage collection
            gc.collect()

            self._update_performance_stats()

        except Exception as e:
            print(f"Error clearing curves: {e}")

    def _remove_oldest_curve(self) -> None:
        """Remove the oldest curve to make room for new ones."""
        if self._curves:
            oldest_name = next(iter(self._curves))
            self.remove_curve(oldest_name)

    def _schedule_render(self, curve_name: str) -> None:
        """Schedule a delayed render for performance optimization."""
        if curve_name not in self._pending_renders:
            self._pending_renders.append(curve_name)

        # Delay rendering to batch multiple updates
        self._render_timer.start(50)  # 50ms delay

    def _delayed_render(self) -> None:
        """Perform delayed rendering of pending curves."""
        if self.backend == "matplotlib":
            self.canvas.draw()

        self._pending_renders.clear()

    def _update_performance_stats(self) -> None:
        """Update and emit performance statistics."""
        import time

        current_time = time.time()

        if current_time - self._last_performance_check > 5.0:  # Update every 5 seconds
            try:
                import psutil

                process = psutil.Process()
                self._memory_usage_mb = process.memory_info().rss / 1024 / 1024
            except:
                self._memory_usage_mb = 0.0

            stats = {
                "curve_count": self._curve_count,
                "memory_usage_mb": self._memory_usage_mb,
                "backend": self.backend,
                "render_time_ms": self._render_time_ms,
            }

            self.performance_stats.emit(stats)
            self._last_performance_check = current_time

    def switch_backend(self, new_backend: str) -> bool:
        """
        Switch to a different plotting backend.

        Parameters:
            new_backend (str): New backend to use ('matplotlib' or 'pyqtgraph')

        Returns:
            bool: True if switch was successful, False otherwise
        """
        if new_backend == self.backend:
            return True

        try:
            # Save current curve data
            saved_curves = self._curve_data.copy()

            # Clear current backend
            self.clear_all_curves()

            # Remove current widgets
            for i in reversed(range(self.layout.count())):
                widget = self.layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Switch backend
            old_backend = self.backend
            self.backend = new_backend
            self._setup_backend()

            # Restore curves
            for name, (x_data, y_data) in saved_curves.items():
                self.add_curve(name, x_data, y_data)

            self.backend_switched.emit(new_backend)
            return True

        except Exception as e:
            print(f"Error switching backend from {old_backend} to {new_backend}: {e}")
            return False

    def get_performance_info(self) -> Dict[str, Any]:
        """
        Get current performance information.

        Returns:
            Dict[str, Any]: Performance statistics
        """
        return {
            "curve_count": self._curve_count,
            "memory_usage_mb": self._memory_usage_mb,
            "backend": self.backend,
            "memory_limit_mb": self.memory_limit_mb,
            "max_curves": self.max_curves,
            "lazy_rendering": self.enable_lazy_rendering,
        }

    def cleanup(self) -> None:
        """Clean up resources and memory."""
        try:
            self.clear_all_curves()

            # Clean up weak references
            for ref in self._weak_references:
                obj = ref()
                if obj is not None:
                    try:
                        obj.deleteLater()
                    except:
                        pass

            self._weak_references.clear()

            # Stop timers
            self._render_timer.stop()

            # Force garbage collection
            gc.collect()

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def closeEvent(self, event) -> None:
        """Handle widget close event with proper cleanup."""
        self.cleanup()
        super().closeEvent(event)
