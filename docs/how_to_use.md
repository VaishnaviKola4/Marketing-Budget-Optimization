# How to Use: Marketing Budget Optimizer

A step-by-step practical guide to configuring, operating, and integrating the Marketing Budget Optimizer across your marketing tech stack.

---

## 1. System Requirements & Environment Setup

### Prerequisites
- Python 3.9+ (Python 3.10 or 3.11 recommended)
- 4 GB RAM minimum
- Modern web browser (Chrome, Edge, Firefox, Safari)

### Installation
Clone or download the repository into your desired workspace:

```bash
cd "Marketing Budget Optimization"
```

Create and activate an isolated virtual environment:

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install package dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Verify the installation by running the test suite:

```bash
python -m pytest -v
```

---

## 2. Generating & Preparing Your Data

### Using Pre-Generated Datasets
The project comes with a high-fidelity synthetic data generator that creates realistic campaign logs and customer touchpoints.

To generate fresh data:
```bash
python -m marketing_budget_optimizer.data.generator
```
This generates three primary CSV files in the `data/` directory:
- `data/campaign_performance.csv`: 180 days of daily campaign spend, impressions, clicks, conversions, and revenue.
- `data/customer_journeys.csv`: 2,500 multi-touch customer conversion paths.
- `data/channel_summary.csv`: Aggregated channel metrics and baseline ROAS.

### Using Custom Enterprise Data
To ingest your brand's historical advertising data, prepare a CSV file conforming to the following schema:

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `date` | String | `2026-03-15` | Date in `YYYY-MM-DD` format |
| `campaign_id` | String | `CAMP_GGL_01` | Unique campaign identifier |
| `campaign_name`| String | `Google_Brand_Exact`| Human-readable campaign name |
| `channel` | String | `Google_Search` | High-level channel identifier |
| `spend` | Float | `1450.50` | Daily spend in dollars |
| `impressions` | Integer | `45000` | Ad impressions served |
| `clicks` | Integer | `1850` | Total ad clicks |
| `conversions` | Integer | `92` | Conversions attributed |
| `revenue` | Float | `9850.00` | Revenue attributed |

Place your custom CSV in `data/campaign_performance.csv` or load it programmatically via `MarketingDataLoader.load_campaign_data(path)`.

---

## 3. Running the Interactive Streamlit UI

The system includes a modern, high-performance web dashboard.

### Launching the Dashboard
Execute:
```bash
python run_app.py
```
Or directly via Streamlit:
```bash
streamlit run marketing_budget_optimizer/ui/dashboard.py
```
Open your browser to: **`http://localhost:8501`**

### Navigating Dashboard Tabs
1. **Executive Overview:**
   - Review high-level KPI cards (Total daily budget, projected daily revenue, portfolio ROAS, annualized revenue lift, and identified monthly waste).
   - Inspect the **Reallocation Delta Bar Chart** to see recommended dollar shifts per channel.
   - Read the detailed reallocation table showing current vs. recommended spend, projected revenue, and marginal ROAS.
2. **Saturation Curves & mROAS:**
   - Examine non-linear **Hill Saturation Curves** for each channel.
   - Identify the "knee" of the curve where diminishing returns begin.
   - Compare current operating spend points against recommended points.
3. **Waste & Inefficiency Flags:**
   - Review automated flags for creative ad fatigue, high-CPA bleeders, and over-saturated spend.
   - Read AI-generated prescriptive recommendations and estimated dollar savings.
4. **Multi-Touch Attribution:**
   - Compare revenue and conversion credit distributions across First-Touch, Last-Touch, Linear, Time-Decay, and Position-Based models.
5. **What-If Scenario Simulator:**
   - Interactively adjust channel sliders to test custom hypothetical budget distributions.
   - Forecast real-time revenue and ROAS before executing changes in live ad platforms.
6. **Data Explorer & Export:**
   - Filter and inspect raw records.
   - Export optimized budget plans in CSV or JSON format for easy import into Google Ads, Amazon Advertising Console, or Meta Ads Manager.

---

## 4. Running the Headless REST API

For enterprise automated pipelines, the system can run as a high-throughput FastAPI service:

```bash
python run_app.py --api
```
Or directly via uvicorn:
```bash
uvicorn marketing_budget_optimizer.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation is available at: **`http://localhost:8000/docs`**

---

## 5. Programmatic Python API

You can import and integrate the optimizer directly into internal Python scripts, notebooks, or automated Airflow / Dagster pipelines:

```python
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter
from marketing_budget_optimizer.optimizer.budget_allocator import BudgetAllocator
from marketing_budget_optimizer.data.schemas import OptimizationRequest

# 1. Load campaign data
df = MarketingDataLoader.load_campaign_data("data/campaign_performance.csv")

# 2. Fit non-linear saturation curves
curve_fitter = SaturationCurveFitter(curve_type="hill")
curve_fitter.fit_from_dataframe(df)

# 3. Initialize optimizer
allocator = BudgetAllocator(curve_fitter=curve_fitter)

# 4. Define current spend baseline
current_spends = df.groupby("channel")["spend"].mean().to_dict()

# 5. Execute optimization (e.g. scale budget by +15% with max 30% channel shift)
request = OptimizationRequest(
    budget_scaling_factor=1.15,
    objective="maximize_revenue",
    max_channel_shift_pct=0.30
)
summary = allocator.optimize(current_spend_dict=current_spends, request=request)

# 6. Print results
print(f"Total Recommended Daily Budget: ${summary.total_recommended_spend:,.2f}")
print(f"Projected Daily Revenue: ${summary.total_predicted_recommended_revenue:,.2f}")
print(f"Projected Revenue Lift: +${summary.revenue_lift:,.2f} (+{summary.revenue_lift_pct:.2f}%)")

for alloc in summary.channel_allocations:
    print(f" - {alloc.channel}: ${alloc.current_spend:,.0f} -> ${alloc.recommended_spend:,.0f} (mROAS: {alloc.projected_marginal_roas:.2f}x)")
```

