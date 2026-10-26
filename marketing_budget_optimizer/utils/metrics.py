"""
Marketing Performance and Financial Metrics Utilities.
"""

from typing import Dict, Any, Union
import numpy as np
import pandas as pd


def compute_roas(revenue: Union[float, np.ndarray, pd.Series], spend: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray, pd.Series]:
    """Computes Return On Ad Spend: Revenue / Spend."""
    spend_safe = np.where(spend == 0, np.nan, spend)
    roas = np.divide(revenue, spend_safe)
    return np.nan_to_num(roas, nan=0.0)


def compute_cpa(spend: Union[float, np.ndarray, pd.Series], conversions: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray, pd.Series]:
    """Computes Cost Per Acquisition: Spend / Conversions."""
    conv_safe = np.where(conversions == 0, np.nan, conversions)
    cpa = np.divide(spend, conv_safe)
    return np.nan_to_num(cpa, nan=0.0)


def compute_cpc(spend: Union[float, np.ndarray, pd.Series], clicks: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray, pd.Series]:
    """Computes Cost Per Click: Spend / Clicks."""
    clicks_safe = np.where(clicks == 0, np.nan, clicks)
    cpc = np.divide(spend, clicks_safe)
    return np.nan_to_num(cpc, nan=0.0)


def compute_cpm(spend: Union[float, np.ndarray, pd.Series], impressions: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray, pd.Series]:
    """Computes Cost Per Mille (1,000 Impressions): (Spend / Impressions) * 1000."""
    imp_safe = np.where(impressions == 0, np.nan, impressions)
    cpm = np.divide(spend, imp_safe) * 1000.0
    return np.nan_to_num(cpm, nan=0.0)


def compute_ctr(clicks: Union[float, np.ndarray, pd.Series], impressions: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray, pd.Series]:
    """Computes Click-Through Rate: Clicks / Impressions."""
    imp_safe = np.where(impressions == 0, np.nan, impressions)
    ctr = np.divide(clicks, imp_safe)
    return np.nan_to_num(ctr, nan=0.0)


def compute_cvr(conversions: Union[float, np.ndarray, pd.Series], clicks: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray, pd.Series]:
    """Computes Conversion Rate: Conversions / Clicks."""
    clicks_safe = np.where(clicks == 0, np.nan, clicks)
    cvr = np.divide(conversions, clicks_safe)
    return np.nan_to_num(cvr, nan=0.0)


def compute_portfolio_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Computes high-level portfolio KPIs from a campaign DataFrame."""
    total_spend = float(df["spend"].sum())
    total_rev = float(df["revenue"].sum())
    total_clicks = int(df["clicks"].sum())
    total_imps = int(df["impressions"].sum())
    total_convs = int(df["conversions"].sum())

    return {
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_rev, 2),
        "portfolio_roas": round(total_rev / max(total_spend, 1.0), 2),
        "mer": round(total_rev / max(total_spend, 1.0), 2),  # Marketing Efficiency Ratio
        "portfolio_cpa": round(total_spend / max(total_convs, 1), 2),
        "portfolio_cpc": round(total_spend / max(total_clicks, 1), 2),
        "portfolio_ctr": round((total_clicks / max(total_imps, 1)) * 100, 2),
        "portfolio_cvr": round((total_convs / max(total_clicks, 1)) * 100, 2),
        "total_conversions": total_convs
    }

