"""
Fit manager for handling curve fitting operations.

This module manages fit operations for curves, handles fit parameter storage
and retrieval, and coordinates between UI and fit calculations.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from PyQt5 import QtCore
from .fit_models import FitModel, FitResult, get_available_models


class FitData:
    """Container for fit data associated with a curve."""
    
    def __init__(self, 
                 fit_id: str,
                 model_name: str,
                 fit_result: FitResult,
                 x_range: Optional[Tuple[float, float]] = None,
                 visible: bool = True):
        """
        Initialize fit data.
        
        Parameters:
        - fit_id: Unique identifier for this fit
        - model_name: Name of the fit model used
        - fit_result: FitResult object containing fit parameters and metrics
        - x_range: Optional range of x values used for fitting
        - visible: Whether the fit curve should be visible
        """
        self.fit_id = fit_id
        self.model_name = model_name
        self.fit_result = fit_result
        self.x_range = x_range
        self.visible = visible


class FitManager(QtCore.QObject):
    """Manages fit operations for curves."""
    
    fitAdded = QtCore.pyqtSignal(str, str)  # curveID, fitID
    fitUpdated = QtCore.pyqtSignal(str, str)  # curveID, fitID  
    fitRemoved = QtCore.pyqtSignal(str, str)  # curveID, fitID
    fitVisibilityChanged = QtCore.pyqtSignal(str, str, bool)  # curveID, fitID, visible
    
    def __init__(self, parent=None):
        """
        Initialize fit manager.
        
        Parameters:
        - parent: Parent QObject
        """
        super().__init__(parent)
        self._fits: Dict[str, Dict[str, FitData]] = {}  # {curveID: {fitID: FitData}}
        self._models = get_available_models()
        self._fit_counter = 0
    
    def get_available_models(self) -> Dict[str, FitModel]:
        """
        Get available fit models.
        
        Returns:
        - Dictionary mapping model names to FitModel instances
        """
        return self._models
    
    def addFit(self, curveID: str, model_name: str, x_data: np.ndarray, y_data: np.ndarray,
               x_range: Optional[Tuple[float, float]] = None,
               initial_params: Optional[Dict[str, float]] = None,
               bounds: Optional[Dict[str, Tuple[float, float]]] = None) -> str:
        """
        Add a new fit to a curve.
        
        Parameters:
        - curveID: ID of the curve to fit
        - model_name: Name of the fit model to use
        - x_data: X values for fitting
        - y_data: Y values for fitting
        - x_range: Optional range of x values to use for fitting
        - initial_params: Optional initial parameter guesses
        - bounds: Optional parameter bounds
        
        Returns:
        - fitID: Unique identifier for the new fit
        
        Raises:
        - ValueError: If model_name is not available or fit fails
        """
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not available")
        
        model = self._models[model_name]
        
        # Apply x_range if specified
        if x_range is not None:
            mask = (x_data >= x_range[0]) & (x_data <= x_range[1])
            x_fit = x_data[mask]
            y_fit = y_data[mask]
        else:
            x_fit = x_data
            y_fit = y_data
        
        # Perform the fit
        try:
            fit_result = model.fit(x_fit, y_fit, initial_params, bounds)
        except Exception as e:
            raise ValueError(f"Fit failed: {str(e)}")
        
        # Generate unique fit ID
        self._fit_counter += 1
        fit_id = f"{model_name}_{self._fit_counter}"
        
        # Store fit data
        if curveID not in self._fits:
            self._fits[curveID] = {}
        
        fit_data = FitData(
            fit_id=fit_id,
            model_name=model_name,
            fit_result=fit_result,
            x_range=x_range,
            visible=True
        )
        
        self._fits[curveID][fit_id] = fit_data
        
        # Emit signal
        self.fitAdded.emit(curveID, fit_id)
        
        return fit_id
    
    def removeFit(self, curveID: str, fitID: str) -> None:
        """
        Remove a fit from a curve.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit to remove
        """
        if curveID in self._fits and fitID in self._fits[curveID]:
            del self._fits[curveID][fitID]
            if not self._fits[curveID]:  # Remove empty curve entry
                del self._fits[curveID]
            self.fitRemoved.emit(curveID, fitID)
    
    def removeAllFits(self, curveID: str) -> None:
        """
        Remove all fits from a curve.
        
        Parameters:
        - curveID: ID of the curve
        """
        if curveID in self._fits:
            fit_ids = list(self._fits[curveID].keys())
            for fit_id in fit_ids:
                self.removeFit(curveID, fit_id)
    
    def getFitData(self, curveID: str, fitID: str) -> Optional[FitData]:
        """
        Get fit data for a specific fit.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        
        Returns:
        - FitData object if found, None otherwise
        """
        return self._fits.get(curveID, {}).get(fitID)
    
    def getCurveFits(self, curveID: str) -> Dict[str, FitData]:
        """
        Get all fits for a curve.
        
        Parameters:
        - curveID: ID of the curve
        
        Returns:
        - Dictionary mapping fit IDs to FitData objects
        """
        return self._fits.get(curveID, {}).copy()
    
    def getAllFits(self) -> Dict[str, Dict[str, FitData]]:
        """
        Get all fits for all curves.
        
        Returns:
        - Dictionary mapping curve IDs to their fits
        """
        return {curve_id: fits.copy() for curve_id, fits in self._fits.items()}
    
    def setFitVisibility(self, curveID: str, fitID: str, visible: bool) -> None:
        """
        Set visibility of a fit curve.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        - visible: Whether the fit curve should be visible
        """
        fit_data = self.getFitData(curveID, fitID)
        if fit_data and fit_data.visible != visible:
            fit_data.visible = visible
            self.fitVisibilityChanged.emit(curveID, fitID, visible)
    
    def isFitVisible(self, curveID: str, fitID: str) -> bool:
        """
        Check if a fit is visible.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        
        Returns:
        - True if fit is visible, False otherwise
        """
        fit_data = self.getFitData(curveID, fitID)
        return fit_data.visible if fit_data else False
    
    def getFitCurveData(self, curveID: str, fitID: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get the fitted curve data for plotting.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        
        Returns:
        - Tuple of (x_fit, y_fit) arrays if found, None otherwise
        """
        fit_data = self.getFitData(curveID, fitID)
        if fit_data:
            return fit_data.fit_result.x_fit, fit_data.fit_result.fit_curve
        return None
    
    def getFitParameters(self, curveID: str, fitID: str) -> Optional[Dict[str, float]]:
        """
        Get fit parameters for a specific fit.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        
        Returns:
        - Dictionary of parameter names and values if found, None otherwise
        """
        fit_data = self.getFitData(curveID, fitID)
        return fit_data.fit_result.parameters if fit_data else None
    
    def getFitUncertainties(self, curveID: str, fitID: str) -> Optional[Dict[str, float]]:
        """
        Get fit parameter uncertainties for a specific fit.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        
        Returns:
        - Dictionary of parameter names and uncertainties if found, None otherwise
        """
        fit_data = self.getFitData(curveID, fitID)
        return fit_data.fit_result.uncertainties if fit_data else None
    
    def getFitQualityMetrics(self, curveID: str, fitID: str) -> Optional[Dict[str, float]]:
        """
        Get fit quality metrics for a specific fit.
        
        Parameters:
        - curveID: ID of the curve
        - fitID: ID of the fit
        
        Returns:
        - Dictionary of quality metrics if found, None otherwise
        """
        fit_data = self.getFitData(curveID, fitID)
        if fit_data:
            return {
                "r_squared": fit_data.fit_result.r_squared,
                "chi_squared": fit_data.fit_result.chi_squared,
                "reduced_chi_squared": fit_data.fit_result.reduced_chi_squared
            }
        return None
    
    def hasFits(self, curveID: str) -> bool:
        """
        Check if a curve has any fits.
        
        Parameters:
        - curveID: ID of the curve
        
        Returns:
        - True if curve has fits, False otherwise
        """
        return curveID in self._fits and len(self._fits[curveID]) > 0
    
    def getFitCount(self, curveID: str) -> int:
        """
        Get the number of fits for a curve.
        
        Parameters:
        - curveID: ID of the curve
        
        Returns:
        - Number of fits for the curve
        """
        return len(self._fits.get(curveID, {}))
    
    def clearAllFits(self) -> None:
        """Remove all fits from all curves."""
        curve_ids = list(self._fits.keys())
        for curve_id in curve_ids:
            self.removeAllFits(curve_id) 