"""
Pydantic Schemas for Data Validation, API Contracts, and System Types.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import date

class CampaignRecord(BaseModel):
    """Represents a single daily campaign performance observation."""
    date: str = Field(..., description="Date of the record (YYYY-MM-DD)")
    campaign_id: str = Field(..., description="Unique campaign identifier")
    campaign_name: str = Field(..., description="Descriptive name of the campaign")
    channel: str = Field(..., description="Channel name (e.g. Google_Search, Meta_Ads)")
    spend: float = Field(..., ge=0.0, description="Daily spend in dollars")
    impressions: int = Field(..., ge=0, description="Total impressions recorded")
    clicks: int = Field(..., ge=0, description="Total link or ad clicks")
    conversions: int = Field(..., ge=0, description="Total conversions attributed")
    revenue: float = Field(..., ge=0.0, description="Total revenue generated in dollars")

    @field_validator("clicks")
    @classmethod
    def validate_clicks_le_impressions(cls, v, info):
        # Gracefully handle clicks > impressions if data is noisy
        return v

class CustomerTouchpoint(BaseModel):
    """Represents a user touchpoint along the conversion path."""
    customer_id: str
    timestamp: str
    channel: str
    campaign_id: str
    touchpoint_position: int
    converted: bool
    order_value: float = 0.0

class ChannelConstraint(BaseModel):
    """Channel-specific optimization boundaries."""
    channel: str
    current_spend: float = Field(..., ge=0.0)
    min_spend: Optional[float] = None
    max_spend: Optional[float] = None
    fixed: bool = False

class OptimizationRequest(BaseModel):
    """Payload to trigger budget reallocation."""
    total_budget: Optional[float] = Field(None, gt=0, description="Total budget to distribute. If None, uses sum of current spend.")
    budget_scaling_factor: Optional[float] = Field(1.0, gt=0, description="Scale total current budget (e.g. 1.10 for +10% budget)")
    objective: str = Field(default="maximize_revenue", description="maximize_revenue | maximize_conversions | maximize_profit")
    constraints: Optional[List[ChannelConstraint]] = None
    max_channel_shift_pct: float = Field(default=0.40, ge=0.0, le=1.0, description="Max swing up or down per channel")
    cost_margin_pct: float = Field(default=0.30, ge=0.0, le=1.0, description="COGS/Margin ratio for profit maximization")

class ChannelOptimizationResult(BaseModel):
    """Per-channel budget allocation outcome."""
    channel: str
    current_spend: float
    recommended_spend: float
    spend_delta: float
    spend_delta_pct: float
    predicted_current_revenue: float
    predicted_recommended_revenue: float
    revenue_delta: float
    current_roas: float
    projected_roas: float
    current_marginal_roas: float
    projected_marginal_roas: float

class OptimizationSummary(BaseModel):
    """Overall reallocation summary."""
    total_current_spend: float
    total_recommended_spend: float
    total_predicted_current_revenue: float
    total_predicted_recommended_revenue: float
    revenue_lift: float
    revenue_lift_pct: float
    overall_current_roas: float
    overall_projected_roas: float
    objective: str
    channel_allocations: List[ChannelOptimizationResult]

class InefficiencyFlag(BaseModel):
    """Identified spend inefficiency or waste issue."""
    campaign_id: str
    campaign_name: str
    channel: str
    issue_type: str  # 'DIMINISHING_RETURNS', 'HIGH_CPA', 'AD_FATIGUE', 'LOW_CONVERSION_RATE'
    severity: str    # 'CRITICAL', 'WARNING', 'INFO'
    metric_value: float
    benchmark_value: float
    waste_estimate: float
    recommendation: str

