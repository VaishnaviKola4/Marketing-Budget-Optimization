"""
Marketing Mix Model (MMM) Engine.
Integrates Adstock Carryover, Diminishing Returns, and Multi-channel Regression
to decompose base vs incremental sales and determine channel elasticities.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import r2_score, mean_absolute_percentage_error

from marketing_budget_optimizer.models.adstock import AdstockTransformer
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter


class MarketingMixModel:
    """
    Econometric Marketing Mix Model (MMM).
    Decomposes total revenue into:
    1. Base Sales (baseline demand, brand equity, organic traffic)
    2. Incremental Sales driven by each marketing channel (with carryover + saturation)
    """

    def __init__(self, regularization: float = 1.0, adstock_decay_default: float = 0.3):
        self.regularization = regularization
        self.adstock_decay_default = adstock_decay_default
        self.channel_decay_rates: Dict[str, float] = {}
        self.channel_weights: Dict[str, float] = {}
        self.base_sales: float = 0.0
        self.r2: float = 0.0
        self.mape: float = 0.0
        self.channels: List[str] = []
        self.curve_fitter = SaturationCurveFitter(curve_type="hill")
        self.model = Ridge(alpha=regularization, positive=True, fit_intercept=True)
        self.is_fitted = False

    def fit(
        self,
        df: pd.DataFrame,
        decay_overrides: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Fits the MMM model from a panel or aggregate dataset.
        
        Args:
            df: DataFrame containing ['date', 'channel', 'spend', 'revenue']
            decay_overrides: Optional dict specifying channel decay rates.
        """
        # Fit saturation curves per channel
        self.curve_fitter.fit_from_dataframe(df)

        # Pivot daily data to channel matrix
        daily_pivot_spend = df.pivot_table(index="date", columns="channel", values="spend", aggfunc="sum").fillna(0.0)
        daily_revenue = df.groupby("date")["revenue"].sum().reindex(daily_pivot_spend.index).fillna(0.0)

        self.channels = list(daily_pivot_spend.columns)
        
        # Determine decay rates
        decay_map = decay_overrides or {
            "Google_Search": 0.20,
            "Meta_Ads": 0.35,
            "Amazon_Sponsored_Products": 0.15,
            "TikTok_Ads": 0.25,
            "Email_Marketing": 0.45,
            "Influencer_Partnerships": 0.60,
            "Affiliate_Marketing": 0.20
        }
        for ch in self.channels:
            self.channel_decay_rates[ch] = decay_map.get(ch, self.adstock_decay_default)

        # Apply Adstock transformation
        adstocked_features = np.zeros_like(daily_pivot_spend.values, dtype=float)
        for idx, ch in enumerate(self.channels):
            decay = self.channel_decay_rates[ch]
            adstocked_features[:, idx] = AdstockTransformer.geometric_adstock(
                daily_pivot_spend[ch].values, decay_rate=decay
            )

        # Fit positive-constrained Ridge Regression
        X = adstocked_features
        y = daily_revenue.values

        self.model.fit(X, y)
        y_pred = self.model.predict(X)

        self.base_sales = float(max(0.0, self.model.intercept_))
        for idx, ch in enumerate(self.channels):
            self.channel_weights[ch] = float(self.model.coef_[idx])

        self.r2 = float(max(0.0, r2_score(y, y_pred)))
        self.mape = float(mean_absolute_percentage_error(y, np.maximum(y_pred, 1.0)))
        self.is_fitted = True

        # Calculate Channel Contribution Share
        total_attributed_pred = np.sum(X * self.model.coef_, axis=0)
        total_pred_rev = float(np.sum(y_pred))
        contribution_share = {}
        for idx, ch in enumerate(self.channels):
            share = float(total_attributed_pred[idx] / max(total_pred_rev, 1.0))
            contribution_share[ch] = round(share * 100, 2)

        return {
            "r2_score": round(self.r2, 4),
            "mape": round(self.mape, 4),
            "base_sales_daily": round(self.base_sales, 2),
            "base_sales_share_pct": round((self.base_sales * len(y) / max(total_pred_rev, 1.0)) * 100, 2),
            "channel_coefficients": {ch: round(self.channel_weights[ch], 4) for ch in self.channels},
            "channel_contribution_share_pct": contribution_share
        }

    def predict_daily(self, spend_dict: Dict[str, float]) -> float:
        """Predicts daily revenue given a distribution of daily spend across channels."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")

        total_rev = self.base_sales
        for ch, spend in spend_dict.items():
            if ch in self.curve_fitter.channel_models:
                # Use response curve
                total_rev += self.curve_fitter.predict(ch, spend)
            elif ch in self.channel_weights:
                total_rev += self.channel_weights[ch] * spend
        return float(total_rev)

