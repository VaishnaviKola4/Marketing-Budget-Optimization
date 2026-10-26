"""
Diminishing Returns & Saturation Curve Modeling.
Fits non-linear response curves (Hill and Exponential functions) to quantify
diminishing returns and calculate Marginal ROAS (mROAS).
"""

from typing import Tuple, Dict, Optional, Union
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def hill_function(x: np.ndarray, vmax: float, k: float, s: float) -> np.ndarray:
    """
    Hill Saturation Function:
        R(x) = Vmax * (x^S) / (K^S + x^S)
    
    Args:
        x: Marketing spend
        vmax: Maximum theoretical saturation ceiling for revenue
        k: Half-saturation point (spend where R = vmax / 2)
        s: Slope / curvature parameter (s > 1 creates S-curve, s <= 1 creates concave curve)
    """
    x_safe = np.maximum(x, 1e-6)
    x_s = np.power(x_safe, s)
    k_s = np.power(k, s)
    return vmax * (x_s / (k_s + x_s))


def hill_derivative(x: float, vmax: float, k: float, s: float) -> float:
    """
    First derivative of Hill function dR/dx (Marginal Return on Ad Spend - mROAS).
        dR/dx = vmax * s * (k^s) * x^(s-1) / (k^s + x^s)^2
    """
    if x <= 0:
        return vmax / max(k, 1.0)
    x_s = x ** s
    k_s = k ** s
    numerator = vmax * s * k_s * (x ** (s - 1))
    denominator = (k_s + x_s) ** 2
    return float(numerator / max(denominator, 1e-9))


def exponential_saturation(x: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """
    Concave Exponential Saturation Function:
        R(x) = alpha * (1 - exp(-beta * x))
    """
    return alpha * (1.0 - np.exp(-beta * np.maximum(x, 0.0)))


def exponential_derivative(x: float, alpha: float, beta: float) -> float:
    """First derivative dR/dx = alpha * beta * exp(-beta * x)."""
    return float(alpha * beta * np.exp(-beta * max(x, 0.0)))


class SaturationCurveFitter:
    """
    Fits and manages channel-specific saturation curves.
    Enables prediction of revenue, average ROAS, and marginal ROAS at any spend level.
    """

    def __init__(self, curve_type: str = "hill"):
        self.curve_type = curve_type
        self.channel_models: Dict[str, Dict[str, float]] = {}

    def fit_channel(self, spend: np.ndarray, revenue: np.ndarray, channel_name: str) -> Dict[str, float]:
        """Fits response curve parameters for a single channel."""
        spend = np.asarray(spend, dtype=float)
        revenue = np.asarray(revenue, dtype=float)

        # Filter positive values
        mask = (spend > 0) & (revenue >= 0)
        x_clean = spend[mask]
        y_clean = revenue[mask]

        if len(x_clean) < 5:
            # Fallback linear approximation if data is scarce
            ratio = float(np.mean(revenue) / max(np.mean(spend), 1.0))
            params = {"vmax": float(np.max(spend) * ratio * 3.0), "k": float(np.mean(spend) * 2.0), "s": 1.1}
            self.channel_models[channel_name] = params
            return params

        vmax_init = float(np.max(y_clean) * 1.8)
        k_init = float(np.median(x_clean))
        s_init = 1.2

        if self.curve_type == "hill":
            p0 = [vmax_init, k_init, s_init]
            bounds = (
                [np.max(y_clean) * 0.5, np.min(x_clean) * 0.1, 0.5],
                [np.max(y_clean) * 10.0, np.max(x_clean) * 5.0, 3.0]
            )
            try:
                popt, _ = curve_fit(hill_function, x_clean, y_clean, p0=p0, bounds=bounds, maxfev=4000)
                params = {"vmax": float(popt[0]), "k": float(popt[1]), "s": float(popt[2])}
            except Exception:
                # Robust heuristic fallback
                params = {"vmax": vmax_init, "k": k_init, "s": 1.2}
        else:
            # Exponential fit
            beta_init = 1.0 / max(np.mean(x_clean), 1.0)
            p0 = [vmax_init, beta_init]
            bounds = ([np.max(y_clean) * 0.5, 1e-7], [np.max(y_clean) * 10.0, 1.0])
            try:
                popt, _ = curve_fit(exponential_saturation, x_clean, y_clean, p0=p0, bounds=bounds, maxfev=4000)
                params = {"alpha": float(popt[0]), "beta": float(popt[1])}
            except Exception:
                params = {"alpha": vmax_init, "beta": beta_init}

        self.channel_models[channel_name] = params
        return params

    def fit_from_dataframe(
        self,
        df: pd.DataFrame,
        spend_col: str = "spend",
        revenue_col: str = "revenue",
        channel_col: str = "channel"
    ) -> Dict[str, Dict[str, float]]:
        """Fits saturation curves across all channels in DataFrame."""
        for channel, group in df.groupby(channel_col):
            self.fit_channel(group[spend_col].values, group[revenue_col].values, str(channel))
        return self.channel_models

    def predict(self, channel: str, spend: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Predicts revenue given spend for a channel."""
        if channel not in self.channel_models:
            raise KeyError(f"Channel '{channel}' has not been fitted. Available: {list(self.channel_models.keys())}")

        params = self.channel_models[channel]
        spend_arr = np.asarray(spend, dtype=float)

        if self.curve_type == "hill":
            pred = hill_function(spend_arr, params["vmax"], params["k"], params["s"])
        else:
            pred = exponential_saturation(spend_arr, params["alpha"], params["beta"])

        if np.isscalar(spend):
            return float(pred)
        return pred

    def marginal_roas(self, channel: str, spend: float) -> float:
        """Calculates marginal ROAS (mROAS) at a specific spend level."""
        if channel not in self.channel_models:
            raise KeyError(f"Channel '{channel}' has not been fitted.")

        params = self.channel_models[channel]
        if self.curve_type == "hill":
            return hill_derivative(spend, params["vmax"], params["k"], params["s"])
        else:
            return exponential_derivative(spend, params["alpha"], params["beta"])

    def find_saturation_point(self, channel: str, target_mroas: float = 1.0, max_search_spend: float = 50000.0) -> float:
        """
        Binary search for the spend point where marginal ROAS drops below target_mroas.
        Spend beyond this point produces diminishing returns where incremental revenue < incremental spend.
        """
        low = 10.0
        high = max_search_spend
        for _ in range(35):
            mid = (low + high) / 2.0
            m_roas = self.marginal_roas(channel, mid)
            if m_roas > target_mroas:
                low = mid
            else:
                high = mid
        return round(float(mid), 2)

