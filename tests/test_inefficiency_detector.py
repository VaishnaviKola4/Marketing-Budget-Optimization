"""
Unit tests for the Inefficiency and Waste Detector.
"""

import pytest
from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter
from marketing_budget_optimizer.optimizer.inefficiency_detector import InefficiencyDetector


def test_inefficiency_detector():
    df = MarketingDataLoader.load_campaign_data(DATA_DIR / "campaign_performance.csv")
    fitter = SaturationCurveFitter(curve_type="hill")
    fitter.fit_from_dataframe(df)

    detector = InefficiencyDetector()
    flags = detector.scan_campaigns(df, curve_fitter=fitter)

    assert isinstance(flags, list)
    assert len(flags) > 0

    first = flags[0]
    assert hasattr(first, "campaign_id")
    assert hasattr(first, "issue_type")
    assert hasattr(first, "severity")
    assert hasattr(first, "waste_estimate")
    assert first.waste_estimate >= 0.0

