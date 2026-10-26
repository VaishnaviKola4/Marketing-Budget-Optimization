# AI-Driven Marketing Budget Optimizer (MBO)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/Framework-FastAPI%20%7C%20Streamlit-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-16%20passed-success.svg)](tests/)

An enterprise-grade, AI-driven marketing budget optimization platform that analyzes cross-channel advertising campaigns, customer conversion journeys, and revenue metrics. The system identifies inefficient ad spend, estimates non-linear channel saturation curves, pinpoints creative ad fatigue, and computes mathematically optimal budget reallocations to maximize total revenue, conversions, or net profit under real-world operating constraints.

---

## ⚠️ Problem Statement

Modern enterprise and e-commerce marketing teams deploy substantial capital across fragmented advertising platforms—including **Google Search**, **Amazon Sponsored Products**, **Meta Ads**, **TikTok Ads**, **Email Marketing**, and **Affiliate Partnerships**. Despite significant financial exposure, budget allocation decisions are predominantly governed by intuition, heuristic rules of thumb, or misleading **Last-Click attribution models**. 

This operational reality introduces critical inefficiencies:
1. **The Diminishing Returns Trap (Over-Saturation):** Channels scale budget linearly without accounting for saturation. As spend rises, marginal acquisition cost escalates, pushing campaigns past their economic knee where the **Marginal Return on Ad Spend (mROAS)** falls below 1.0 (each additional dollar spent yields less than \$1.00 in revenue).
2. **Invisible Ad Fatigue & Spend Bleeders:** Creative assets naturally fatigue over time, causing Click-Through Rates (CTR) to decay and Cost-Per-Acquisition (CPA) to surge. Without automated multi-window anomaly detection, these fatigued campaigns quietly consume up to 20–35% of daily budgets with negative incremental ROI.
3. **Attribution Blindness:** Last-click attribution falsely attributes 100% of conversion credit to bottom-of-funnel search capture or brand defense, starving top-of-funnel discovery channels of necessary awareness capital and distorting true customer acquisition costs.
4. **Lack of Constrained Mathematical Optimization:** Marketing managers lack algorithmic tooling to answer the core operational question: *"Given a fixed or flexible budget $B$, exactly how many dollars should be shifted between channel $A$ and channel $B$ to maximize portfolio revenue without violating business risk bounds?"*

The **Marketing Budget Optimizer (MBO)** solves this systemic challenge by unifying non-linear response modeling, multi-window waste diagnostics, adstock carryover transformation, and constrained non-linear optimization into a single automated intelligence engine.

---

