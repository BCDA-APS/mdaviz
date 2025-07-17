"""
Enhanced fit manager for handling curve fitting operations with performance optimizations.

This module provides advanced fit management with asynchronous fitting capabilities,
performance monitoring, comprehensive error handling, and user-friendly feedback.

.. autosummary::

    ~FitData
    ~FitManager
    ~FitError
    ~FitWarning
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, Dict, List, Any, Callable, Union
import numpy as np
from dataclasses import dataclass, field

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from mdaviz.fit_models import FitModel, FitResult, get_available_models


class FitError(ValueError):
    """Custom exception for fit-related errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """
        Initialize fit error.

        Parameters:
            message (str): Main error message
            details (Optional[str]): Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        """Get string representation of the error."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class FitWarning(Warning):
    """Custom warning for fit-related issues."""

    pass


@dataclass
class FitData:
    """
    Enhanced container for fit data associated with a curve.

    This class stores comprehensive fit information including performance
    metrics and metadata for improved fit management.
    """

    model_name: str
    fit_result: FitResult
    x_range: Optional[Tuple[float, float]] = None
    visible: bool = True
    fit_time: float = field(default=0.0)
    creation_time: float = field(default_factory=time.time)
    data_points: int = field(default=0)
    convergence_status: str = field(default="unknown")
    user_notes: str = field(default="")

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if hasattr(self.fit_result, "x_fit"):
            self.data_points = len(self.fit_result.x_fit)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the fit data.

        Returns:
            Dict[str, Any]: Summary information
        """
        return {
            "model": self.model_name,
            "r_squared": self.fit_result.r_squared,
            "chi_squared": self.fit_result.chi_squared,
            "data_points": self.data_points,
            "fit_time": self.fit_time,
            "convergence": self.convergence_status,
            "visible": self.visible,
        }

    def is_good_fit(self, r_squared_threshold: float = 0.8) -> bool:
        """
        Assess if this is a good fit based on R-squared value.

        Parameters:
            r_squared_threshold (float): Minimum R-squared for good fit

        Returns:
            bool: True if considered a good fit
        """
        return (
            hasattr(self.fit_result, "r_squared")
            and self.fit_result.r_squared >= r_squared_threshold
        )


class FitManager(QObject):
    """
    Enhanced fit manager with performance optimizations and async capabilities.

    This manager provides advanced fit operations including asynchronous fitting,
    performance monitoring, comprehensive error handling, and fit quality assessment.
    """

    # Enhanced signals with more information
    fitAdded = pyqtSignal(str, dict)  # curveID, fit_summary
    fitUpdated = pyqtSignal(str, dict)  # curveID, fit_summary
    fitRemoved = pyqtSignal(str)  # curveID
    fitVisibilityChanged = pyqtSignal(str, bool)  # curveID, visible
    fitError = pyqtSignal(str, str, str)  # curveID, error_message, details
    fitWarning = pyqtSignal(str, str)  # curveID, warning_message
    fitProgress = pyqtSignal(str, int, int)  # curveID, current, total
    performanceUpdate = pyqtSignal(dict)  # performance_stats

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize enhanced fit manager.

        Parameters:
            parent (Optional[QObject]): Parent object
        """
        super().__init__(parent)

        # Fit storage with weak references to prevent memory leaks
        self._fits: Dict[str, FitData] = {}
        self._fit_history: Dict[str, List[FitData]] = {}

        # Performance tracking
        self._performance_stats: Dict[str, Any] = {
            "total_fits": 0,
            "successful_fits": 0,
            "failed_fits": 0,
            "average_fit_time": 0.0,
            "total_fit_time": 0.0,
            "fits_per_model": {},
        }

        # Async fitting support
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="FitManager"
        )
        self._active_fits: Dict[str, asyncio.Future] = {}

        # Configuration
        self.max_fit_history = 10  # Keep last 10 fits per curve
        self.max_concurrent_fits = 2
        self.default_r_squared_threshold = 0.8
        self.enable_auto_quality_check = True

        # Performance monitoring timer
        self._perf_timer = QTimer()
        self._perf_timer.timeout.connect(self._emit_performance_stats)
        self._perf_timer.start(30000)  # Update every 30 seconds

    def get_available_models(self) -> dict[str, FitModel]:
        """
        Get available fit models.

        Returns:
        - Dictionary mapping model names to FitModel instances
        """
        return get_available_models()

    def addFit(
        self,
        curveID: str,
        model_name: str,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_range: Optional[Tuple[float, float]] = None,
        initial_params: Optional[Dict[str, float]] = None,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        async_fit: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Union[bool, asyncio.Future]:
        """
        Add a fit to a curve with enhanced error handling and optional async execution.

        Parameters:
            curveID (str): Unique identifier for the curve
            model_name (str): Name of the fit model to use
            x_data (np.ndarray): X data points
            y_data (np.ndarray): Y data points
            x_range (Optional[Tuple[float, float]]): Range for fitting
            initial_params (Optional[Dict[str, float]]): Initial parameter guesses
            bounds (Optional[Dict[str, Tuple[float, float]]]): Parameter bounds
            async_fit (bool): Whether to perform fitting asynchronously
            progress_callback (Optional[Callable]): Progress callback function

        Returns:
            Union[bool, asyncio.Future]: Success status or Future for async fits

        Raises:
            FitError: If fitting parameters are invalid or fit fails
        """
        try:
            # Validate inputs
            self._validate_fit_inputs(curveID, model_name, x_data, y_data, x_range)

            # Check concurrent fit limit
            if len(self._active_fits) >= self.max_concurrent_fits:
                raise FitError(
                    f"Maximum concurrent fits ({self.max_concurrent_fits}) reached",
                    "Wait for existing fits to complete or increase the limit",
                )

            if async_fit:
                return self._add_fit_async(
                    curveID,
                    model_name,
                    x_data,
                    y_data,
                    x_range,
                    initial_params,
                    bounds,
                    progress_callback,
                )
            else:
                return self._add_fit_sync(
                    curveID,
                    model_name,
                    x_data,
                    y_data,
                    x_range,
                    initial_params,
                    bounds,
                    progress_callback,
                )

        except Exception as e:
            error_msg = f"Failed to add fit for curve {curveID}"
            details = str(e)
            self.fitError.emit(curveID, error_msg, details)
            self._update_performance_stats(success=False)
            raise FitError(error_msg, details)

    def _validate_fit_inputs(
        self,
        curveID: str,
        model_name: str,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_range: Optional[Tuple[float, float]],
    ) -> None:
        """
        Validate fit inputs and raise appropriate errors.

        Parameters:
            curveID (str): Curve identifier
            model_name (str): Model name
            x_data (np.ndarray): X data
            y_data (np.ndarray): Y data
            x_range (Optional[Tuple[float, float]]): Fit range

        Raises:
            FitError: If inputs are invalid
        """
        # Check if model exists
        available_models = get_available_models()
        if model_name not in available_models:
            raise FitError(
                f"Unknown fit model: {model_name}",
                f"Available models: {', '.join(available_models.keys())}",
            )

        # Validate data arrays
        if not isinstance(x_data, np.ndarray) or not isinstance(y_data, np.ndarray):
            raise FitError("Data must be numpy arrays")

        if len(x_data) != len(y_data):
            raise FitError(
                "X and Y data must have the same length",
                f"X: {len(x_data)}, Y: {len(y_data)}",
            )

        if len(x_data) < 3:
            raise FitError(
                "Insufficient data points for fitting",
                f"Need at least 3 points, got {len(x_data)}",
            )

        # Check for NaN or infinite values
        if np.any(~np.isfinite(x_data)) or np.any(~np.isfinite(y_data)):
            raise FitError("Data contains NaN or infinite values")

        # Validate range if specified
        if x_range is not None:
            if len(x_range) != 2:
                raise FitError("Range must be a tuple of (min, max)")

            if x_range[0] >= x_range[1]:
                raise FitError("Range minimum must be less than maximum")

            # Check if range contains any data points
            mask = (x_data >= x_range[0]) & (x_data <= x_range[1])
            if not np.any(mask):
                raise FitError(
                    f"No data points in specified range [{x_range[0]}, {x_range[1]}]"
                )

    def _add_fit_sync(
        self,
        curveID: str,
        model_name: str,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_range: Optional[Tuple[float, float]],
        initial_params: Optional[Dict[str, float]],
        bounds: Optional[Dict[str, Tuple[float, float]]],
        progress_callback: Optional[Callable[[int, int], None]],
    ) -> bool:
        """Perform synchronous fitting."""
        start_time = time.time()

        try:
            # Get the model
            available_models = get_available_models()
            model = available_models[model_name]

            # Process data for fitting
            x_fit, y_fit = self._prepare_fit_data(x_data, y_data, x_range)

            # Emit progress
            if progress_callback:
                progress_callback(0, 100)
            self.fitProgress.emit(curveID, 0, 100)

            # Perform the fit
            try:
                fit_result = model.fit(x_fit, y_fit, initial_params, bounds)
                convergence_status = "converged"
            except Exception as e:
                raise FitError(f"Fit algorithm failed: {str(e)}")

            # Emit progress
            if progress_callback:
                progress_callback(100, 100)
            self.fitProgress.emit(curveID, 100, 100)

            # Calculate fit time
            fit_time = time.time() - start_time

            # Create fit data
            fit_data = FitData(
                model_name=model_name,
                fit_result=fit_result,
                x_range=x_range,
                visible=True,
                fit_time=fit_time,
                data_points=len(x_fit),
                convergence_status=convergence_status,
            )

            # Store fit data
            had_existing_fit = curveID in self._fits
            self._fits[curveID] = fit_data

            # Update fit history
            if curveID not in self._fit_history:
                self._fit_history[curveID] = []
            self._fit_history[curveID].append(fit_data)

            # Trim history if needed
            if len(self._fit_history[curveID]) > self.max_fit_history:
                self._fit_history[curveID] = self._fit_history[curveID][
                    -self.max_fit_history :
                ]

            # Update performance stats
            self._update_performance_stats(
                success=True, fit_time=fit_time, model_name=model_name
            )

            # Perform quality check if enabled
            if self.enable_auto_quality_check:
                self._check_fit_quality(curveID, fit_data)

            # Emit appropriate signal
            fit_summary = fit_data.get_summary()
            if had_existing_fit:
                self.fitUpdated.emit(curveID, fit_summary)
            else:
                self.fitAdded.emit(curveID, fit_summary)

            return True

        except Exception:
            self._update_performance_stats(success=False)
            raise

    def _add_fit_async(
        self,
        curveID: str,
        model_name: str,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_range: Optional[Tuple[float, float]],
        initial_params: Optional[Dict[str, float]],
        bounds: Optional[Dict[str, Tuple[float, float]]],
        progress_callback: Optional[Callable[[int, int], None]],
    ) -> asyncio.Future:
        """Perform asynchronous fitting."""

        def fit_worker():
            """Worker function for async fitting."""
            return self._add_fit_sync(
                curveID,
                model_name,
                x_data,
                y_data,
                x_range,
                initial_params,
                bounds,
                progress_callback,
            )

        def on_complete(future):
            """Callback for async completion."""
            try:
                # Remove from active fits
                if curveID in self._active_fits:
                    del self._active_fits[curveID]

                # Check for exceptions
                future.result()

            except Exception as e:
                error_msg = f"Async fit failed for curve {curveID}"
                details = str(e)
                self.fitError.emit(curveID, error_msg, details)

        # Submit async task
        future = self._executor.submit(fit_worker)
        future.add_done_callback(on_complete)

        # Track active fit
        self._active_fits[curveID] = future

        return future

    def _prepare_fit_data(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_range: Optional[Tuple[float, float]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for fitting by applying range and cleaning.

        Parameters:
            x_data (np.ndarray): X data
            y_data (np.ndarray): Y data
            x_range (Optional[Tuple[float, float]]): Fit range

        Returns:
            Tuple[np.ndarray, np.ndarray]: Prepared x and y data
        """
        # Ensure arrays are contiguous and float64
        x_fit = np.ascontiguousarray(x_data, dtype=np.float64)
        y_fit = np.ascontiguousarray(y_data, dtype=np.float64)

        # Apply range if specified
        if x_range is not None:
            mask = (x_fit >= x_range[0]) & (x_fit <= x_range[1])
            x_fit = x_fit[mask]
            y_fit = y_fit[mask]

        # Remove any remaining NaN or infinite values
        finite_mask = np.isfinite(x_fit) & np.isfinite(y_fit)
        x_fit = x_fit[finite_mask]
        y_fit = y_fit[finite_mask]

        return x_fit, y_fit

    def _check_fit_quality(self, curveID: str, fit_data: FitData) -> None:
        """
        Check fit quality and emit warnings if needed.

        Parameters:
            curveID (str): Curve identifier
            fit_data (FitData): Fit data to check
        """
        try:
            # Check R-squared
            if hasattr(fit_data.fit_result, "r_squared"):
                r_squared = fit_data.fit_result.r_squared
                if r_squared < 0.5:
                    self.fitWarning.emit(
                        curveID,
                        f"Poor fit quality (R² = {r_squared:.3f}). Consider different model or parameters.",
                    )
                elif r_squared < self.default_r_squared_threshold:
                    self.fitWarning.emit(
                        curveID,
                        f"Moderate fit quality (R² = {r_squared:.3f}). Results may be unreliable.",
                    )

            # Check parameter uncertainties
            if hasattr(fit_data.fit_result, "uncertainties"):
                uncertainties = fit_data.fit_result.uncertainties
                parameters = fit_data.fit_result.parameters

                for param, uncertainty in uncertainties.items():
                    if param in parameters:
                        relative_error = (
                            abs(uncertainty / parameters[param])
                            if parameters[param] != 0
                            else float("inf")
                        )
                        if relative_error > 0.5:  # 50% relative error
                            self.fitWarning.emit(
                                curveID,
                                f"Large uncertainty in parameter '{param}' ({relative_error * 100:.1f}%)",
                            )

        except Exception as e:
            print(f"Error in fit quality check: {e}")

    def _update_performance_stats(
        self,
        success: bool,
        fit_time: Optional[float] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """
        Update performance statistics.

        Parameters:
            success (bool): Whether the fit was successful
            fit_time (Optional[float]): Time taken for the fit
            model_name (Optional[str]): Name of the model used
        """
        self._performance_stats["total_fits"] += 1

        if success:
            self._performance_stats["successful_fits"] += 1

            if fit_time is not None:
                self._performance_stats["total_fit_time"] += fit_time
                successful_fits = self._performance_stats["successful_fits"]
                self._performance_stats["average_fit_time"] = (
                    self._performance_stats["total_fit_time"] / successful_fits
                )

            if model_name is not None:
                if model_name not in self._performance_stats["fits_per_model"]:
                    self._performance_stats["fits_per_model"][model_name] = 0
                self._performance_stats["fits_per_model"][model_name] += 1
        else:
            self._performance_stats["failed_fits"] += 1

    def _emit_performance_stats(self) -> None:
        """Emit current performance statistics."""
        stats = self._performance_stats.copy()
        stats["active_fits"] = len(self._active_fits)
        stats["cached_fits"] = len(self._fits)
        self.performanceUpdate.emit(stats)

    def removeFit(self, curveID: str) -> bool:
        """
        Remove a fit from a curve.

        Parameters:
            curveID (str): Curve identifier

        Returns:
            bool: True if fit was removed, False if not found
        """
        try:
            if curveID in self._fits:
                # Cancel active fit if running
                if curveID in self._active_fits:
                    try:
                        self._active_fits[curveID].cancel()
                        del self._active_fits[curveID]
                    except Exception:
                        pass  # Future may already be completed

                del self._fits[curveID]
                self.fitRemoved.emit(curveID)
                return True
            return False

        except Exception as e:
            print(f"Error removing fit for {curveID}: {e}")
            return False

    def removeAllFits(self, curveID: str) -> None:
        """
        Remove the fit from a curve (alias for removeFit).

        Parameters:
        - curveID: ID of the curve
        """
        self.removeFit(curveID)

    def getFit(self, curveID: str) -> Optional[FitData]:
        """
        Get fit data for a curve.

        Parameters:
            curveID (str): Curve identifier

        Returns:
            Optional[FitData]: Fit data or None if not found
        """
        return self._fits.get(curveID)

    def getFitData(self, curveID: str) -> Optional[FitData]:
        """
        Get fit data for a curve (backward compatibility alias).

        Parameters:
            curveID (str): Curve identifier

        Returns:
            Optional[FitData]: Fit data or None if not found
        """
        return self.getFit(curveID)

    def getFitHistory(self, curveID: str) -> List[FitData]:
        """
        Get fit history for a curve.

        Parameters:
            curveID (str): Curve identifier

        Returns:
            List[FitData]: List of historical fit data
        """
        return self._fit_history.get(curveID, [])

    def getFitSummary(self, curveID: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the current fit for a curve.

        Parameters:
            curveID (str): Curve identifier

        Returns:
            Optional[Dict[str, Any]]: Fit summary or None if not found
        """
        fit_data = self.getFit(curveID)
        return fit_data.get_summary() if fit_data else None

    def setFitVisibility(self, curveID: str, visible: bool) -> bool:
        """
        Set fit curve visibility.

        Parameters:
            curveID (str): Curve identifier
            visible (bool): Whether fit should be visible

        Returns:
            bool: True if successful, False if curve not found
        """
        try:
            if curveID in self._fits:
                self._fits[curveID].visible = visible
                self.fitVisibilityChanged.emit(curveID, visible)
                return True
            return False

        except Exception as e:
            print(f"Error setting fit visibility for {curveID}: {e}")
            return False

    def isFitVisible(self, curveID: str) -> bool:
        """
        Check if a fit is visible.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - True if fit is visible, False otherwise
        """
        fit_data = self.getFit(curveID)
        return fit_data.visible if fit_data else False

    def getFitCurveData(self, curveID: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get the fitted curve data for plotting.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Tuple of (x_fit, y_fit) arrays if found, None otherwise
        """
        fit_data = self.getFit(curveID)
        if fit_data:
            return fit_data.fit_result.x_fit, fit_data.fit_result.fit_curve
        return None

    def getFitParameters(self, curveID: str) -> Optional[Dict[str, float]]:
        """
        Get fit parameters for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Dictionary of parameter names and values if found, None otherwise
        """
        fit_data = self.getFit(curveID)
        return fit_data.fit_result.parameters if fit_data else None

    def getFitUncertainties(self, curveID: str) -> Optional[Dict[str, float]]:
        """
        Get fit parameter uncertainties for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Dictionary of parameter names and uncertainties if found, None otherwise
        """
        fit_data = self.getFit(curveID)
        return fit_data.fit_result.uncertainties if fit_data else None

    def getFitQualityMetrics(self, curveID: str) -> Optional[Dict[str, float]]:
        """
        Get fit quality metrics for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Dictionary of quality metrics if found, None otherwise
        """
        fit_data = self.getFit(curveID)
        if fit_data:
            return {
                "r_squared": fit_data.fit_result.r_squared,
                "chi_squared": fit_data.fit_result.chi_squared,
                "reduced_chi_squared": fit_data.fit_result.reduced_chi_squared,
            }
        return None

    def hasFit(self, curveID: str) -> bool:
        """
        Check if a curve has a fit.

        Parameters:
            curveID (str): Curve identifier

        Returns:
            bool: True if curve has a fit
        """
        return curveID in self._fits

    def hasFits(self, curveID: str) -> bool:
        """
        Check if a curve has a fit (backward compatibility alias).

        Parameters:
            curveID (str): Curve identifier

        Returns:
            bool: True if curve has a fit
        """
        return self.hasFit(curveID)

    def getFitCount(self, curveID: str) -> int:
        """
        Get the number of fits for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Number of fits for the curve (0 or 1)
        """
        return 1 if curveID in self._fits else 0

    def clearAllFits(self) -> None:
        """Clear all fits and reset statistics."""
        try:
            # Cancel all active fits
            for future in self._active_fits.values():
                try:
                    future.cancel()
                except Exception:
                    pass

            # Clear data structures
            self._fits.clear()
            self._fit_history.clear()
            self._active_fits.clear()

            # Reset performance stats
            self._performance_stats = {
                "total_fits": 0,
                "successful_fits": 0,
                "failed_fits": 0,
                "average_fit_time": 0.0,
                "total_fit_time": 0.0,
                "fits_per_model": {},
            }

        except Exception as e:
            print(f"Error clearing fits: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._perf_timer.stop()
            self.clearAllFits()

            if self._executor:
                self._executor.shutdown(wait=False)

        except Exception as e:
            print(f"Error during fit manager cleanup: {e}")

    def closeEvent(self, event) -> None:
        """Handle close event with proper cleanup."""
        self.cleanup()
        super().closeEvent(event)
