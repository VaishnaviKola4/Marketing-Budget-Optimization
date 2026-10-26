"""
Global Configuration and Constants for Marketing Budget Optimizer.
"""

from pathlib import Path
from pydantic import BaseModel, Field

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"

# Core Marketing Channels
DEFAULT_CHANNELS = [
    "Google_Search",
    "Meta_Ads",
    "Amazon_Sponsored_Products",
    "TikTok_Ads",
    "Email_Marketing",
    "Influencer_Partnerships",
    "Affiliate_Marketing"
]

# Efficiency Thresholds
class OptimizationThresholds(BaseModel):
    min_roas_target: float = Field(default=2.0, description="Minimum acceptable ROAS")
    max_cpa_threshold: float = Field(default=65.0, description="Maximum allowable Cost Per Acquisition ($)")
    fatigue_ctr_drop_pct: float = Field(default=0.25, description="CTR drop signifying creative ad fatigue (25%)")
    diminishing_marginal_roas_floor: float = Field(default=1.1, description="Marginal ROAS floor below which spend is considered wasteful")
    default_reallocation_bound_pct: float = Field(default=0.40, description="Max +/- budget swing permitted per channel (40%)")

# Optimization Objectives
OBJECTIVE_REVENUE = "maximize_revenue"
OBJECTIVE_CONVERSIONS = "maximize_conversions"
OBJECTIVE_PROFIT = "maximize_profit"