## Table of Contents
- [⚠️ Problem Statement](#️-problem-statement)
- [1. Project Overview and Purpose](#1-project-overview-and-purpose)
- [2. Repository Structure](#2-repository-structure)
- [3. Algorithm Overview & Mathematical Framework](#3-algorithm-overview--mathematical-framework)
- [4. Installation and Setup Instructions](#4-installation-and-setup-instructions)
- [5. Usage Guide](#5-usage-guide)
- [6. Core Features Explanation](#6-core-features-explanation)
- [7. Data Requirements and Format](#7-data-requirements-and-format)
- [8. Model Architecture](#8-model-architecture)
- [9. In-Depth Documentation Index](#9-in-depth-documentation-index)
- [10. Contribution Guidelines](#10-contribution-guidelines)
- [11. License Information](#11-license-information)

---

## 1. Project Overview and Purpose

The primary objective of the Marketing Budget Optimizer is to transform marketing resource allocation from reactive guesswork into an automated, mathematically rigorous, and auditable discipline.

### Core Objectives
1. **Empirical Response Modeling:** Fit parametric saturation curves to historical spend and revenue to capture non-linear diminishing returns and quantify channel capacity ($V_{\max}$) and sensitivity ($K$).
2. **Automated Anomaly & Waste Diagnosis:** Continuously scan campaigns across trailing time horizons (14-day vs. 45-day baselines) to flag ad fatigue, high-CPA bleeders, and over-saturation with quantified dollar waste estimates.
3. **Constrained Resource Reallocation:** Formulate budget distribution as a non-linear optimization problem solved via **Sequential Least Squares Programming (SLSQP)**, equalizing marginal returns across channels to unlock incremental revenue lift without increasing aggregate expenditure.
4. **Transparent Decision Support:** Deliver an interactive Streamlit UI dashboard and headless FastAPI service enabling marketers and data scientists to execute what-if simulations, inspect saturation curves, and export optimized budget schedules.

---

## 2. Repository Structure

```
Marketing Budget Optimization/
├── README.md                               # Root documentation, problem statement & algorithm overview
├── LICENSE                                 # MIT License
├── requirements.txt                        # Python dependencies
├── setup.py                                # Package installation specification
├── run_app.py                              # Unified CLI launcher (Streamlit UI / FastAPI)
├── data/                                   # Pre-generated benchmark datasets
│   ├── campaign_performance.csv            # 180-day multi-channel campaign records
│   ├── customer_journeys.csv               # 2,500 multi-touch customer conversion paths
│   └── channel_summary.csv                 # Aggregated channel KPIs and baseline ROAS
├── docs/                                   # In-depth technical documentation folder
│   ├── use_cases.md                        # Seasonal products, waste reduction, cash flow, NPL
│   ├── how_to_use.md                       # Step-by-step setup, loading, training, recommendations
│   ├── api_interface_guide.md              # Complete REST API specifications & UI guide
│   └── technical_deep_dive.md              # Mathematical proofs, Hill curves, KKT conditions
├── marketing_budget_optimizer/             # Core Python package
│   ├── config.py                           # System configuration, channels, and thresholds
│   ├── data/
│   │   ├── generator.py                    # Multi-channel synthetic data generator
│   │   ├── loader.py                       # Data loading and schema validation
│   │   └── schemas.py                      # Pydantic v2 schemas and validation contracts
│   ├── models/
│   │   ├── adstock.py                      # Geometric & Weibull carryover decay models
│   │   ├── saturation.py                   # Hill & Exponential saturation curve fitters
│   │   ├── mmm.py                          # Econometric Marketing Mix Model (Ridge MMM)
│   │   └── attribution.py                  # Multi-Touch Attribution (5 standard models)
│   ├── optimizer/
│   │   ├── budget_allocator.py             # Constrained SLSQP non-linear optimizer
│   │   └── inefficiency_detector.py        # Automated ad fatigue & bleeder scanner
│   ├── api/
│   │   └── app.py                          # Production FastAPI REST application
│   ├── ui/
│   │   └── dashboard.py                    # Interactive modern Streamlit dashboard
│   └── utils/
│       ├── metrics.py                      # Financial & marketing KPI formulas
│       └── visualization.py                # Plotly interactive chart builders
└── tests/                                  # Full automated test suite (16 tests passed)
    ├── test_api.py
    ├── test_data_loader.py
    ├── test_inefficiency_detector.py
    ├── test_models.py
    └── test_optimizer.py
```

---

## 3. Algorithm Overview & Mathematical Framework

The optimization pipeline operates through a sequence of algorithmic steps designed to model channel physics, detect anomalies, and compute mathematically optimal budget distributions:

```
[Historical Data] 
       │
       ▼
1. Adstock Carryover Transformation  ──▶  Models lagged consumer memory
       │
       ▼
2. Non-Linear Saturation Fitting    ──▶  Estimates Hill curve: R(x) = Vmax * x^S / (K^S + x^S)
       │
       ▼
3. Marginal ROAS Computation        ──▶  Computes first derivative: dR/dx
       │
       ▼
4. Inefficiency & Anomaly Scanning  ──▶  Detects ad fatigue (CTR drop/CPA spike) & bleeders
       │
       ▼
5. Constrained SLSQP Optimization   ──▶  Equalizes mROAS across channels under budget constraint
       │
       ▼
[Optimal Reallocation & Lift Forecast]
```

### Step 1: Adstock Carryover Transformation
Advertising builds brand awareness that persists beyond the initial day of ad exposure. To capture this lingering memory effect, raw daily spend $X_t$ is transformed using **Geometric Adstock Decay**:

$$A_t = X_t + \theta \cdot A_{t-1}$$

Where $\theta \in [0, 1)$ represents the retention rate (decay parameter). A channel with high awareness memory (such as Influencer or Video branding) exhibits $\theta \approx 0.60$, while direct purchase search ads exhibit $\theta \approx 0.15$.

### Step 2: Diminishing Returns Response Modeling (Hill Function)
To model the non-linear relationship between spend $x$ and generated revenue $R(x)$, the engine fits the **Hill Saturation Function** using non-linear least squares (`scipy.optimize.curve_fit`):

$$R(x) = V_{\max} \cdot \frac{x^S}{K^S + x^S}$$

- **$V_{\max}$ (Revenue Ceiling):** The maximum possible revenue achievable by the channel at infinite spend.
- **$K$ (Half-Saturation Spend):** The dollar spend level required to achieve $50\%$ of $V_{\max}$.
- **$S$ (Curvature Exponent):** Governs the shape of the curve ($S \le 1$ produces concave diminishing returns from $x=0$; $S > 1$ models an initial awareness threshold followed by diminishing returns).

### Step 3: Marginal ROAS ($mROAS$) & Breakeven Analysis
The instantaneous efficiency of each incremental dollar is derived from the first derivative of the Hill function:

$$\text{mROAS}(x) = \frac{dR}{dx} = V_{\max} \cdot S \cdot K^S \cdot \frac{x^{S-1}}{(K^S + x^S)^2}$$

- When $\text{mROAS} > 1.0$: Spending an additional \$1.00 produces more than \$1.00 in revenue.
- When $\text{mROAS} < 1.0$: The channel has crossed the **economic breakeven knee**, where incremental ad dollars destroy capital.

### Step 4: Constrained Non-Linear Budget Optimization (SLSQP)
The budget allocator solves the non-linear optimization problem using **Sequential Least Squares Programming (SLSQP)**:

$$\max_{\mathbf{x}} \quad \Phi(\mathbf{x}) = \sum_{i=1}^M R_i(x_i)$$

Subject to:
1. **Total Budget Equality Constraint:**
   $$\sum_{i=1}^M x_i = B_{\text{target}}$$
2. **Operational Box Constraints (Guardrail Bounds):**
   $$L_i \le x_i \le U_i \quad \forall i \in \{1, \dots, M\}$$
   Where $L_i = x_{i,\text{curr}} \cdot (1 - \delta_{\max})$ and $U_i = x_{i,\text{curr}} \cdot (1 + \delta_{\max})$, with $\delta_{\max}$ representing the user-configured max swing limit (e.g. $\pm 40\%$).

#### The Equimarginal Optimality Principle
Under the Karush-Kuhn-Tucker (KKT) conditions, optimal capital distribution occurs when the **Marginal ROAS is equalized across all unconstrained channels**:

$$\text{mROAS}_1(x_1^*) = \text{mROAS}_2(x_2^*) = \dots = \text{mROAS}_k(x_k^*) = \lambda^*$$

If channel $A$ exhibits higher marginal return than channel $B$, transferring \$1 from $B$ to $A$ strictly increases total portfolio revenue without increasing total budget.

### Step 5: Automated Inefficiency & Ad Fatigue Detection
The scanner compares rolling 14-day performance against prior 30-day baselines to identify:
- **Creative Ad Fatigue:** Flagged when CTR drops $\ge 25\%$ while CPA increases $\ge 20\%$.
- **Over-Saturation:** Flagged when current daily spend operates at $\text{mROAS} < 1.1$.
- **High-CPA Bleeders:** Flagged when campaign CPA exceeds target thresholds while consuming material budget.
- **Quantified Dollar Waste:** Computes exact estimated dollar waste:
  $$\text{Waste} = \Delta \text{CPA} \times \text{Conversions} \times \text{Discount Factor}$$

### Step 6: Multi-Touch Attribution Engine (MTA)
Evaluates customer journey conversion paths across 5 standard models:
- **First-Touch:** $100\%$ credit to the discovery channel.
- **Last-Touch:** $100\%$ credit to the conversion closer.
- **Linear:** Uniform credit distributed equally across all path touchpoints ($w_j = 1/N$).
- **Time-Decay:** Exponential weighting with half-life $\tau = 7\text{ days}$ ($w_j \propto 2^{-(t_N - t_j)/\tau}$).
- **Position-Based (U-Shaped):** $40\%$ to first touch, $40\%$ to last touch, and $20\%$ distributed across intermediary touches.

---

## 4. Installation and Setup Instructions

### Prerequisites
- Python 3.9, 3.10, or 3.11
- Git
- 4 GB RAM minimum

### Step 1: Clone the Repository
```bash
git clone https://github.com/veerenkumar/amazon-marketing-budget-optimizer.git
cd "Marketing Budget Optimization"
```

### Step 2: Create a Virtual Environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

### Step 4: Verify the Installation
Run the automated test suite to ensure all components, models, and endpoints are healthy:
```bash
python -m pytest -v
```

---

## 5. Usage Guide

### 5.1 Running the Interactive Dashboard
Launch the Streamlit web interface with a single command:
```bash
python run_app.py
```
Or alternatively:
```bash
streamlit run marketing_budget_optimizer/ui/dashboard.py
```
Open **`http://localhost:8501`** in your browser.

#### How to Use the UI:
1. **Select Objective:** In the sidebar, choose your optimization target (`Maximize Revenue ($)`, `Maximize Total Conversions`, or `Maximize Net Profit ($)`).
2. **Configure Budget Constraints:** Keep current budget fixed, apply a scaling multiplier (e.g. +15% for holiday scaling), or set an explicit dollar budget.
3. **Set Channel Shift Limits:** Restrict the maximum allowed channel change (e.g., $\pm 40\%$) to maintain operational guardrails.
4. **Analyze Insights:**
   - **Executive Overview:** View total projected revenue lift, portfolio ROAS, and recommended spend deltas.
   - **Saturation Curves:** Inspect where each channel operates along its Hill response curve and identify where diminishing returns begin.
   - **Waste Flags:** Review flagged campaigns with estimated monthly waste and prescriptive AI recommendations.
   - **Multi-Touch Attribution:** Compare First-Touch, Last-Touch, Linear, Time-Decay, and Position-Based models.
   - **What-If Simulator:** Drag interactive channel sliders to test custom budget scenarios with instant revenue and ROAS forecasts.
   - **Export:** Download the recommended allocation plan as a CSV or JSON file.

### 5.2 Running the Headless REST API
For automated CI/CD pipelines, cron jobs, or internal BI integrations, start the FastAPI service:
```bash
python run_app.py --api
```
Or directly:
```bash
uvicorn marketing_budget_optimizer.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation and schema explorer will be accessible at **`http://localhost:8000/docs`**.

### 5.3 Programmatic Python API
```python
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter
from marketing_budget_optimizer.optimizer.budget_allocator import BudgetAllocator
from marketing_budget_optimizer.data.schemas import OptimizationRequest

# Load and fit
df = MarketingDataLoader.load_campaign_data("data/campaign_performance.csv")
fitter = SaturationCurveFitter(curve_type="hill")
fitter.fit_from_dataframe(df)

# Optimize
allocator = BudgetAllocator(curve_fitter=fitter)
current_spends = df.groupby("channel")["spend"].mean().to_dict()

req = OptimizationRequest(objective="maximize_revenue", max_channel_shift_pct=0.35)
summary = allocator.optimize(current_spend_dict=current_spends, request=req)

print(f"Projected Revenue Lift: +${summary.revenue_lift:,.2f} (+{summary.revenue_lift_pct:.2f}%)")
```

---

## 6. Core Features Explanation

| Feature | Description | Key Metric / Output |
| :--- | :--- | :--- |
| **Diminishing Returns Modeling** | Fits non-linear Hill saturation curves ($R = V_{\max} \cdot \frac{x^S}{K^S + x^S}$) to quantify channel capacity. | $V_{\max}$, $K$, Shape ($S$), Knee spend point |
| **Marginal ROAS (mROAS) Tracking** | Computes the instantaneous first derivative $\frac{dR}{dx}$ to identify spend levels where return drops below hurdle rates. | Marginal ROAS per dollar spent |
| **Adstock Carryover Transformation** | Simulates lagged consumer memory using geometric decay ($A_t = X_t + \theta A_{t-1}$) and Weibull distributions. | Decay rates ($\theta \in [0, 1)$), half-life |
| **Constrained Budget Allocator** | Uses Sequential Least Squares Programming (SLSQP) to reallocate budgets under exact equality and box constraints. | Reallocated dollar amounts, spend deltas, revenue lift |
| **Inefficiency & Waste Scanner** | Automatically flags creative ad fatigue (CTR decay + CPA inflation), budget bleeders, and over-saturation. | Severity tags, estimated dollar waste, actionable fixes |
| **Multi-Touch Attribution (MTA)** | Evaluates customer conversion journeys across First-Touch, Last-Touch, Linear, Time-Decay, and U-Shaped models. | Attributed revenue and conversions per channel |
| **What-If Scenario Simulator** | Real-time interactive sliders allowing marketers to simulate custom budget splits and instantly forecast outcomes. | Real-time simulated revenue and ROAS |
| **Exportable Action Plans** | One-click export to CSV and JSON formatted for direct implementation in ad platform managers. | `optimized_marketing_budget.csv` |

---

## 7. Data Requirements and Format

The system ingests two primary data types:

### 1. Daily Campaign Performance Data (`campaign_performance.csv`)
Aggregated or daily level records reporting expenditures, ad exposure, engagement, and conversion revenue.

| Field | Type | Required | Description | Example |
| :--- | :--- | :---: | :--- | :--- |
| `date` | String | Yes | Date in `YYYY-MM-DD` format | `2026-04-12` |
| `campaign_id` | String | Yes | Unique campaign code | `CAMP_GGL_01` |
| `campaign_name`| String | Yes | Human-readable campaign name | `Google_Brand_Exact` |
| `channel` | String | Yes | Marketing channel name | `Google_Search` |
| `spend` | Float | Yes | Total daily spend in dollars | `1250.00` |
| `impressions` | Integer | Yes | Total ad impressions | `32000` |
| `clicks` | Integer | Yes | Total link or ad clicks | `1240` |
| `conversions` | Integer | Yes | Attributed conversions | `65` |
| `revenue` | Float | Yes | Gross revenue generated | `7450.00` |

### 2. Customer Journey Path Data (`customer_journeys.csv`)
Touchpoint paths representing multi-step conversion funnels.

| Field | Type | Description |
| :--- | :--- | :--- |
| `customer_id` | String | Unique identifier for the customer / user profile |
| `timestamp` | String | Touchpoint datetime (`YYYY-MM-DD HH:MM:SS`) |
| `touchpoint_position` | Integer | Sequence order along the conversion journey ($1, 2, 3 \dots$) |
| `channel` | String | Marketing channel where touchpoint occurred |
| `converted` | Boolean | True if this final touchpoint culminated in a purchase |
| `order_value` | Float | Monetary value of the completed order |

---

## 8. Model Architecture

The diagram below depicts the model pipeline:

```mermaid
flowchart LR
    Spend["Daily Channel Spend (x)"] --> Adstock["Adstock Carryover Transformation<br>(Geometric / Weibull Decay)"]
    Adstock --> Hill["Non-Linear Hill Saturation Model<br>R(x) = Vmax * x^S / (K^S + x^S)"]
    Hill --> Slope["Marginal ROAS Computation<br>mROAS = dR / dx"]
    Slope --> SLSQP["Non-Linear Optimizer (SLSQP)<br>Equimarginal Principle (mROAS_1 = mROAS_2)"]
    SLSQP --> Alloc["Optimized Budget Distribution & Lift Forecast"]
```

### Machine Learning & Optimization Frameworks
- **Curve Fitting:** `scipy.optimize.curve_fit` (Trust Region Reflective algorithm with bounded parameter estimation).
- **Mathematical Optimization:** `scipy.optimize.minimize` utilizing the **SLSQP (Sequential Least Squares Programming)** method to solve non-linear objectives with equality and bound constraints.
- **Marketing Mix Modeling:** `scikit-learn` positive-constrained Ridge Regression and ElasticNet with Adstock memory variables.
- **Data Schemas & Validation:** `pydantic` v2 for runtime contract enforcement and error reporting.
- **Web & API Frameworks:** `FastAPI` + `Uvicorn` for headless REST services and `Streamlit` + `Plotly` for interactive generative visual interfaces.

---

## 9. In-Depth Documentation Index

For exhaustive technical guides, refer to the dedicated [`docs/`](docs/) directory:

- 📖 **[docs/use_cases.md](docs/use_cases.md):** In-depth exploration of operational scenarios: seasonal spike management, waste reduction, cash flow optimization, cold-start product launches, and cross-channel synergy.
- 🛠️ **[docs/how_to_use.md](docs/how_to_use.md):** Step-by-step installation, dataset preprocessing, UI walkthrough, and programmatic usage examples.
- 🔌 **[docs/api_interface_guide.md](docs/api_interface_guide.md):** Full REST API specification with endpoint contracts, sample JSON payloads, curl commands, and UI interface specifications.
- 🔬 **[docs/technical_deep_dive.md](docs/technical_deep_dive.md):** Mathematical formulas (Hill equation, adstock lag, SLSQP Lagrangian optimality, Karush-Kuhn-Tucker conditions), algorithmic complexity, and Mermaid architecture diagrams.

---

## 10. Contribution Guidelines

We welcome contributions from the community! To contribute:

1. **Fork the Repository:** Create your own feature branch (`git checkout -b feature/amazing-feature`).
2. **Follow Code Quality Standards:**
   - Adhere to **PEP 8** coding standards.
   - Use type annotations (`typing`, `Pydantic`) for all function signatures and public APIs.
   - Maintain docstrings for modules and public classes.
3. **Write Unit Tests:** Add test cases in the `tests/` directory for any new models, optimization routines, or API endpoints.
4. **Execute Test Suite:** Ensure all tests pass cleanly before submitting:
   ```bash
   python -m pytest -v
   ```
5. **Submit a Pull Request:** Open a descriptive PR describing your changes, test results, and any relevant issue references.

---

## 11. License Information

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details. You are free to use, modify, distribute, and commercialize this software with proper attribution.
