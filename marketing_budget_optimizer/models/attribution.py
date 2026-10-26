"""
Multi-Touch Attribution (MTA) Models.
Compares First-Touch, Last-Touch, Linear, Time-Decay, and Position-Based (U-Shaped)
attribution rules to evaluate channel value across the customer conversion journey.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class MultiTouchAttributor:
    """
    Evaluates multi-touch customer journeys and attributes conversions and revenue
    across marketing channels using standard rule-based and algorithmic attribution models.
    """

    def __init__(self, half_life_days: float = 7.0):
        self.half_life_days = half_life_days

    def compute_all_attributions(self, df_journeys: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates credit share across all standard attribution models:
        - First Touch
        - Last Touch
        - Linear
        - Time Decay
        - Position Based (40-20-40)
        """
        # Filter for journeys that converted
        converted_custs = df_journeys[df_journeys["converted"]]["customer_id"].unique()
        df_conv = df_journeys[df_journeys["customer_id"].isin(converted_custs)].copy()

        if df_conv.empty:
            return pd.DataFrame()

        df_conv["timestamp"] = pd.to_datetime(df_conv["timestamp"])
        df_conv = df_conv.sort_values(by=["customer_id", "timestamp"])

        results = []

        for cust_id, group in df_conv.groupby("customer_id"):
            n_touches = len(group)
            order_val = group["order_value"].max()
            max_time = group["timestamp"].max()

            # 1. First Touch Weights
            w_first = np.zeros(n_touches)
            w_first[0] = 1.0

            # 2. Last Touch Weights
            w_last = np.zeros(n_touches)
            w_last[-1] = 1.0

            # 3. Linear Weights
            w_linear = np.ones(n_touches) / float(n_touches)

            # 4. Time Decay Weights (Exponential decay from last touch)
            days_diff = (max_time - group["timestamp"]).dt.total_seconds() / (24 * 3600.0)
            decay_lambda = np.log(2.0) / self.half_life_days
            w_decay = np.exp(-decay_lambda * days_diff.values)
            w_decay = w_decay / max(w_decay.sum(), 1e-9)

            # 5. Position-Based (40% first, 40% last, 20% middle)
            if n_touches == 1:
                w_pos = np.array([1.0])
            elif n_touches == 2:
                w_pos = np.array([0.5, 0.5])
            else:
                w_pos = np.zeros(n_touches)
                w_pos[0] = 0.40
                w_pos[-1] = 0.40
                w_pos[1:-1] = 0.20 / (n_touches - 2)

            for idx, (_, row) in enumerate(group.iterrows()):
                results.append({
                    "customer_id": cust_id,
                    "channel": row["channel"],
                    "order_value": order_val,
                    "first_touch_rev": order_val * w_first[idx],
                    "last_touch_rev": order_val * w_last[idx],
                    "linear_rev": order_val * w_linear[idx],
                    "time_decay_rev": order_val * w_decay[idx],
                    "position_based_rev": order_val * w_pos[idx],
                    "first_touch_conv": 1.0 * w_first[idx],
                    "last_touch_conv": 1.0 * w_last[idx],
                    "linear_conv": 1.0 * w_linear[idx],
                    "time_decay_conv": 1.0 * w_decay[idx],
                    "position_based_conv": 1.0 * w_pos[idx]
                })

        df_res = pd.DataFrame(results)

        # Aggregate by channel
        channel_attrib = df_res.groupby("channel").agg({
            "first_touch_rev": "sum",
            "last_touch_rev": "sum",
            "linear_rev": "sum",
            "time_decay_rev": "sum",
            "position_based_rev": "sum",
            "first_touch_conv": "sum",
            "last_touch_conv": "sum",
            "linear_conv": "sum",
            "time_decay_conv": "sum",
            "position_based_conv": "sum"
        }).round(2).reset_index()

        return channel_attrib

