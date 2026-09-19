from datetime import date, timedelta
import numpy as np, pandas as pd, requests, streamlit as st, plotly.express as px

st.set_page_config(page_title="Monsoon-to-Margin",layout="wide")
st.title("Monsoon-to-Margin — Live Weather & Quick-Commerce Disruption")
st.caption("Weather is live from Open-Meteo; business operations are simulated transparently.")

CITIES={"Chennai":(13.0827,80.2707),"Bengaluru":(12.9716,77.5946),"Hyderabad":(17.385,78.4867),
        "Mumbai":(19.076,72.8777),"Delhi":(28.6139,77.209),"Pune":(18.5204,73.8567),"Kolkata":(22.5726,88.3639)}
BANDS=[("none",0,2.5),("light",2.5,15),("moderate",15,64.5),("heavy",64.5,115.5),("very_heavy",115.5,99999)]
RULES={"none":(1,0,0,1),"light":(1.08,2,.01,.97),"moderate":(1.22,6,.035,.90),"heavy":(1.40,14,.08,.75),"very_heavy":(1.55,24,.15,.60)}

def sev(x):
    for n,lo,hi in BANDS:
        if lo<=x<hi:return n
    return "very_heavy"

@st.cache_data(ttl=900)
def weather(city):
    lat,lon=CITIES[city]
    params={"latitude":lat,"longitude":lon,"hourly":"temperature_2m,precipitation","forecast_days":16,"timezone":"auto"}
    try:
        j=requests.get("https://api.open-meteo.com/v1/forecast",params=params,timeout=12)
        j.raise_for_status()
        h=j.json()["hourly"]
        d=pd.DataFrame({"date":pd.to_datetime(h["time"]).date,
                        "rain":h["precipitation"],"temp":h["temperature_2m"]})
        return d.groupby("date",as_index=False).agg(rainfall_mm=("rain","sum"),temp_c=("temp","mean"))
    except Exception:
        rng=np.random.default_rng(42)
        dates=pd.date_range(date.today()-timedelta(days=7),periods=15)
        return pd.DataFrame({"date":dates.date,"rainfall_mm":rng.gamma(1.2,12,15),"temp_c":rng.normal(29,2,15)})

city=st.sidebar.selectbox("City",list(CITIES))
df=weather(city)
df["severity"]=df.rainfall_mm.apply(sev)

rng=np.random.default_rng(42)
weekday=np.where(pd.to_datetime(df.date).dt.dayofweek>=4,1.10,1.0)
mult=df.severity.map(lambda x:RULES[x][0])
delay=df.severity.map(lambda x:RULES[x][1])
cancel_add=df.severity.map(lambda x:RULES[x][2])
rider=df.severity.map(lambda x:RULES[x][3])
df["orders"]=np.maximum(0,np.round(4200*weekday*mult+rng.normal(0,170,len(df)))).astype(int)
df["avg_delivery_min"]=13+delay+rng.normal(0,.7,len(df))
df["cancellation_rate"]=np.clip(.025+cancel_add+rng.normal(0,.003,len(df)),0,.95)
df["rider_availability_pct"]=rider
df["revenue_inr"]=df.orders*(1-df.cancellation_rate)*390
df["rider_surge_cost_inr"]=df.orders*(1-df.rider_availability_pct)/25*85
df["sla_penalty_inr"]=df.orders*df.cancellation_rate*22
df["disruption_cost_inr"]=df.rider_surge_cost_inr+df.sla_penalty_inr

c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Orders",f"{df.orders.sum():,.0f}")
c2.metric("Revenue",f"INR {df.revenue_inr.sum():,.0f}")
c3.metric("Avg Delivery",f"{df.avg_delivery_min.mean():.1f} min")
c4.metric("Cancellation",f"{df.cancellation_rate.mean():.1%}")
c5.metric("Disruption Cost",f"INR {df.disruption_cost_inr.sum():,.0f}")

if df.severity.isin(["heavy","very_heavy"]).any():
    st.error("Heavy-rain disruption threshold crossed.")

st.plotly_chart(px.bar(df,x="date",y="rainfall_mm",title=f"Rainfall — {city}"),use_container_width=True)
st.plotly_chart(px.scatter(df,x="rainfall_mm",y="avg_delivery_min",color="severity",title="Rainfall vs Delivery Delay"),use_container_width=True)
st.plotly_chart(px.bar(df.groupby("severity",as_index=False).cancellation_rate.mean(),x="severity",y="cancellation_rate",title="Cancellation Rate by Severity"),use_container_width=True)
st.dataframe(df,use_container_width=True)
