"""
Adstock Transformation Models for Marketing Mix Modeling.
Simulates and fits advertising carryover effects and lagged memory.
"""

import numpy as np
import pandas as pd
from typing import Union, List


class AdstockTransformer:
    """
    Transforms raw spend or impression series into adstock-decayed representations.
    Supports:
    1. Geometric (Exponential) decay
    2. Delayed Weibull decay
    """

    @staticmethod
    def geometric_adstock(
        series: Union[np.ndarray, pd.Series, List[float]],
        decay_rate: float = 0.3
    ) -> np.ndarray:
        """
        Calculates geometric adstock:
        Adstock[t] = Spend[t] + decay_rate * Adstock[t-1]
        
        Args:
            series: Daily spend or impressions array.
            decay_rate: Retention rate in [0, 1). 0 means no carryover, 0.7 means strong carryover.
        """
        x = np.asarray(series, dtype=float)
        adstocked = np.zeros_like(x)
        running = 0.0
        for t in range(len(x)):
            running = x[t] + decay_rate * running
            adstocked[t] = running
        return adstocked

    @staticmethod
    def weibull_adstock(
        series: Union[np.ndarray, pd.Series],
        shape: float = 2.0,
        scale: float = 3.0,
        max_lag: int = 14
    ) -> np.ndarray:
        """
        Weibull PDF adstock transformation for delayed peak impact (e.g. brand campaigns).
        """
        x = np.asarray(series, dtype=float)
        t = np.arange(1, max_lag + 1)
        # Weibull PDF weights
        weights = (shape / scale) * ((t / scale) ** (shape - 1)) * np.exp(-((t / scale) ** shape))
        weights /= weights.sum()

        padded_x = np.pad(x, (max_lag - 1, 0), mode="constant")
        adstocked = np.convolve(padded_x, weights[::-1], mode="valid")
        return adstocked[:len(x)]

    @classmethod
    def transform_dataframe(
        cls,
        df: pd.DataFrame,
        decay_rates: dict,
        date_col: str = "date",
        spend_col: str = "spend",
        channel_col: str = "channel"
    ) -> pd.DataFrame:
        """Applies channel-specific geometric adstock transformations to a panel DataFrame."""
        df_out = df.copy().sort_values(by=date_col)
        adstock_series = []

        for channel, group in df_out.groupby(channel_col):
            decay = decay_rates.get(channel, 0.2)
            adstocked_spend = cls.geometric_adstock(group[spend_col].values, decay_rate=decay)
            group_copy = group.copy()
            group_copy["adstock_spend"] = adstocked_spend
            adstock_series.append(group_copy)

        return pd.concat(adstock_series).sort_values(by=date_col).reset_index(drop=True)

