"""
Data Loader and Validator for Marketing Budget Optimizer.
Loads CSV, JSON, or DataFrames, validates against schemas, and performs preprocessing.
"""

import pandas as pd
from pathlib import Path
from typing import Union, List, Optional
from pydantic import ValidationError

from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.schemas import CampaignRecord, CustomerTouchpoint


class MarketingDataLoader:
    """Handles loading, validation, and preprocessing of campaign performance and journey data."""

    @staticmethod
    def load_campaign_data(
        source: Union[str, Path, pd.DataFrame] = DATA_DIR / "campaign_performance.csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Loads and validates campaign performance data."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Campaign dataset not found at {path}. Run data generator first.")
            df = pd.read_csv(path)
        elif isinstance(source, pd.DataFrame):
            df = source.copy()
        else:
            raise ValueError(f"Unsupported data source type: {type(source)}")

        # Required columns
        required_cols = {"date", "campaign_id", "campaign_name", "channel", "spend", "impressions", "clicks", "conversions", "revenue"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Input data is missing required columns: {missing}")

        # Basic type conversions
        df["date"] = pd.to_datetime(df["date"])
        for col in ["spend", "revenue"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        for col in ["impressions", "clicks", "conversions"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # Apply date filters if requested
        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date)]

        # Calculated KPIs
        df["roas"] = (df["revenue"] / df["spend"].replace(0, float("nan"))).fillna(0.0).round(2)
        df["cpa"] = (df["spend"] / df["conversions"].replace(0, float("nan"))).fillna(0.0).round(2)
        df["cpc"] = (df["spend"] / df["clicks"].replace(0, float("nan"))).fillna(0.0).round(2)
        df["ctr"] = (df["clicks"] / df["impressions"].replace(0, float("nan"))).fillna(0.0).round(4)
        df["cvr"] = (df["conversions"] / df["clicks"].replace(0, float("nan"))).fillna(0.0).round(4)

        return df.sort_values(by="date").reset_index(drop=True)

    @staticmethod
    def load_customer_journeys(
        source: Union[str, Path, pd.DataFrame] = DATA_DIR / "customer_journeys.csv"
    ) -> pd.DataFrame:
        """Loads customer multi-touch journey path data."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Customer journeys not found at {path}.")
            df = pd.read_csv(path)
        elif isinstance(source, pd.DataFrame):
            df = source.copy()
        else:
            raise ValueError(f"Unsupported data source type: {type(source)}")

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["order_value"] = pd.to_numeric(df["order_value"], errors="coerce").fillna(0.0)
        df["converted"] = df["converted"].astype(bool)

        return df.sort_values(by=["customer_id", "timestamp"]).reset_index(drop=True)

    @staticmethod
    def get_channel_aggregates(df: pd.DataFrame) -> pd.DataFrame:
        """Computes aggregate channel-level KPIs from a campaign DataFrame."""
        agg_df = df.groupby("channel").agg(
            total_spend=("spend", "sum"),
            total_revenue=("revenue", "sum"),
            total_impressions=("impressions", "sum"),
            total_clicks=("clicks", "sum"),
            total_conversions=("conversions", "sum"),
            active_campaigns=("campaign_id", "nunique"),
            avg_daily_spend=("spend", "mean"),
            avg_daily_revenue=("revenue", "mean")
        ).reset_index()

        agg_df["roas"] = (agg_df["total_revenue"] / agg_df["total_spend"]).round(2)
        agg_df["cpa"] = (agg_df["total_spend"] / agg_df["total_conversions"].clip(lower=1)).round(2)
        agg_df["cpc"] = (agg_df["total_spend"] / agg_df["total_clicks"].clip(lower=1)).round(2)
        agg_df["ctr"] = (agg_df["total_clicks"] / agg_df["total_impressions"].clip(lower=1)).round(4)
        agg_df["cvr"] = (agg_df["total_conversions"] / agg_df["total_clicks"].clip(lower=1)).round(4)

        return agg_df

