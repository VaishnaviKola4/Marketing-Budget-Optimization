# API and Interface Guide: Marketing Budget Optimizer

This guide details the REST API specifications, JSON contracts, response structures, and user interface controls provided by the Marketing Budget Optimizer.

---

## 1. REST API Specification

### Base URL
- Local: `http://localhost:8000`
- API Prefix: `/api/v1`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Redoc Documentation: `http://localhost:8000/redoc`

---

### Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check and system version |
| `GET` | `/api/v1/channels` | Aggregated channel metrics and historical KPIs |
| `POST`| `/api/v1/optimize` | Solves constrained non-linear budget allocation problem |
| `POST`| `/api/v1/predict` | Predicts revenue given channel spend distribution |
| `GET` | `/api/v1/inefficiencies`| Scans for creative fatigue, bleeders, and over-saturation |
| `GET` | `/api/v1/attribution` | Computes multi-touch attribution across 5 standard models |
| `POST`| `/api/v1/data/generate` | Generates realistic synthetic benchmark dataset |

---

### Detailed Endpoint Contracts

#### 1. System Health Check
- **Endpoint:** `GET /health` or `GET /api/v1/health`
- **Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "Marketing Budget Optimizer",
  "version": "1.0.0"
}
```

---

#### 2. Get Channels & Historical Baseline
- **Endpoint:** `GET /api/v1/channels`
- **Response:** `200 OK` (Array of channel performance objects)
```json
[
  {
    "channel": "Amazon_Sponsored_Products",
    "total_spend": 396000.0,
    "total_revenue": 1425600.0,
    "total_impressions": 7850000,
    "total_clicks": 298300,
    "total_conversions": 25355,
    "active_campaigns": 3,
    "avg_daily_spend": 2200.0,
    "avg_daily_revenue": 7920.0,
    "roas": 3.6,
    "cpa": 15.62,
    "cpc": 1.33,
    "ctr": 0.038,
    "cvr": 0.085
  }
]
```

---

#### 3. Optimize Budget Reallocation
- **Endpoint:** `POST /api/v1/optimize`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "total_budget": null,
  "budget_scaling_factor": 1.10,
  "objective": "maximize_revenue",
  "max_channel_shift_pct": 0.35,
  "cost_margin_pct": 0.30,
  "constraints": [
    {
      "channel": "Amazon_Sponsored_Products",
      "current_spend": 2200.0,
      "min_spend": 2000.0,
      "max_spend": 3500.0,
      "fixed": false
    }
  ]
}
```

- **Response:** `200 OK`
```json
{
  "total_current_spend": 12550.0,
  "total_recommended_spend": 13805.0,
  "total_predicted_current_revenue": 78540.0,
  "total_predicted_recommended_revenue": 87920.0,
  "revenue_lift": 9380.0,
  "revenue_lift_pct": 11.94,
  "overall_current_roas": 6.26,
  "overall_projected_roas": 6.37,
  "objective": "maximize_revenue",
  "channel_allocations": [
    {
      "channel": "Amazon_Sponsored_Products",
      "current_spend": 2200.0,
      "recommended_spend": 2950.0,
      "spend_delta": 750.0,
      "spend_delta_pct": 34.09,
      "predicted_current_revenue": 14200.0,
      "predicted_recommended_revenue": 17850.0,
      "revenue_delta": 3650.0,
      "current_roas": 6.45,
      "projected_roas": 6.05,
      "current_marginal_roas": 3.25,
      "projected_marginal_roas": 2.15
    }
  ]
}
```

---

#### 4. Predict Daily Revenue
- **Endpoint:** `POST /api/v1/predict`
- **Request Body:**
```json
{
  "Google_Search": 3200.0,
  "Meta_Ads": 2800.0,
  "Amazon_Sponsored_Products": 3000.0,
  "Email_Marketing": 500.0
}
```

- **Response:** `200 OK`
```json
{
  "total_predicted_revenue": 48320.50,
  "channel_breakdown": {
    "Google_Search": 18200.20,
    "Meta_Ads": 12450.30,
    "Amazon_Sponsored_Products": 14200.00,
    "Email_Marketing": 3470.00
  }
}
```

---

#### 5. Detect Inefficiencies and Waste
- **Endpoint:** `GET /api/v1/inefficiencies`
- **Response:** `200 OK` (Array of flagged inefficiency issues)
```json
[
  {
    "campaign_id": "CAMP_MET_01",
    "campaign_name": "Meta_Prospecting_Lookalike",
    "channel": "Meta_Ads",
    "issue_type": "AD_FATIGUE",
    "severity": "WARNING",
    "metric_value": 32.4,
    "benchmark_value": 25.0,
    "waste_estimate": 4350.0,
    "recommendation": "CTR dropped by 32.4% while CPA rose by 26.1%. Ad audience has become saturated. Rotate new creatives or expand audience lookalike brackets."
  }
]
```

---

#### 6. Multi-Touch Attribution Breakdown
- **Endpoint:** `GET /api/v1/attribution`
- **Response:** `200 OK`
```json
[
  {
    "channel": "TikTok_Ads",
    "first_touch_rev": 14500.0,
    "last_touch_rev": 6200.0,
    "linear_rev": 9800.0,
    "time_decay_rev": 8100.0,
    "position_based_rev": 11200.0
  }
]
```

---

## 2. Streamlit User Interface Guide

### Layout Overview
The user interface is structured into a left-side configuration sidebar and a main multi-tab analytical panel:

1. **Sidebar Navigation & Controls:**
   - **Target Objective:** Switch seamlessly between `Maximize Revenue ($)`, `Maximize Total Conversions`, or `Maximize Net Profit ($)`.
   - **Budget Constraint Mode:** Choose to maintain budget parity, scale the budget by a percentage, or key in an exact custom dollar budget.
   - **Max Channel Swing Limit:** Guardrail slider ($\pm 10\%$ to $\pm 100\%$) preventing severe budget shocks.
   - **Dataset Actions:** One-click synthetic data generation button to reset and simulate fresh market conditions.

2. **Executive Overview Panel:**
   - 5 KPI summary cards displaying live budget, projected revenue, ROAS, annualized incremental revenue, and monthly waste.
   - Reallocation Delta bar chart distinguishing positive spend increases (green) from reductions (red).
   - Export-ready allocation matrix with baseline vs. projected metrics.

3. **Response Curve & Knee Analysis Panel:**
   - Interactive Plotly chart rendering fitted Hill saturation curves.
   - Channel hover states showing current operating points and optimized targets.
   - Equimarginal return analysis table displaying saturation ceilings ($V_{\max}$) and half-saturation inflection points ($K$).

4. **Inefficiency Diagnostics Panel:**
   - Interactive bubble matrix plotting Cost-Per-Acquisition ($CPA$) against Return-on-Ad-Spend ($ROAS$), sized by total spend.
   - Categorized cards for `CRITICAL`, `WARNING`, and `INFO` issues with estimated financial waste and recommended corrective actions.

5. **What-If Scenario Simulator:**
   - Channel sliders providing continuous real-time forecasting.
   - Dynamic comparison bars testing hypothetical strategic allocations before ad spend commitment.

