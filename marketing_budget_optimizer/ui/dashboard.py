"""
Interactive AI Marketing Budget Optimizer Dashboard.
Built with Streamlit and Plotly for real-time spend reallocation,
saturation curve inspection, inefficiency diagnostics, and what-if simulation.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

from marketing_budget_optimizer.config import DATA_DIR
from marketing_budget_optimizer.data.generator import MarketingDataGenerator
from marketing_budget_optimizer.data.loader import MarketingDataLoader
from marketing_budget_optimizer.data.schemas import OptimizationRequest, ChannelConstraint
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter
from marketing_budget_optimizer.models.attribution import MultiTouchAttributor
from marketing_budget_optimizer.optimizer.budget_allocator import BudgetAllocator
from marketing_budget_optimizer.optimizer.inefficiency_detector import InefficiencyDetector
from marketing_budget_optimizer.utils.visualization import VisualizationFactory
from marketing_budget_optimizer.utils.metrics import compute_portfolio_metrics


# Page Configuration
st.set_page_config(
    page_title="AI Marketing Budget Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #10B981;
        font-weight: 600;
        margin-top: 2px;
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-info {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_or_generate_datasets():
    """Caches dataset loading and generates on first run if missing."""
    camp_file = DATA_DIR / "campaign_performance.csv"
    journ_file = DATA_DIR / "customer_journeys.csv"
    if not camp_file.exists() or not journ_file.exists():
        gen = MarketingDataGenerator(random_seed=42)
        gen.generate_all_and_save(DATA_DIR)
    
    df_camp = MarketingDataLoader.load_campaign_data(camp_file)
    df_journ = MarketingDataLoader.load_customer_journeys(journ_file)
    return df_camp, df_journ


df_campaigns, df_journeys = load_or_generate_datasets()

# Initialize models
curve_fitter = SaturationCurveFitter(curve_type="hill")
curve_fitter.fit_from_dataframe(df_campaigns)
allocator = BudgetAllocator(curve_fitter=curve_fitter)
detector = InefficiencyDetector()

# Header
st.markdown('<div class="main-header">Marketing Budget Optimizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Marketing Mix Modeling, Diminishing Returns Optimization & Inefficient Spend Diagnostics</div>', unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.title("Optimization Settings")
st.sidebar.markdown("Configure constraints and optimization objectives.")

objective = st.sidebar.selectbox(
    "Target Objective",
    options=["maximize_revenue", "maximize_conversions", "maximize_profit"],
    format_func=lambda x: {
        "maximize_revenue": "Maximize Revenue ($)",
        "maximize_conversions": "Maximize Total Conversions",
        "maximize_profit": "Maximize Net Profit ($)"
    }[x]
)

budget_mode = st.sidebar.radio(
    "Budget Constraint Mode",
    ["Keep Total Budget Fixed", "Scale Budget (+/- %)", "Set Custom Total Budget ($)"]
)

# Baseline current daily average spend by channel
current_spends = df_campaigns.groupby("channel")["spend"].mean().to_dict()
total_current_daily_spend = sum(current_spends.values())

custom_budget = None
budget_scale = 1.0

if budget_mode == "Scale Budget (+/- %)":
    pct_scale = st.sidebar.slider("Adjust Budget by %", min_value=-50, max_value=100, value=0, step=5)
    budget_scale = 1.0 + (pct_scale / 100.0)
elif budget_mode == "Set Custom Total Budget ($)":
    custom_budget = st.sidebar.number_input(
        "Total Daily Budget ($)",
        min_value=1000.0,
        max_value=200000.0,
        value=float(round(total_current_daily_spend, 0)),
        step=500.0
    )

max_shift_pct = st.sidebar.slider(
    "Max Channel Swing (+/- %)",
    min_value=10,
    max_value=100,
    value=40,
    step=5,
    help="Limits how much budget can shift up or down from historical baseline for risk control."
) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("Dataset Actions")
if st.sidebar.button("Regenerate Synthetic Data"):
    with st.spinner("Generating fresh realistic market data..."):
        gen = MarketingDataGenerator(random_seed=np.random.randint(1, 1000))
        gen.generate_all_and_save(DATA_DIR)
        st.cache_data.clear()
        st.success("New data generated successfully! Reloading...")
        st.rerun()

# Run Optimization
req = OptimizationRequest(
    total_budget=custom_budget,
    budget_scaling_factor=budget_scale,
    objective=objective,
    max_channel_shift_pct=max_shift_pct
)
summary = allocator.optimize(current_spend_dict=current_spends, request=req)

# Dashboard Tabs
tab_exec, tab_curves, tab_waste, tab_attribution, tab_simulator, tab_data = st.tabs([
    "Executive Overview",
    "Saturation Curves & mROAS",
    "Waste & Inefficiency Flags",
    "Multi-Touch Attribution",
    "What-If Simulator",
    "Data Explorer & Export"
])

# ----------------- TAB 1: EXECUTIVE OVERVIEW -----------------
with tab_exec:
    st.markdown("### Portfolio Optimization Results")
    st.markdown(f"Optimal allocation calculated using **Sequential Least Squares Programming (SLSQP)** under `{objective}`.")

    # Top KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Daily Budget</div>
            <div class="metric-val">${summary.total_recommended_spend:,.0f}</div>
            <div class="metric-sub">Current: ${summary.total_current_spend:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Projected Daily Revenue</div>
            <div class="metric-val">${summary.total_predicted_recommended_revenue:,.0f}</div>
            <div class="metric-sub" style="color:#10B981;">+{summary.revenue_lift_pct:.1f}% (+${summary.revenue_lift:,.0f})</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Portfolio ROAS</div>
            <div class="metric-val">{summary.overall_projected_roas:.2f}x</div>
            <div class="metric-sub">Baseline: {summary.overall_current_roas:.2f}x</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        annual_lift = summary.revenue_lift * 365.0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Annualized Revenue Lift</div>
            <div class="metric-val">${annual_lift:,.0f}</div>
            <div class="metric-sub">Zero Extra Ad Spend</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        ineff_flags = detector.scan_campaigns(df_campaigns, curve_fitter)
        total_waste = sum(f.waste_estimate for f in ineff_flags)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Monthly Waste Identified</div>
            <div class="metric-val" style="color:#EF4444;">${total_waste:,.0f}</div>
            <div class="metric-sub" style="color:#EF4444;">{len(ineff_flags)} Flagged Items</div>
        </div>
        """, unsafe_allow_html=True)

    # Visualizations row
    col_chart1, col_chart2 = st.columns([1, 1])
    with col_chart1:
        st.plotly_chart(VisualizationFactory.plot_reallocation_deltas(summary), use_container_width=True)
    with col_chart2:
        # Comparison Bar Chart: Spend vs Revenue
        comp_df = pd.DataFrame([
            {"Metric": "Daily Spend ($)", "Current": summary.total_current_spend, "AI Recommended": summary.total_recommended_spend},
            {"Metric": "Daily Revenue ($)", "Current": summary.total_predicted_current_revenue, "AI Recommended": summary.total_predicted_recommended_revenue}
        ])
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=comp_df["Metric"], y=comp_df["Current"], name="Current Baseline", marker_color="#94A3B8"))
        fig_comp.add_trace(go.Bar(x=comp_df["Metric"], y=comp_df["AI Recommended"], name="AI Recommended", marker_color="#4F46E5"))
        fig_comp.update_layout(
            barmode="group",
            title="<b>Current vs AI-Optimized Performance Baseline</b>",
            template="plotly_white",
            height=420,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # Detailed Channel Reallocation Table
    st.markdown("#### Recommended Spend Reallocation by Channel")
    table_rows = []
    for r in summary.channel_allocations:
        table_rows.append({
            "Channel": r.channel,
            "Current Spend ($)": f"${r.current_spend:,.2f}",
            "Recommended Spend ($)": f"${r.recommended_spend:,.2f}",
            "Shift ($)": f"{'+' if r.spend_delta >= 0 else ''}${r.spend_delta:,.2f}",
            "Shift (%)": f"{'+' if r.spend_delta_pct >= 0 else ''}{r.spend_delta_pct:.1f}%",
            "Projected Daily Rev ($)": f"${r.predicted_recommended_revenue:,.2f}",
            "Rev Lift ($)": f"{'+' if r.revenue_delta >= 0 else ''}${r.revenue_delta:,.2f}",
            "Baseline ROAS": f"{r.current_roas:.2f}x",
            "Projected ROAS": f"{r.projected_roas:.2f}x",
            "Marginal ROAS (mROAS)": f"{r.projected_marginal_roas:.2f}x"
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


# ----------------- TAB 2: SATURATION CURVES -----------------
with tab_curves:
    st.markdown("### Diminishing Returns & Response Modeling")
    st.markdown(
        "Response curves follow the **Hill Saturation Function**: "
        r"$R(x) = V_{\max} \cdot \frac{x^S}{K^S + x^S}$. "
        "The **open circles** depict current operating spend, while the **stars** mark the AI-recommended reallocation point."
    )
    
    st.plotly_chart(VisualizationFactory.plot_saturation_curves(curve_fitter, summary=summary), use_container_width=True)

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        st.markdown("#### Fitted Hill Curve Parameters")
        params_list = []
        for ch, p in curve_fitter.channel_models.items():
            sat_point = curve_fitter.find_saturation_point(ch, target_mroas=1.1)
            params_list.append({
                "Channel": ch,
                "Vmax (Max Revenue Ceiling $)": f"${p['vmax']:,.0f}",
                "K (Half Saturation Spend $)": f"${p['k']:,.0f}",
                "Shape Exponent (S)": f"{p['s']:.2f}",
                "Diminishing Knee Spend ($/day)": f"${sat_point:,.0f}"
            })
        st.dataframe(pd.DataFrame(params_list), use_container_width=True, hide_index=True)

    with col_s2:
        st.markdown("#### Saturation Diagnostic Analysis")
        st.info(
            "**Key Mathematical Insight:** Optimal budget allocation across multiple non-linear channels occurs "
            "when the **Marginal Return on Ad Spend (mROAS)** is equalized across all unconstrained channels (Equimarginal Principle). "
            "Channels operating past their knee point (where mROAS < 1.0) burn cash with negative incremental ROI."
        )


# ----------------- TAB 3: WASTE & INEFFICIENCY FLAGS -----------------
with tab_waste:
    st.markdown("### Automated Spend Waste & Inefficiency Diagnostics")
    st.markdown("Identifies campaigns suffering from creative ad fatigue, high CPA bleed, and over-saturation.")

    st.plotly_chart(VisualizationFactory.plot_cpa_roas_bubble(df_campaigns), use_container_width=True)

    flags = detector.scan_campaigns(df_campaigns, curve_fitter)

    if flags:
        st.markdown(f"**Identified {len(flags)} Inefficiencies & Optimization Opportunities:**")
        for f in flags:
            badge_class = f"badge-{f.severity.lower()}"
            with st.expander(f"[{f.severity}] {f.channel} - {f.campaign_name} | Potential Savings: ${f.waste_estimate:,.2f}"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Issue:** `{f.issue_type}`")
                c2.markdown(f"**Metric Observed:** `{f.metric_value}` (Hurdle: `{f.benchmark_value}`)")
                c3.markdown(f"**Estimated Waste:** `${f.waste_estimate:,.2f}`")
                st.markdown(f"💡 **AI Recommendation:** {f.recommendation}")
    else:
        st.success("No critical inefficiencies detected! All campaigns are operating within acceptable thresholds.")


# ----------------- TAB 4: MULTI-TOUCH ATTRIBUTION -----------------
with tab_attribution:
    st.markdown("### Multi-Touch Attribution (MTA) Analysis")
    st.markdown(
        "Compare how credit is distributed across customer journey touchpoints. "
        "First-Touch highlights top-of-funnel discovery channels; Last-Touch favors closers."
    )
    
    attributor = MultiTouchAttributor()
    attrib_df = attributor.compute_all_attributions(df_journeys)

    st.plotly_chart(VisualizationFactory.plot_attribution_comparison(attrib_df), use_container_width=True)

    st.markdown("#### Channel Attribution Summary Table")
    st.dataframe(attrib_df, use_container_width=True, hide_index=True)


# ----------------- TAB 5: WHAT-IF SIMULATOR -----------------
with tab_simulator:
    st.markdown("### Interactive What-If Scenario Simulator")
    st.markdown("Adjust individual channel spend sliders below to forecast expected daily revenue and ROAS in real time.")

    col_sim_controls, col_sim_results = st.columns([1, 1])

    sim_spends = {}
    with col_sim_controls:
        st.markdown("#### Adjust Daily Channel Spend ($)")
        for r in summary.channel_allocations:
            default_val = float(r.recommended_spend)
            min_val = max(10.0, default_val * 0.2)
            max_val = default_val * 3.0
            sim_spends[r.channel] = st.slider(
                f"{r.channel}",
                min_value=float(round(min_val, 0)),
                max_value=float(round(max_val, 0)),
                value=float(round(default_val, 0)),
                step=50.0,
                key=f"sim_{r.channel}"
            )

    with col_sim_results:
        st.markdown("#### Simulated Scenario Forecast")
        sim_total_spend = sum(sim_spends.values())
        sim_total_rev = sum(curve_fitter.predict(ch, s) for ch, s in sim_spends.items())
        sim_roas = sim_total_rev / max(sim_total_spend, 1.0)

        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("Simulated Spend", f"${sim_total_spend:,.0f}", delta=f"${sim_total_spend - summary.total_current_spend:,.0f}")
        s_col2.metric("Simulated Revenue", f"${sim_total_rev:,.0f}", delta=f"${sim_total_rev - summary.total_predicted_current_revenue:,.0f}")
        s_col3.metric("Simulated ROAS", f"{sim_roas:.2f}x", delta=f"{sim_roas - summary.overall_current_roas:.2f}x")

        # Breakdown chart
        sim_df = pd.DataFrame([
            {"Channel": ch, "Spend": s, "Revenue": curve_fitter.predict(ch, s)}
            for ch, s in sim_spends.items()
        ])
        fig_sim = px.bar(
            sim_df,
            x="Channel",
            y=["Spend", "Revenue"],
            barmode="group",
            title="<b>Simulated Spend vs Forecasted Revenue by Channel</b>",
            template="plotly_white"
        )
        st.plotly_chart(fig_sim, use_container_width=True)


# ----------------- TAB 6: DATA EXPLORER & EXPORT -----------------
with tab_data:
    st.markdown("### Data Explorer & Export")
    
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        st.markdown("#### Historical Campaign Records")
        channel_filter = st.selectbox("Filter Channel", options=["All"] + list(current_spends.keys()))
        if channel_filter != "All":
            filtered_df = df_campaigns[df_campaigns["channel"] == channel_filter]
        else:
            filtered_df = df_campaigns
        st.dataframe(filtered_df.head(100), use_container_width=True)

    with col_d2:
        st.markdown("#### Export Optimized Allocation Schedule")
        export_df = pd.DataFrame([res.dict() for res in summary.channel_allocations])
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Allocation Plan (CSV)",
            data=csv_data,
            file_name="optimized_marketing_budget.csv",
            mime="text/csv"
        )

        json_data = summary.json(indent=2)
        st.download_button(
            label="Download Optimization Summary (JSON)",
            data=json_data,
            file_name="optimization_summary.json",
            mime="application/json"
        )

        st.markdown("#### Summary JSON Preview")
        st.code(json_data[:1000] + "\n...", language="json")

