# Monsoon-to-Margin
### Live Quick-Commerce Demand & Disruption Dashboard

## 🚀 Live Dashboard

**[Open the Monsoon-to-Margin live Streamlit dashboard ↗](https://harsha-monsoon-margin.streamlit.app)**

Try the interactive dashboard directly in your browser. The GitHub repository contains the complete source code, while the Streamlit deployment is the live, interactive version for portfolio reviewers and hiring managers.

> **How to use this document:** This is a complete build brief, not a short prompt.
> Paste this entire file into ChatGPT as your first message and ask it to build
> the project exactly as specified, file by file, in the order given in Section 11.
> This document also defines exactly what the project's own `README.md` must
> contain once built (Section 14).

## 1. Business Problem
Quick-commerce platforms (Blinkit, Zepto, Swiggy Instamart) promise 10–20 minute
deliveries. Monsoon rainfall breaks that promise in two ways at once:
- **Demand spikes** — people avoid stepping out, so order volume rises.
- **Supply capacity drops** — riders slow down, roads flood, delivery time and
  cancellations rise.

Ops and category teams need to see this collision coming by city, so they can
pre-position riders, adjust SLA promises, and budget for rider surge pay
*before* a rain event, not after customer complaints.

**Business questions this project answers:**
- Which cities/days saw the sharpest demand-vs-capacity mismatch?
- How much does heavier rainfall cost us in delivery delay, cancellations, and
  rider incentive spend?
- What's the estimated margin hit on a "heavy rain" day vs. a dry day?

## 2. Business Impact (why this matters on a resume)
Frames data work as a decision-support tool for operations, not just a chart.
Demonstrates external API integration, resilience engineering (graceful
degradation when the API is unreachable), a quantified cost model, and a
stakeholder-ready dashboard — all skills a Business Analyst uses to turn ops
data into an action plan.

## 3. Solution Overview
A Streamlit dashboard that pulls **live rainfall/temperature data** for 7
Indian cities from a free weather API, and layers a **transparent, rule-based
demand-disruption model** on top (real quick-commerce order data is never
public) to estimate order volume, delivery delay, cancellations, rider
availability, and ₹ margin impact — refreshable on demand, with a documented
fallback so it never crashes offline.

## 4. Tech Stack
| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.11+ | Core logic |
| Data source | Open-Meteo REST API (free, no key) | Live + historical + forecast weather |
| Data handling | pandas, numpy | Transformation, modeling |
| App/dashboard | Streamlit | Interactive web UI |
| Charts | Plotly | Dual-axis time series, scatter, bar charts |
| HTTP | requests | API calls |
| Testing | pytest | Unit tests on business logic |
| Version control | Git + GitHub | Source control, portfolio hosting |

## 5. Architecture / Pipeline
```
[Open-Meteo API] --(requests, cached 15 min)--> [weather.py]
        |  (on failure: fallback generator)
        v
[weather DataFrame: date, rainfall_mm, temp_max_c, temp_min_c]
        v
[simulate_orders.py]  -- rule-based demand/disruption model -->
[daily ops DataFrame: orders, avg_delivery_min, cancellation_rate,
 rider_availability_pct, revenue_inr, rider_surge_cost_inr,
 sla_penalty_inr, disruption_cost_inr]
        v
[metrics.py] --> KPI summary dict
        v
[app.py: Streamlit] --> KPI cards, 4 charts, alert banner, raw data table
```
This is: **Ingest (API) → Transform/Model (rules engine) → Aggregate (KPIs) →
Visualize (Streamlit) → Recommend (alert banner)** — the same shape as any
production BI pipeline, just running on live+simulated data instead of a
warehouse.

## 6. Data Model
Single daily fact table (in-memory pandas DataFrame, one row per date):

| Column | Type | Description |
|---|---|---|
| date | datetime | Calendar day |
| rainfall_mm | float | Daily rainfall (live from API, or offline fallback) |
| temp_max_c / temp_min_c | float | Daily temperature range |
| severity | str | none / light / moderate / heavy / very_heavy |
| orders | int | Simulated daily order count |
| avg_delivery_min | float | Simulated average delivery time |
| cancellation_rate | float | Simulated cancellation rate (0–1) |
| rider_availability_pct | float | Simulated % of riders active |
| revenue_inr | float | orders × (1 − cancellation_rate) × avg order value |
| rider_surge_cost_inr | float | Extra incentive paid to riders during disruption |
| sla_penalty_inr | float | Estimated cost of late-delivery SLA breaches |
| disruption_cost_inr | float | rider_surge_cost + sla_penalty |

## 7. Rainfall Severity Bands (IMD-style, mm/day)
| Band | Range (mm) |
|---|---|
| none | < 2.5 |
| light | 2.5 – 15 |
| moderate | 15 – 64.5 |
| heavy | 64.5 – 115.5 |
| very_heavy | ≥ 115.5 |

## 8. Demand-Disruption Model (rule-based, fully documented — not a black box)
| Severity | Demand multiplier | Delivery delay add (min) | Cancellation add | Rider availability |
|---|---|---|---|---|
| none | 1.00 | +0 | +0.00 | 100% |
| light | 1.08 | +2 | +0.01 | 97% |
| moderate | 1.22 | +6 | +0.035 | 90% |
| heavy | 1.40 | +14 | +0.08 | 75% |
| very_heavy | 1.55 | +24 | +0.15 | 60% |

Apply on top of a weekday/weekend baseline multiplier (Fri/Sat/Sun higher than
Mon–Wed) and Gaussian noise for realism. All constants live in one
`config.py` — no magic numbers scattered through the code.

## 9. Dashboard Specification
- **Sidebar:** city dropdown (7 cities), mode toggle (Live past-7d+forecast /
  Historical custom range), manual refresh button
- **KPI row (5 cards):** total orders, revenue (₹), avg delivery time, avg
  cancellation rate, total disruption cost (with a "demand uplift % vs dry
  days" delta)
- **Alert banner:** red banner when any day crosses the "heavy" threshold
- **Chart 1:** dual-axis time series — orders (line) vs rainfall (bar)
- **Chart 2:** scatter — rainfall vs delivery delay, colored by intensity
- **Chart 3:** bar — average cancellation rate by severity band
- **Chart 4:** stacked bar — rider surge cost + SLA penalty cost per day
- **Expander 1:** full raw data table
- **Expander 2:** "About this dashboard" — methodology, live vs simulated
  disclosure

## 10. File & Folder Structure
```
monsoon-to-margin/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── tests/
│   ├── test_simulate_orders.py
│   └── test_metrics.py
└── src/
    ├── __init__.py
    ├── config.py
    ├── weather.py
    ├── simulate_orders.py
    └── metrics.py
```

## 11. Step-by-Step Build Order (for the AI)
1. Scaffold the folder structure above; write `.gitignore` and `LICENSE` (MIT).
2. Write `src/config.py` with every constant from Sections 6–8, named clearly.
3. Write `src/weather.py`: `fetch_current_and_forecast()` and
   `fetch_historical()`, each wrapped in try/except that falls back to a
   seeded synthetic weather generator on any failure. Cache with
   `@st.cache_data`.
4. Write `src/simulate_orders.py`: pure function `simulate(weather_df) ->
   DataFrame` implementing Section 8's table exactly.
5. Write `src/metrics.py`: pure function `summarize(df) -> dict` computing
   the KPI row values.
6. Write `tests/test_simulate_orders.py` and `tests/test_metrics.py` — assert
   monotonicity (higher severity ⇒ ≥ orders, ≥ delay, ≥ cancellation, ≤ rider
   availability than a lower band), and that KPIs never crash on an all-dry
   or empty input.
7. Write `app.py` wiring sidebar → weather.py → simulate_orders.py →
   metrics.py → the dashboard layout in Section 9.
8. Run locally (`streamlit run app.py`) in both modes; fix any exception
   until the app runs clean.
9. Write the final `README.md` per Section 14.
10. `git init`, commit, push to GitHub.

## 12. Production-Quality Bar
- [ ] Every function has a type-hinted signature and a docstring
- [ ] No bare `except:` — always catch a specific exception and log/display it
- [ ] No magic numbers outside `config.py`
- [ ] `logging` module used for internal diagnostics (not just `print`)
- [ ] `pytest` passes with at least the monotonicity tests in Step 6
- [ ] `requirements.txt` has pinned minimum versions
- [ ] App runs with zero unhandled exceptions in both modes, online or offline

## 13. Roadmap / Future Enhancements
- Swap the rule-based model for a regression fit once real order data exists
- Add a city-level map view (e.g., pydeck) showing disruption severity
  geographically
- Recreate the KPI view in Power BI/Tableau connected to an exported CSV, to
  demonstrate BI-tool fluency alongside Python
- Add email/Slack alerting when a city crosses the heavy-rain threshold

## 14. Required Contents of the Final `README.md`
Business problem (Section 1) → what's live vs. simulated (a table) →
features list → setup steps (`pip install -r requirements.txt`, `streamlit
run app.py`) → full tech stack list → project structure tree → "tuning the
model" section pointing at `config.py` → limitations.

## 15. Definition of Done
- [ ] Runs with zero exceptions via `streamlit run app.py`
- [ ] All 4 charts + 5 KPI cards + alert banner render correctly
- [ ] Offline fallback verified (works with no internet)
- [ ] Tests pass
- [ ] README complete per Section 14

## 16. Resume Bullet Template
"Built a live ops-analytics dashboard (Python, Streamlit, Plotly, REST API)
modeling monsoon disruption impact on quick-commerce delivery SLAs and margin
across 7 cities."