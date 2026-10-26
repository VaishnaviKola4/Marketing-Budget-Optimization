"""
Synthetic Data Generator for Marketing Budget Optimization.
Generates multi-channel daily performance, adstock carryover, saturation curves,
and customer multi-touch attribution paths.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict

from marketing_budget_optimizer.config import DATA_DIR, DEFAULT_CHANNELS


class MarketingDataGenerator:
    """
    Generates realistic marketing campaign data simulating:
    - Channel-specific CPM, CPC, and conversion rates
    - Non-linear diminishing returns (Hill / Log-logistic saturation)
    - Adstock carryover decay effects
    - Weekly and seasonal calendar cycles
    - Inefficiencies: fatigue in saturated campaigns, budget bleeders
    """

    def __init__(self, random_seed: int = 42):
        np.random.seed(random_seed)
        self.channels = {
            "Google_Search": {
                "base_spend": 2800,
                "spend_volatility": 400,
                "cpc_mean": 2.20,
                "ctr_mean": 0.045,
                "cvr_mean": 0.052,
                "aov_mean": 115.0,
                "saturation_k": 5500,  # Spend half-saturation point
                "saturation_s": 1.4,   # Shape exponent
                "max_potential_revenue": 24000,
                "adstock_decay": 0.25,
            },
            "Meta_Ads": {
                "base_spend": 3500,
                "spend_volatility": 650,
                "cpc_mean": 1.45,
                "ctr_mean": 0.022,
                "cvr_mean": 0.028,
                "aov_mean": 95.0,
                "saturation_k": 4200,  # Starts saturating faster
                "saturation_s": 1.2,
                "max_potential_revenue": 20000,
                "adstock_decay": 0.40,
            },
            "Amazon_Sponsored_Products": {
                "base_spend": 2200,
                "spend_volatility": 350,
                "cpc_mean": 1.10,
                "ctr_mean": 0.038,
                "cvr_mean": 0.085,  # High buyer intent
                "aov_mean": 68.0,
                "saturation_k": 4800,
                "saturation_s": 1.5,
                "max_potential_revenue": 22000,
                "adstock_decay": 0.15,
            },
            "TikTok_Ads": {
                "base_spend": 1600,
                "spend_volatility": 450,
                "cpc_mean": 0.75,
                "ctr_mean": 0.018,
                "cvr_mean": 0.016,
                "aov_mean": 75.0,
                "saturation_k": 2800,
                "saturation_s": 1.1,
                "max_potential_revenue": 9500,
                "adstock_decay": 0.30,
            },
            "Email_Marketing": {
                "base_spend": 450,
                "spend_volatility": 80,
                "cpc_mean": 0.20,
                "ctr_mean": 0.080,
                "cvr_mean": 0.065,
                "aov_mean": 130.0,
                "saturation_k": 850,   # Saturated quickly because list size is finite
                "saturation_s": 1.8,
                "max_potential_revenue": 6500,
                "adstock_decay": 0.50,
            },
            "Influencer_Partnerships": {
                "base_spend": 1200,
                "spend_volatility": 700,
                "cpc_mean": 3.50,
                "ctr_mean": 0.030,
                "cvr_mean": 0.024,
                "aov_mean": 110.0,
                "saturation_k": 3200,
                "saturation_s": 1.3,
                "max_potential_revenue": 10500,
                "adstock_decay": 0.65, # Long memory carryover
            },
            "Affiliate_Marketing": {
                "base_spend": 800,
                "spend_volatility": 150,
                "cpc_mean": 0.90,
                "ctr_mean": 0.025,
                "cvr_mean": 0.040,
                "aov_mean": 105.0,
                "saturation_k": 2100,
                "saturation_s": 1.4,
                "max_potential_revenue": 7200,
                "adstock_decay": 0.20,
            }
        }

    def _hill_transform(self, spend: np.ndarray, vmax: float, k: float, s: float) -> np.ndarray:
        """Applies Hill saturation curve: R(s) = Vmax * (s^S) / (K^S + s^S)"""
        spend_s = np.power(spend, s)
        k_s = np.power(k, s)
        return vmax * (spend_s / (k_s + spend_s))

    def generate_daily_campaign_data(self, days: int = 180) -> pd.DataFrame:
        """Generates realistic daily campaign performance records over N days."""
        start_date = datetime.now() - timedelta(days=days)
        records = []

        campaign_names = {
            "Google_Search": ["Google_Brand_Exact", "Google_NonBrand_Generic", "Google_Competitor_Keywords"],
            "Meta_Ads": ["Meta_Prospecting_Lookalike", "Meta_Retargeting_Catalog", "Meta_Story_Reels_Video"],
            "Amazon_Sponsored_Products": ["Amazon_Auto_Discovery", "Amazon_Manual_Exact_ASIN", "Amazon_Brand_Defense"],
            "TikTok_Ads": ["TikTok_Spark_Ads_UGC", "TikTok_InFeed_Broad"],
            "Email_Marketing": ["Klaviyo_Automated_Flows", "Weekly_Promotional_Newsletter"],
            "Influencer_Partnerships": ["Micro_Influencer_Gifting", "Tier1_Creator_Sponsorships"],
            "Affiliate_Marketing": ["Coupon_Affiliates", "Content_Review_Affiliates"]
        }

        dates = [start_date + timedelta(days=i) for i in range(days)]

        for current_date in dates:
            date_str = current_date.strftime("%Y-%m-%d")
            day_of_week = current_date.weekday()
            # Seasonality multiplier: weekends higher for retail/e-commerce, dips midweek
            weekly_seasonality = 1.0 + 0.15 * np.sin((day_of_week / 7.0) * 2 * np.pi)
            
            # Holiday spike simulator around mid period
            mid_period = days // 2
            days_from_event = abs((current_date - (start_date + timedelta(days=mid_period))).days)
            holiday_multiplier = 1.0 + 0.45 * np.exp(-(days_from_event ** 2) / (2 * 6 ** 2))

            for channel_name, params in self.channels.items():
                c_campaigns = campaign_names[channel_name]
                channel_spend_today = max(50.0, np.random.normal(params["base_spend"], params["spend_volatility"]))
                channel_spend_today *= weekly_seasonality * holiday_multiplier

                # Split across individual campaigns
                weights = np.random.dirichlet(np.ones(len(c_campaigns)))

                for c_idx, c_name in enumerate(c_campaigns):
                    camp_spend = max(20.0, channel_spend_today * weights[c_idx])
                    
                    # Simulated ad fatigue or inefficiency in one specific campaign
                    is_fatigued = (c_name in ["Meta_Prospecting_Lookalike", "TikTok_InFeed_Broad"]) and (current_date > start_date + timedelta(days=90))
                    cpc_adj = params["cpc_mean"] * (1.35 if is_fatigued else 1.0) * np.random.uniform(0.9, 1.1)
                    ctr_adj = params["ctr_mean"] * (0.65 if is_fatigued else 1.0) * np.random.uniform(0.9, 1.1)
                    cvr_adj = params["cvr_mean"] * (0.75 if is_fatigued else 1.0) * np.random.uniform(0.92, 1.08)

                    clicks = max(1, int(camp_spend / cpc_adj))
                    impressions = max(clicks, int(clicks / max(0.005, ctr_adj)))
                    conversions = max(0, int(np.random.binomial(clicks, max(0.002, min(0.35, cvr_adj)))))

                    # Calculate revenue with Hill equation diminishing return baseline + conversion variation
                    hill_rev = self._hill_transform(
                        camp_spend,
                        params["max_potential_revenue"] / len(c_campaigns),
                        params["saturation_k"] / len(c_campaigns),
                        params["saturation_s"]
                    )
                    
                    actual_revenue = max(0.0, hill_rev * weekly_seasonality * holiday_multiplier * np.random.normal(1.0, 0.08))
                    if conversions > 0 and actual_revenue == 0.0:
                        actual_revenue = conversions * params["aov_mean"] * np.random.uniform(0.85, 1.15)

                    records.append({
                        "date": date_str,
                        "campaign_id": f"CAMP_{channel_name[:3].upper()}_{c_idx+1:02d}",
                        "campaign_name": c_name,
                        "channel": channel_name,
                        "spend": round(float(camp_spend), 2),
                        "impressions": int(impressions),
                        "clicks": int(clicks),
                        "conversions": int(conversions),
                        "revenue": round(float(actual_revenue), 2)
                    })

        df = pd.DataFrame(records)
        return df

    def generate_customer_journeys(self, num_customers: int = 1500) -> pd.DataFrame:
        """
        Generates customer conversion journeys across multiple touchpoints
        for multi-touch attribution analysis (First-touch, Last-touch, Linear, Time-decay).
        """
        records = []
        channels_list = list(self.channels.keys())
        channel_weights = [0.25, 0.22, 0.20, 0.13, 0.08, 0.07, 0.05]

        for cust_id in range(1, num_customers + 1):
            journey_len = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.35, 0.28, 0.18, 0.10, 0.06, 0.03])
            converted = np.random.rand() < (0.28 + 0.05 * journey_len)
            order_val = round(float(np.random.gamma(shape=5.0, scale=22.0)), 2) if converted else 0.0

            touch_days = sorted(np.random.randint(1, 45, size=journey_len))
            base_date = datetime.now() - timedelta(days=50)

            for step_idx in range(journey_len):
                assigned_channel = np.random.choice(channels_list, p=channel_weights)
                t_date = base_date + timedelta(days=int(touch_days[step_idx]), hours=int(np.random.randint(0, 23)))

                records.append({
                    "customer_id": f"CUST_{cust_id:05d}",
                    "timestamp": t_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "touchpoint_position": step_idx + 1,
                    "total_touchpoints": journey_len,
                    "channel": assigned_channel,
                    "campaign_id": f"CAMP_{assigned_channel[:3].upper()}_01",
                    "converted": bool(converted and (step_idx == journey_len - 1)),
                    "order_value": order_val if (converted and step_idx == journey_len - 1) else 0.0
                })

        return pd.DataFrame(records)

    def generate_all_and_save(self, output_dir: Path = DATA_DIR) -> Dict[str, str]:
        """Generates all datasets and saves them to the data directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Daily Campaign Performance (180 days)
        df_campaigns = self.generate_daily_campaign_data(days=180)
        camp_path = output_dir / "campaign_performance.csv"
        df_campaigns.to_csv(camp_path, index=False)

        # 2. Customer Journeys (2500 customer paths)
        df_journeys = self.generate_customer_journeys(num_customers=2500)
        journ_path = output_dir / "customer_journeys.csv"
        df_journeys.to_csv(journ_path, index=False)

        # 3. Channel Aggregates Summary
        summary = df_campaigns.groupby("channel").agg(
            total_spend=("spend", "sum"),
            total_revenue=("revenue", "sum"),
            total_impressions=("impressions", "sum"),
            total_clicks=("clicks", "sum"),
            total_conversions=("conversions", "sum")
        ).reset_index()

        summary["roas"] = (summary["total_revenue"] / summary["total_spend"]).round(2)
        summary["cpa"] = (summary["total_spend"] / summary["total_conversions"].clip(lower=1)).round(2)
        summary["cpc"] = (summary["total_spend"] / summary["total_clicks"].clip(lower=1)).round(2)
        summary["ctr"] = (summary["total_clicks"] / summary["total_impressions"].clip(lower=1)).round(4)
        summary["cvr"] = (summary["total_conversions"] / summary["total_clicks"].clip(lower=1)).round(4)

        summ_path = output_dir / "channel_summary.csv"
        summary.to_csv(summ_path, index=False)

        return {
            "campaign_performance": str(camp_path),
            "customer_journeys": str(journ_path),
            "channel_summary": str(summ_path)
        }


if __name__ == "__main__":
    gen = MarketingDataGenerator(random_seed=42)
    files = gen.generate_all_and_save()
    print("Generated synthetic datasets successfully:")
    for k, v in files.items():
        print(f"  - {k}: {v}")

