# 🔋 Battery Degradation Simulator

An interactive simulator that models Li-ion battery capacity fade and internal resistance growth over repeated charge/discharge cycles, based on an empirical Arrhenius-style aging model.

**Live demo:** _(https://battery-degradation-simulator-ibeflsyjnxfekvuukb94tz.streamlit.app/)_

## What it does

- Simulates **capacity fade** and **State of Health (SoH)** decline across charge cycles
- Simulates **internal resistance growth** as the cell ages
- Accounts for key real-world stress factors:
  - Depth of Discharge (DoD)
  - C-rate (charge/discharge speed)
  - Operating temperature
  - Calendar time (time-based aging, independent of cycling)
- Estimates the cycle at which the battery crosses the **80% SoH end-of-life threshold**
- Interactive charts (Plotly) + downloadable CSV of simulation data

## Model

Uses a simplified two-part aging model common in Li-ion aging literature:

- **Cycle aging** — capacity fade driven by number of cycles, depth of discharge, and C-rate, with Arrhenius-style temperature acceleration
- **Calendar aging** — time-based fade that occurs even when the cell isn't being cycled, also temperature-accelerated
- **Resistance growth** — increases with both cycle count and elapsed time

This is an **educational approximation**, not a lab-validated electrochemical model — useful for visualizing aging *trends and sensitivities*, not precise lab-grade predictions.

## Tech stack

- Python
- Streamlit (UI + interactivity)
- NumPy / Pandas (simulation logic)
- Plotly (interactive charts)

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Deployed for free via [Streamlit Community Cloud](https://share.streamlit.io) — connect this GitHub repo and point it at `app.py`.

---


