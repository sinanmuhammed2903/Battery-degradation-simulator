"""
Battery Degradation Simulator
------------------------------
Simulates Li-ion battery capacity fade and internal resistance growth
over repeated charge/discharge cycles, using a parametric aging model.

Built by Sinan — ECE student, College of Engineering Thalassery
Project 4 of summer build series.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Battery Degradation Simulator",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ────────────────────────────────────────────────────────────────
# CUSTOM STYLING
# ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #111827;
        border: 1px solid #1f2d42;
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🔋 Battery Degradation Simulator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Simulate Li-ion capacity fade & internal resistance growth across charge cycles</p>', unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────
# DEGRADATION MODEL
# ────────────────────────────────────────────────────────────────
def simulate_battery_degradation(
    initial_capacity_mah,
    initial_resistance_mohm,
    num_cycles,
    dod_percent,
    avg_temp_c,
    c_rate,
    calendar_days
):
    """
    Simulates capacity fade and resistance growth using a combined
    cycle-aging + calendar-aging empirical model.

    Capacity fade model (simplified, based on common Li-ion aging literature):
        Q_loss_cycle = k_cyc * N * (DoD)^0.5 * exp(Ea_cyc * (1/Tref - 1/T)) * C_rate_factor
        Q_loss_calendar = k_cal * sqrt(t_days) * exp(Ea_cal * (1/Tref - 1/T))

    Resistance growth model:
        R_growth = R0 * (1 + alpha * N^0.5 + beta * t_days)

    These are simplified Arrhenius-style empirical approximations —
    not a full electrochemical model — intended for educational
    visualization of aging *trends*, not lab-grade precision.
    """
    cycles = np.arange(0, num_cycles + 1)

    # Reference temperature (25°C) in Kelvin
    T_ref = 298.15
    T = avg_temp_c + 273.15

    # Empirical aging coefficients (tunable, based on typical NMC/LFP cell behavior)
    k_cyc = 0.00008      # cycle aging base rate
    k_cal = 0.00015      # calendar aging base rate
    Ea_cyc = 4000        # activation energy term (cycle aging), simplified units
    Ea_cal = 5000         # activation energy term (calendar aging)

    # Temperature acceleration factor (higher temp = faster aging)
    temp_factor_cyc = np.exp(Ea_cyc * (1 / T_ref - 1 / T))
    temp_factor_cal = np.exp(Ea_cal * (1 / T_ref - 1 / T))

    # C-rate stress factor — higher charge/discharge rates accelerate fade
    c_rate_factor = 1 + 0.15 * (c_rate - 0.5)
    c_rate_factor = max(c_rate_factor, 0.5)

    # Depth of Discharge factor — deeper discharge cycles age the cell faster
    dod_factor = (dod_percent / 100) ** 0.5

    # ── Cycle-based capacity fade ──
    cycle_fade_pct = k_cyc * cycles * dod_factor * temp_factor_cyc * c_rate_factor * 100

    # ── Calendar-based capacity fade (time elapses alongside cycling) ──
    days_per_cycle = calendar_days / max(num_cycles, 1)
    elapsed_days = cycles * days_per_cycle
    calendar_fade_pct = k_cal * np.sqrt(elapsed_days) * temp_factor_cal * 100

    # Combined fade (capped at 100%)
    total_fade_pct = np.clip(cycle_fade_pct + calendar_fade_pct, 0, 100)
    capacity_mah = initial_capacity_mah * (1 - total_fade_pct / 100)

    # ── Internal resistance growth ──
    alpha = 0.012  # cycle-driven resistance growth coefficient
    beta = 0.0008  # calendar-driven resistance growth coefficient
    resistance_mohm = initial_resistance_mohm * (
        1 + alpha * np.sqrt(cycles) * temp_factor_cyc + beta * elapsed_days * temp_factor_cal
    )

    # State of Health (SoH) — capacity relative to original
    soh_pct = (capacity_mah / initial_capacity_mah) * 100

    # Estimate cycle at which SoH crosses 80% (common EOL threshold)
    eol_idx = np.argmax(soh_pct <= 80) if np.any(soh_pct <= 80) else None
    eol_cycle = cycles[eol_idx] if eol_idx else None

    return pd.DataFrame({
        "cycle": cycles,
        "elapsed_days": elapsed_days,
        "capacity_mah": capacity_mah,
        "soh_pct": soh_pct,
        "resistance_mohm": resistance_mohm,
        "fade_pct": total_fade_pct
    }), eol_cycle


# ────────────────────────────────────────────────────────────────
# SIDEBAR — INPUT CONTROLS
# ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Battery Parameters")

    st.subheader("Cell Specifications")
    initial_capacity = st.number_input(
        "Initial Capacity (mAh)", min_value=100, max_value=10000, value=3000, step=50,
        help="Rated capacity of the fresh cell, e.g. 3000mAh for an 18650 Li-ion cell"
    )
    initial_resistance = st.number_input(
        "Initial Internal Resistance (mΩ)", min_value=5, max_value=500, value=45, step=5,
        help="Typical fresh Li-ion 18650 cells: 30-60 mΩ"
    )

    st.subheader("Usage Conditions")
    num_cycles = st.slider(
        "Number of Charge Cycles to Simulate", min_value=10, max_value=2000, value=500, step=10
    )
    dod_percent = st.slider(
        "Depth of Discharge (%)", min_value=10, max_value=100, value=80, step=5,
        help="How much of the battery's capacity is used each cycle. Shallower discharge = slower aging."
    )
    c_rate = st.slider(
        "Average C-Rate", min_value=0.1, max_value=3.0, value=0.5, step=0.1,
        help="Charge/discharge rate relative to capacity. 1C = full discharge in 1 hour."
    )
    avg_temp = st.slider(
        "Average Operating Temperature (°C)", min_value=0, max_value=60, value=25, step=1,
        help="Higher temperatures significantly accelerate both cycle and calendar aging."
    )
    calendar_days = st.slider(
        "Total Calendar Time (days)", min_value=30, max_value=3650, value=365, step=30,
        help="Real-world time elapsed while these cycles occur — affects calendar aging."
    )

    st.divider()
    st.caption("📘 Model is an educational empirical approximation (Arrhenius-style cycle + calendar aging), not a lab-validated electrochemical model.")


# ────────────────────────────────────────────────────────────────
# RUN SIMULATION
# ────────────────────────────────────────────────────────────────
df, eol_cycle = simulate_battery_degradation(
    initial_capacity, initial_resistance, num_cycles,
    dod_percent, avg_temp, c_rate, calendar_days
)

final_soh = df["soh_pct"].iloc[-1]
final_capacity = df["capacity_mah"].iloc[-1]
final_resistance = df["resistance_mohm"].iloc[-1]
resistance_growth_pct = ((final_resistance / initial_resistance) - 1) * 100

# ────────────────────────────────────────────────────────────────
# TOP METRICS
# ────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Final SoH", f"{final_soh:.1f}%", delta=f"{final_soh - 100:.1f}%")
with col2:
    st.metric("Final Capacity", f"{final_capacity:.0f} mAh", delta=f"{final_capacity - initial_capacity:.0f} mAh")
with col3:
    st.metric("Final Resistance", f"{final_resistance:.1f} mΩ", delta=f"+{resistance_growth_pct:.1f}%")
with col4:
    if eol_cycle:
        st.metric("Est. EOL Cycle (80% SoH)", f"{int(eol_cycle)}")
    else:
        st.metric("Est. EOL Cycle (80% SoH)", "Not reached")

st.divider()

# ────────────────────────────────────────────────────────────────
# CHARTS
# ────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📉 Capacity Fade & SoH", "⚡ Internal Resistance", "📊 Raw Data"])

with tab1:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df["cycle"], y=df["soh_pct"], name="State of Health (%)",
        line=dict(color="#00d4ff", width=2.5)
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["cycle"], y=df["capacity_mah"], name="Capacity (mAh)",
        line=dict(color="#7c3aed", width=2.5, dash="dot")
    ), secondary_y=True)

    fig.add_hline(y=80, line_dash="dash", line_color="#fca5a5",
                  annotation_text="80% SoH (typical EOL threshold)",
                  annotation_position="bottom right", secondary_y=False)

    fig.update_layout(
        template="plotly_dark",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="#0a0e17",
        paper_bgcolor="#0a0e17",
    )
    fig.update_xaxes(title_text="Charge Cycle Number")
    fig.update_yaxes(title_text="State of Health (%)", secondary_y=False)
    fig.update_yaxes(title_text="Capacity (mAh)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"💡 At your configured usage pattern ({dod_percent}% DoD, {c_rate}C, {avg_temp}°C), "
        f"the cell degrades to **{final_soh:.1f}% SoH** after **{num_cycles} cycles** "
        f"over **{calendar_days} days**."
    )

with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df["cycle"], y=df["resistance_mohm"], name="Internal Resistance (mΩ)",
        line=dict(color="#f59e0b", width=2.5), fill="tozeroy", fillcolor="rgba(245,158,11,0.08)"
    ))
    fig2.update_layout(
        template="plotly_dark",
        height=440,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="#0a0e17",
        paper_bgcolor="#0a0e17",
        xaxis_title="Charge Cycle Number",
        yaxis_title="Internal Resistance (mΩ)"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.info(
        f"💡 Internal resistance increased by **{resistance_growth_pct:.1f}%** "
        f"({initial_resistance}mΩ → {final_resistance:.1f}mΩ). Rising resistance "
        f"reduces available power and increases heat generation under load."
    )

with tab3:
    st.dataframe(
        df.style.format({
            "elapsed_days": "{:.0f}",
            "capacity_mah": "{:.1f}",
            "soh_pct": "{:.2f}",
            "resistance_mohm": "{:.2f}",
            "fade_pct": "{:.2f}"
        }),
        use_container_width=True,
        height=400
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download simulation data (CSV)",
        data=csv,
        file_name="battery_degradation_simulation.csv",
        mime="text/csv"
    )

# ────────────────────────────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built with Streamlit · Empirical Arrhenius-style aging model · "
    "Part of a TinyML / embedded systems summer build series."
)
