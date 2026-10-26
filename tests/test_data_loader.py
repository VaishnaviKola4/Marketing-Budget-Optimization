"""
Unit tests for data loading, schema validation, and aggregation.
"""

import pytest
import pandas as pd
from pathlib import Path
from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.data.schemas import CampaignRecord


def test_load_campaign_data():
    df = MarketingDataLoader.load_campaign_data(DATA_DIR / "campaign_performance.csv")
    assert not df.empty
    assert "spend" in df.columns
    assert "revenue" in df.columns
    assert "roas" in df.columns
    assert "cpa" in df.columns
    assert len(df) > 100


def test_load_customer_journeys():
    df = MarketingDataLoader.load_customer_journeys(DATA_DIR / "customer_journeys.csv")
    assert not df.empty
    assert "customer_id" in df.columns
    assert "channel" in df.columns
    assert "converted" in df.columns


def test_channel_aggregates():
    df = MarketingDataLoader.load_campaign_data(DATA_DIR / "campaign_performance.csv")
    aggs = MarketingDataLoader.get_channel_aggregates(df)
    assert not aggs.empty
    assert "total_spend" in aggs.columns
    assert "total_revenue" in aggs.columns
    assert (aggs["total_spend"] > 0).all()

