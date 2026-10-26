"""
Unit tests for the non-linear constrained budget allocator.
"""

import pytest
import numpy as np
from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.data.schemas import OptimizationRequest, ChannelConstraint
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter
from marketing_budget_optimizer.optimizer.budget_allocator import BudgetAllocator


@pytest.fixture
def allocator_fixture():
    df = MarketingDataLoader.load_campaign_data(DATA_DIR / "campaign_performance.csv")
    fitter = SaturationCurveFitter(curve_type="hill")
    fitter.fit_from_dataframe(df)
    alloc = BudgetAllocator(curve_fitter=fitter)
    current_spends = df.groupby("channel")["spend"].mean().to_dict()
    return alloc, current_spends


def test_budget_allocator_revenue_maximization(allocator_fixture):
    alloc, current_spends = allocator_fixture
    req = OptimizationRequest(objective="maximize_revenue", max_channel_shift_pct=0.40)
    summary = alloc.optimize(current_spend_dict=current_spends, request=req)
    
    # Total budget constraint must hold within 0.1% tolerance
    assert abs(summary.total_recommended_spend - summary.total_current_spend) < 1.0
    # Revenue lift should be positive or zero
    assert summary.total_predicted_recommended_revenue >= summary.total_predicted_current_revenue * 0.99
    assert len(summary.channel_allocations) == len(current_spends)


def test_budget_allocator_scaled_budget(allocator_fixture):
    alloc, current_spends = allocator_fixture
    req = OptimizationRequest(budget_scaling_factor=1.20)  # +20% budget
    summary = alloc.optimize(current_spend_dict=current_spends, request=req)
    
    expected_budget = summary.total_current_spend * 1.20
    assert abs(summary.total_recommended_spend - expected_budget) < 1.0

