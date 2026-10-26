"""
FastAPI REST API Service for Marketing Budget Optimizer.
Provides endpoints for AI budget optimization, revenue prediction,
inefficiency scanning, and attribution analysis.
"""

from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from marketing_budget_optimizer import __version__
from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.schemas import (
    OptimizationRequest,
    OptimizationSummary,
    InefficiencyFlag
)
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.data.generator import MarketingDataGenerator
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter
from marketing_budget_optimizer.models.attribution import MultiTouchAttributor
from marketing_budget_optimizer.optimizer.budget_allocator import BudgetAllocator
from marketing_budget_optimizer.optimizer.inefficiency_detector import InefficiencyDetector


# In-memory service state
state: Dict[str, Any] = {
    "campaign_df": None,
    "journeys_df": None,
    "curve_fitter": None,
    "allocator": None,
    "detector": None
}


def get_or_init_state():
    """Initializes and caches models if not already in memory."""
    if state["campaign_df"] is None:
        try:
            df = MarketingDataLoader.load_campaign_data()
        except FileNotFoundError:
            gen = MarketingDataGenerator()
            gen.generate_all_and_save()
            df = MarketingDataLoader.load_campaign_data()

        state["campaign_df"] = df
        try:
            state["journeys_df"] = MarketingDataLoader.load_customer_journeys()
        except Exception:
            state["journeys_df"] = pd.DataFrame()

        fitter = SaturationCurveFitter(curve_type="hill")
        fitter.fit_from_dataframe(df)
        state["curve_fitter"] = fitter
        state["allocator"] = BudgetAllocator(curve_fitter=fitter)
        state["detector"] = InefficiencyDetector()

    return state


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup initialization
    get_or_init_state()
    yield


app = FastAPI(
    title="Marketing Budget Optimizer API",
    description="Enterprise AI engine for marketing mix modeling, waste detection, and constrained budget reallocation.",
    version=__version__,
    lifespan=lifespan
)

# Enable CORS for external dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
def health_check():
    """Returns service health status and version."""
    return {
        "status": "healthy",
        "service": "Marketing Budget Optimizer",
        "version": __version__
    }


@app.get("/api/v1/channels", tags=["Performance"])
def get_channels():
    """Returns active marketing channels and historical aggregate KPIs."""
    s = get_or_init_state()
    df = s["campaign_df"]
    aggs = MarketingDataLoader.get_channel_aggregates(df)
    return aggs.to_dict(orient="records")


@app.post("/api/v1/optimize", response_model=OptimizationSummary, tags=["Optimization"])
def optimize_budget(request: OptimizationRequest):
    """
    Solves non-linear constrained budget allocation problem to maximize revenue,
    conversions, or profit across marketing channels.
    """
    s = get_or_init_state()
    df = s["campaign_df"]
    
    # Calculate baseline average daily spend per channel
    current_spends = df.groupby("channel")["spend"].mean().to_dict()

    try:
        summary = s["allocator"].optimize(current_spend_dict=current_spends, request=request)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.post("/api/v1/predict", tags=["Prediction"])
def predict_revenue(spend_distribution: Dict[str, float]):
    """
    Predicts expected daily revenue given a spend distribution across channels.
    """
    s = get_or_init_state()
    fitter: SaturationCurveFitter = s["curve_fitter"]

    predictions = {}
    total_rev = 0.0
    for ch, spend in spend_distribution.items():
        if ch in fitter.channel_models:
            rev = float(fitter.predict(ch, spend))
            predictions[ch] = round(rev, 2)
            total_rev += rev

    return {
        "total_predicted_revenue": round(total_rev, 2),
        "channel_breakdown": predictions
    }


@app.get("/api/v1/inefficiencies", response_model=List[InefficiencyFlag], tags=["Diagnostics"])
def detect_inefficiencies():
    """
    Scans historical campaigns to identify ad fatigue, saturation decay,
    and high-CPA bleeders.
    """
    s = get_or_init_state()
    df = s["campaign_df"]
    fitter = s["curve_fitter"]
    detector: InefficiencyDetector = s["detector"]

    flags = detector.scan_campaigns(df_campaigns=df, curve_fitter=fitter)
    return flags


@app.get("/api/v1/attribution", tags=["Attribution"])
def get_attribution():
    """
    Computes Multi-Touch Attribution across First-Touch, Last-Touch, Linear,
    Time-Decay, and Position-Based models.
    """
    s = get_or_init_state()
    df_j = s["journeys_df"]

    if df_j.empty:
        raise HTTPException(status_code=404, detail="No customer journeys data available.")

    attributor = MultiTouchAttributor()
    attrib_df = attributor.compute_all_attributions(df_j)
    return attrib_df.to_dict(orient="records")


@app.post("/api/v1/data/generate", tags=["Data"])
def regenerate_data(days: int = Query(180, ge=30, le=730), customers: int = Query(2500, ge=500, le=10000)):
    """Regenerates realistic synthetic dataset on disk and refreshes state."""
    gen = MarketingDataGenerator()
    paths = gen.generate_all_and_save()
    
    # Reset in-memory cache
    state["campaign_df"] = None
    state["journeys_df"] = None
    get_or_init_state()

    return {"message": "Data generated and models retrained successfully.", "files": paths}
