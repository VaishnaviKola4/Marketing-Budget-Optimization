"""
Visualization Utilities for Marketing Performance and AI Optimization.
Generates interactive Plotly figures for saturation curves, reallocation deltas,
waterfalls, and attribution model comparisons.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from marketing_budget_optimizer.data.schemas import OptimizationSummary, ChannelOptimizationResult
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter


class VisualizationFactory:
    """Builds interactive Plotly visualizations for dashboards and reports."""

    THEME_COLORS = {
        "primary": "#4F46E5",     # Indigo
        "secondary": "#06B6D4",   # Cyan
        "success": "#10B981",     # Emerald
        "warning": "#F59E0B",     # Amber
        "danger": "#EF4444",      # Rose
        "dark": "#1E293B",        # Slate
        "light_bg": "#F8FAFC"
    }

    @classmethod
    def plot_saturation_curves(
        cls,
        curve_fitter: SaturationCurveFitter,
        summary: Optional[OptimizationSummary] = None,
        max_spend_factor: float = 2.0
    ) -> go.Figure:
        """Plots diminishing return saturation curves with current and recommended operating points."""
        fig = go.Figure()

        alloc_map = {res.channel: res for res in summary.channel_allocations} if summary else {}

        color_palette = px.colors.qualitative.Bold

        for idx, (channel, params) in enumerate(curve_fitter.channel_models.items()):
            color = color_palette[idx % len(color_palette)]
            
            # Channel spend domain
            rec = alloc_map.get(channel)
            ref_spend = rec.current_spend if rec else 4000.0
            spend_range = np.linspace(0, ref_spend * max_spend_factor, 120)
            rev_curve = curve_fitter.predict(channel, spend_range)

            # Draw curve
            fig.add_trace(go.Scatter(
                x=spend_range,
                y=rev_curve,
                mode="lines",
                name=f"{channel}",
                line=dict(color=color, width=2.5),
                hovertemplate="Spend: $%{x:,.0f}<br>Projected Rev: $%{y:,.0f}<extra></extra>"
            ))

            # Mark current and recommended points if summary is provided
            if rec:
                # Current Operating Point
                fig.add_trace(go.Scatter(
                    x=[rec.current_spend],
                    y=[rec.predicted_current_revenue],
                    mode="markers",
                    name=f"{channel} (Current)",
                    marker=dict(size=10, color=color, symbol="circle-open", line=dict(width=2.5, color=color)),
                    showlegend=False,
                    hovertemplate=f"<b>{channel} [CURRENT]</b><br>Spend: ${rec.current_spend:,.0f}<br>Rev: ${rec.predicted_current_revenue:,.0f}<extra></extra>"
                ))
                # Recommended Operating Point
                fig.add_trace(go.Scatter(
                    x=[rec.recommended_spend],
                    y=[rec.predicted_recommended_revenue],
                    mode="markers",
                    name=f"{channel} (Recommended)",
                    marker=dict(size=12, color=color, symbol="star"),
                    showlegend=False,
                    hovertemplate=f"<b>{channel} [RECOMMENDED]</b><br>Spend: ${rec.recommended_spend:,.0f}<br>Rev: ${rec.predicted_recommended_revenue:,.0f}<extra></extra>"
                ))

        fig.update_layout(
            title="<b>Diminishing Returns Saturation Curves & Channel Operating Points</b>",
            xaxis_title="<b>Daily Ad Spend ($)</b>",
            yaxis_title="<b>Predicted Daily Revenue ($)</b>",
            template="plotly_white",
            hovermode="closest",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=80, b=40),
            height=520
        )
        return fig

    @classmethod
    def plot_reallocation_deltas(cls, summary: OptimizationSummary) -> go.Figure:
        """Plots spend shift delta bar chart by channel."""
        channels = [r.channel for r in summary.channel_allocations]
        deltas = [r.spend_delta for r in summary.channel_allocations]
        colors = [cls.THEME_COLORS["success"] if d >= 0 else cls.THEME_COLORS["danger"] for d in deltas]

        fig = go.Figure(go.Bar(
            x=channels,
            y=deltas,
            marker_color=colors,
            text=[f"{'+' if d>=0 else ''}${d:,.0f}" for d in deltas],
            textposition="auto"
        ))

        fig.update_layout(
            title="<b>Recommended Budget Reallocation Delta by Channel ($)</b>",
            xaxis_title="Marketing Channel",
            yaxis_title="Budget Change ($)",
            template="plotly_white",
            height=420,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        return fig

    @classmethod
    def plot_attribution_comparison(cls, df_attrib: pd.DataFrame) -> go.Figure:
        """Compares revenue attribution across different attribution models."""
        fig = go.Figure()

        models = [
            ("first_touch_rev", "First-Touch", "#3B82F6"),
            ("last_touch_rev", "Last-Touch", "#10B981"),
            ("linear_rev", "Linear", "#8B5CF6"),
            ("time_decay_rev", "Time-Decay", "#F59E0B"),
            ("position_based_rev", "Position-Based (U-Shape)", "#EC4899")
        ]

        for col, label, color in models:
            if col in df_attrib.columns:
                fig.add_trace(go.Bar(
                    name=label,
                    x=df_attrib["channel"],
                    y=df_attrib[col],
                    marker_color=color
                ))

        fig.update_layout(
            barmode="group",
            title="<b>Multi-Touch Attribution Revenue Comparison by Model</b>",
            xaxis_title="Channel",
            yaxis_title="Attributed Revenue ($)",
            template="plotly_white",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=80, b=40)
        )
        return fig

    @classmethod
    def plot_cpa_roas_bubble(cls, df_campaigns: pd.DataFrame) -> go.Figure:
        """Creates a bubble chart of CPA vs ROAS with spend as bubble size."""
        camp_agg = df_campaigns.groupby(["campaign_name", "channel"]).agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            conversions=("conversions", "sum")
        ).reset_index()

        camp_agg["roas"] = (camp_agg["revenue"] / camp_agg["spend"].clip(lower=1)).round(2)
        camp_agg["cpa"] = (camp_agg["spend"] / camp_agg["conversions"].clip(lower=1)).round(2)

        fig = px.scatter(
            camp_agg,
            x="cpa",
            y="roas",
            size="spend",
            color="channel",
            hover_name="campaign_name",
            size_max=35,
            title="<b>Campaign Efficiency Matrix: CPA vs ROAS (Bubble Size = Spend)</b>",
            labels={"cpa": "Cost Per Acquisition (CPA) $", "roas": "Return on Ad Spend (ROAS)"},
            template="plotly_white"
        )
        # Add target quadrant lines
        fig.add_hline(y=2.0, line_dash="dash", line_color="green", annotation_text="Target ROAS (2.0x)")
        fig.add_vline(x=65.0, line_dash="dash", line_color="red", annotation_text="Max CPA Threshold ($65)")

        fig.update_layout(height=480, margin=dict(l=40, r=40, t=60, b=40))
        return fig

