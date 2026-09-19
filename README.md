# Monsoon-to-Margin

### Live Quick-Commerce Disruption Control Tower

**[Open Live Dashboard ↗](https://harsha-monsoon-margin.streamlit.app)**

A portfolio-grade operations dashboard that combines **live Open-Meteo weather data across seven Indian cities** with a transparent quick-commerce disruption model.

## Key capabilities

- City and India portfolio views
- Live 16-day precipitation / temperature / wind forecast
- Demand, delivery-delay and cancellation scenario engine
- Rider-capacity and SLA penalty modeling
- Contribution-margin bridge
- City disruption ranking and map
- Rainfall what-if simulator
- 15-minute weather cache and offline fallback

## Live vs simulated

**Live:** weather inputs from Open-Meteo.

**Simulated:** orders, rider availability, cancellations, revenue and margin because real quick-commerce order data is private.

## Technology

Python • Streamlit • requests • pandas • NumPy • Plotly • Open-Meteo API

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
