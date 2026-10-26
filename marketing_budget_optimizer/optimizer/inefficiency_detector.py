"""
Inefficiency and Waste Detection Engine.
Identifies over-saturated channels, creative ad fatigue, high-CPA bleeders,
and diminishing marginal return zones.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from marketing_budget_optimizer.config import OptimizationThresholds
from marketing_budget_optimizer.data.schemas import InefficiencyFlag
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter


class InefficiencyDetector:
    """
    Automated scanner that pinpoints wasteful spending and performance decay.
    """

    def __init__(self, thresholds: Optional[OptimizationThresholds] = None):
        self.thresholds = thresholds or OptimizationThresholds()

    def scan_campaigns(
        self,
        df_campaigns: pd.DataFrame,
        curve_fitter: Optional[SaturationCurveFitter] = None
    ) -> List[InefficiencyFlag]:
        """
        Scans campaign performance records to identify inefficiencies.
        """
        flags: List[InefficiencyFlag] = []
        df = df_campaigns.copy()
        df["date"] = pd.to_datetime(df["date"])

        # Aggregate campaign level performance
        camp_summary = df.groupby(["campaign_id", "campaign_name", "channel"]).agg(
            total_spend=("spend", "sum"),
            total_revenue=("revenue", "sum"),
            total_clicks=("clicks", "sum"),
            total_impressions=("impressions", "sum"),
            total_conversions=("conversions", "sum"),
            avg_daily_spend=("spend", "mean"),
            latest_date=("date", "max"),
            earliest_date=("date", "min")
        ).reset_index()

        camp_summary["roas"] = (camp_summary["total_revenue"] / camp_summary["total_spend"].clip(lower=1)).round(2)
        camp_summary["cpa"] = (camp_summary["total_spend"] / camp_summary["total_conversions"].clip(lower=1)).round(2)
        camp_summary["ctr"] = (camp_summary["total_clicks"] / camp_summary["total_impressions"].clip(lower=1)).round(4)

        # 1. Scan for Low-ROAS / High-CPA Bleeders
        for _, row in camp_summary.iterrows():
            if row["total_spend"] > 1000.0:  # Meaningful spend
                if row["roas"] < self.thresholds.min_roas_target:
                    waste = float((self.thresholds.min_roas_target - row["roas"]) / self.thresholds.min_roas_target * row["total_spend"] * 0.45)
                    flags.append(InefficiencyFlag(
                        campaign_id=str(row["campaign_id"]),
                        campaign_name=str(row["campaign_name"]),
                        channel=str(row["channel"]),
                        issue_type="LOW_ROAS_BLEEDER",
                        severity="CRITICAL" if row["roas"] < 1.2 else "WARNING",
                        metric_value=float(row["roas"]),
                        benchmark_value=float(self.thresholds.min_roas_target),
                        waste_estimate=round(waste, 2),
                        recommendation=(
                            f"Campaign ROAS ({row['roas']:.2f}x) is below hurdle rate ({self.thresholds.min_roas_target:.2f}x). "
                            f"Audit search terms, negative keywords, or pause non-converting ad sets to reclaim estimated ${waste:,.2f}."
                        )
                    ))

                if row["cpa"] > self.thresholds.max_cpa_threshold:
                    cpa_excess = float(row["cpa"] - self.thresholds.max_cpa_threshold)
                    waste = float(cpa_excess * row["total_conversions"] * 0.60)
                    flags.append(InefficiencyFlag(
                        campaign_id=str(row["campaign_id"]),
                        campaign_name=str(row["campaign_name"]),
                        channel=str(row["channel"]),
                        issue_type="EXCESSIVE_CPA",
                        severity="CRITICAL" if row["cpa"] > self.thresholds.max_cpa_threshold * 1.5 else "WARNING",
                        metric_value=float(row["cpa"]),
                        benchmark_value=float(self.thresholds.max_cpa_threshold),
                        waste_estimate=round(waste, 2),
                        recommendation=(
                            f"CPA of ${row['cpa']:.2f} exceeds threshold of ${self.thresholds.max_cpa_threshold:.2f}. "
                            "Refine audience targeting or landing page conversion flow to prevent margin erosion."
                        )
                    ))

        # 2. Scan for Creative Ad Fatigue (Comparing trailing 14 days vs prior 30 days)
        max_date = df["date"].max()
        cutoff_recent = max_date - pd.Timedelta(days=14)
        cutoff_prior = max_date - pd.Timedelta(days=45)

        recent_df = df[df["date"] >= cutoff_recent]
        prior_df = df[(df["date"] >= cutoff_prior) & (df["date"] < cutoff_recent)]

        recent_perf = recent_df.groupby("campaign_id").agg(
            recent_clicks=("clicks", "sum"),
            recent_imps=("impressions", "sum"),
            recent_spend=("spend", "sum"),
            recent_convs=("conversions", "sum")
        )
        recent_perf["recent_ctr"] = recent_perf["recent_clicks"] / recent_perf["recent_imps"].clip(lower=1)
        recent_perf["recent_cpa"] = recent_perf["recent_spend"] / recent_perf["recent_convs"].clip(lower=1)

        prior_perf = prior_df.groupby("campaign_id").agg(
            prior_clicks=("clicks", "sum"),
            prior_imps=("impressions", "sum"),
            prior_spend=("spend", "sum"),
            prior_convs=("conversions", "sum")
        )
        prior_perf["prior_ctr"] = prior_perf["prior_clicks"] / prior_perf["prior_imps"].clip(lower=1)
        prior_perf["prior_cpa"] = prior_perf["prior_spend"] / prior_perf["prior_convs"].clip(lower=1)

        merged_trends = camp_summary.merge(recent_perf, on="campaign_id", how="left").merge(prior_perf, on="campaign_id", how="left")

        for _, row in merged_trends.iterrows():
            if pd.notnull(row.get("recent_ctr")) and pd.notnull(row.get("prior_ctr")) and row["prior_ctr"] > 0:
                ctr_decay = float((row["prior_ctr"] - row["recent_ctr"]) / row["prior_ctr"])
                cpa_inflation = float((row["recent_cpa"] - row["prior_cpa"]) / max(row["prior_cpa"], 1.0))

                if ctr_decay >= self.thresholds.fatigue_ctr_drop_pct and cpa_inflation > 0.20:
                    fatigue_waste = float(row["recent_spend"] * 0.35)
                    flags.append(InefficiencyFlag(
                        campaign_id=str(row["campaign_id"]),
                        campaign_name=str(row["campaign_name"]),
                        channel=str(row["channel"]),
                        issue_type="AD_FATIGUE",
                        severity="WARNING",
                        metric_value=round(ctr_decay * 100, 1),
                        benchmark_value=round(self.thresholds.fatigue_ctr_drop_pct * 100, 1),
                        waste_estimate=round(fatigue_waste, 2),
                        recommendation=(
                            f"CTR dropped by {ctr_decay*100:.1f}% while CPA rose by {cpa_inflation*100:.1f}%. "
                            "Ad audience has become saturated. Rotate new creatives, video hooks, or expand audience lookalike brackets."
                        )
                    ))

        # 3. Scan for Channel Over-Saturation (Diminishing Marginal Returns)
        if curve_fitter and curve_fitter.channel_models:
            channel_agg = df.groupby("channel")["spend"].mean()
            for ch, avg_spend in channel_agg.items():
                if ch in curve_fitter.channel_models:
                    m_roas = curve_fitter.marginal_roas(str(ch), float(avg_spend))
                    if m_roas < self.thresholds.diminishing_marginal_roas_floor:
                        saturation_pt = curve_fitter.find_saturation_point(str(ch), target_mroas=self.thresholds.diminishing_marginal_roas_floor)
                        overspend = max(0.0, float(avg_spend - saturation_pt) * 30.0) # monthly waste
                        flags.append(InefficiencyFlag(
                            campaign_id=f"CH_{ch[:4].upper()}",
                            campaign_name=f"Channel:{ch}",
                            channel=str(ch),
                            issue_type="DIMINISHING_RETURNS",
                            severity="CRITICAL" if m_roas < 0.85 else "WARNING",
                            metric_value=round(m_roas, 2),
                            benchmark_value=round(self.thresholds.diminishing_marginal_roas_floor, 2),
                            waste_estimate=round(overspend, 2),
                            recommendation=(
                                f"Channel is operating deep in saturation: Marginal ROAS is {m_roas:.2f}x (below hurdle {self.thresholds.diminishing_marginal_roas_floor:.2f}x). "
                                f"Each additional dollar spent returns less than acceptable yield. Reallocate spend above ${saturation_pt:,.0f}/day to higher mROAS channels."
                            )
                        ))

        # Sort flags by waste estimate descending
        flags.sort(key=lambda x: x.waste_estimate, reverse=True)
        return flags

