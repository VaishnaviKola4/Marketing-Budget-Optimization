"""
Unit tests for Adstock, Saturation Curves, MMM, and Multi-touch Attribution.
"""

import numpy as np
import pandas as pd
import pytest
from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.models.adstock import AdstockTransformer
from marketing_budget_optimizer.models.saturation import (
    SaturationCurveFitter,
    hill_function,
    hill_derivative
)
from marketing_budget_optimizer.models.mmm import MarketingMixModel
from marketing_budget_optimizer.models.attribution import MultiTouchAttributor


def test_geometric_adstock():
    spend = np.array([100.0, 0.0, 0.0, 0.0])
    adstocked = AdstockTransformer.geometric_adstock(spend, decay_rate=0.5)
    assert adstocked[0] == 100.0
    assert adstocked[1] == 50.0
    assert adstocked[2] == 25.0
    assert adstocked[3] == 12.5


def test_hill_function_and_derivative():
    spend = np.array([100.0, 500.0, 1000.0, 5000.0])
    vmax = 10000.0
    k = 2000.0
    s = 1.2
    rev = hill_function(spend, vmax, k, s)
    assert len(rev) == 4
    assert np.all(np.diff(rev) > 0)  # Monotonically increasing
    
    # Derivative test
    m_roas = hill_derivative(1000.0, vmax, k, s)
    assert m_roas > 0


def test_saturation_curve_fitter():
    df = MarketingDataLoader.load_campaign_data(DATA_DIR / "campaign_performance.csv")
    fitter = SaturationCurveFitter(curve_type="hill")
    models = fitter.fit_from_dataframe(df)
    assert len(models) > 0
    assert "Google_Search" in models
    
    pred_rev = fitter.predict("Google_Search", 2000.0)
    assert pred_rev > 0
    
    m_roas = fitter.marginal_roas("Google_Search", 2000.0)
    assert m_roas > 0


def test_marketing_mix_model():
    df = MarketingDataLoader.load_campaign_data(DATA_DIR / "campaign_performance.csv")
    mmm = MarketingMixModel(regularization=1.0)
    fit_summary = mmm.fit(df)
    assert "r2_score" in fit_summary
    assert "base_sales_daily" in fit_summary
    assert fit_summary["r2_score"] >= 0.0


def test_multitouch_attribution():
    df_j = MarketingDataLoader.load_customer_journeys(DATA_DIR / "customer_journeys.csv")
    attributor = MultiTouchAttributor()
    res = attributor.compute_all_attributions(df_j)
    assert not res.empty
    assert "first_touch_rev" in res.columns
    assert "last_touch_rev" in res.columns
    assert "linear_rev" in res.columns

