from datetime import date
import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Monsoon-to-Margin | Operations Control Tower", page_icon="◈", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1500px}
.hero{padding:1.2rem 1.4rem;border-radius:18px;background:linear-gradient(135deg,#071b2f,#123d5a);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;color:#cde9f7}
.badge{display:inline-block;background:#0ea5e9;color:white;padding:.25rem .6rem;border-radius:999px;font-size:.75rem;font-weight:700}
</style>
""",unsafe_allow_html=True)

CITIES={"Chennai":(13.0827,80.2707),"Bengaluru":(12.9716,77.5946),"Hyderabad":(17.385,78.4867),"Mumbai":(19.076,72.8777),"Delhi":(28.6139,77.209),"Pune":(18.5204,73.8567),"Kolkata":(22.5726,88.3639)}
BANDS=[("none",0,2.5),("light",2.5,15),("moderate",15,64.5),("heavy",64.5,115.5),("very_heavy",115.5,10000)]
RULES={"none":(1.00,0,.00,1.00),"light":(1.08,2,.01,.97),"moderate":(1.22,6,.035,.90),"heavy":(1.40,14,.08,.75),"very_heavy":(1.55,24,.15,.60)}
CITY_BASE={"Chennai":4800,"Bengaluru":5200,"Hyderabad":3900,"Mumbai":5600,"Delhi":6100,"Pune":3100,"Kolkata":3600}
CITY_MARGIN={"Chennai":82,"Bengaluru":86,"Hyderabad":84,"Mumbai":80,"Delhi":78,"Pune":88,"Kolkata":81}

def severity(mm):
    for name,lo,hi in BANDS:
        if lo<=mm<hi:return name
    return "very_heavy"

@st.cache_data(ttl=900)
def get_weather(city):
    lat,lon=CITIES[city]
    params={"latitude":lat,"longitude":lon,"daily":"precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max","forecast_days":16,"timezone":"auto"}
    try:
        r=requests.get("https://api.open-meteo.com/v1/forecast",params=params,timeout=12); r.raise_for_status(); j=r.json()["daily"]
        return pd.DataFrame({"date":pd.to_datetime(j["time"]),"rainfall_mm":j["precipitation_sum"],"temp_max_c":j["temperature_2m_max"],"temp_min_c":j["temperature_2m_min"],"wind_kmh":j["wind_speed_10m_max"],"source":"Live Open-Meteo"})
    except Exception:
        seed=list(CITIES).index(city)+100; rng=np.random.default_rng(seed); d=pd.date_range(date.today(),periods=16)
        return pd.DataFrame({"date":d,"rainfall_mm":rng.gamma(1.2,12,16),"temp_max_c":rng.normal(31,2,16),"temp_min_c":rng.normal(25,2,16),"wind_kmh":rng.uniform(8,28,16),"source":"Synthetic fallback"})

def simulate(weather,city,seed=42):
    d=weather.copy(); d["severity"]=d.rainfall_mm.apply(severity); mult=d.severity.map(lambda x:RULES[x][0]); delay=d.severity.map(lambda x:RULES[x][1]); cancel=d.severity.map(lambda x:RULES[x][2]); rider=d.severity.map(lambda x:RULES[x][3])
    rng=np.random.default_rng(seed+list(CITIES).index(city)); weekend=np.where(d.date.dt.dayofweek>=4,1.08,1.0)
    d["orders"]=np.maximum(0,np.round(CITY_BASE[city]*weekend*mult+rng.normal(0,CITY_BASE[city]*.035,len(d)))).astype(int)
    d["avg_delivery_min"]=13.2+delay+rng.normal(0,.7,len(d)); d["cancellation_rate"]=np.clip(.024+cancel+rng.normal(0,.0025,len(d)),0,.95); d["rider_availability_pct"]=rider
    d["revenue_inr"]=d.orders*(1-d.cancellation_rate)*390; d["surge_cost_inr"]=d.orders*(1-d.rider_availability_pct)/25*85
    d["sla_penalty_inr"]=d.orders*d.cancellation_rate*22; d["contribution_margin_inr"]=d.orders*(1-d.cancellation_rate)*CITY_MARGIN[city]-d.surge_cost_inr-d.sla_penalty_inr
    d["disruption_cost_inr"]=d.surge_cost_inr+d.sla_penalty_inr
    d["disruption_index"]=np.clip((d.avg_delivery_min-12)*2.7+d.cancellation_rate*180+(1-d.rider_availability_pct)*55,0,100)
    return d

st.markdown('<div class="hero"><span class="badge">LIVE WEATHER • OPERATIONS CONTROL TOWER</span><h1>Monsoon-to-Margin — Quick-Commerce Disruption Intelligence</h1><p>Live 16-day weather forecast translated into demand, capacity, SLA and contribution-margin scenarios across seven Indian cities.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    scope=st.radio("View",["City Control Tower","India Portfolio"])
    city=st.selectbox("City",list(CITIES))
    rain_scenario=st.slider("Scenario rainfall multiplier",.5,2.0,1.0,.1)

if scope=="India Portfolio":
    frames=[]
    for c in CITIES:
        w=get_weather(c); s=simulate(w,c); s["city"]=c; frames.append(s)
    portfolio=pd.concat(frames,ignore_index=True)
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Portfolio Orders",f"{portfolio.orders.sum()/1e6:.2f}M"); c2.metric("Revenue",f"₹{portfolio.revenue_inr.sum()/1e7:.2f}Cr")
    c3.metric("Avg Delivery",f"{portfolio.avg_delivery_min.mean():.1f} min"); c4.metric("Cancellation",f"{portfolio.cancellation_rate.mean():.1%}")
    c5.metric("Disruption Cost",f"₹{portfolio.disruption_cost_inr.sum()/1e7:.2f}Cr")
    risk=portfolio.groupby("city",as_index=False).agg(disruption_index=("disruption_index","mean"),margin=("contribution_margin_inr","sum"),rainfall=("rainfall_mm","sum"),cancellation=("cancellation_rate","mean"))
    l,r=st.columns(2); l.plotly_chart(px.bar(risk.sort_values("disruption_index",ascending=False),x="city",y="disruption_index",title="City Disruption Index"),use_container_width=True)
    r.plotly_chart(px.bar(risk.sort_values("margin"),x="city",y="margin",title="Contribution Margin by City"),use_container_width=True)
    map_df=risk.merge(pd.DataFrame([{"city":k,"lat":v[0],"lon":v[1]} for k,v in CITIES.items()]),on="city")
    st.plotly_chart(px.scatter_geo(map_df,lat="lat",lon="lon",size="disruption_index",color="disruption_index",hover_name="city",projection="natural earth",title="India City Risk Map"),use_container_width=True)
    st.dataframe(risk.sort_values("disruption_index",ascending=False),use_container_width=True,hide_index=True)
else:
    weather=get_weather(city); weather["rainfall_mm"]=weather.rainfall_mm*rain_scenario; ops=simulate(weather,city)
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Forecast Orders",f"{ops.orders.sum():,.0f}"); c2.metric("Revenue",f"₹{ops.revenue_inr.sum()/1e7:.2f}Cr"); c3.metric("Avg Delivery",f"{ops.avg_delivery_min.mean():.1f} min")
    c4.metric("Cancellation",f"{ops.cancellation_rate.mean():.1%}"); c5.metric("Contribution Margin",f"₹{ops.contribution_margin_inr.sum()/1e7:.2f}Cr")
    st.caption(f"{city} • weather source: {ops.source.iloc[0]} • refresh: 15-minute cache • scenario rainfall multiplier: {rain_scenario:.1f}×")
    if ops.severity.isin(["heavy","very_heavy"]).any(): st.error(f"Heavy-rain threshold crossed in {city} during the forecast window.")
    t1,t2,t3,t4=st.tabs(["Forecast","Disruption Economics","Capacity","What-if"])
    with t1:
        l,r=st.columns(2); l.plotly_chart(px.bar(ops,x="date",y="rainfall_mm",color="severity",title=f"Forecast Rainfall — {city}"),use_container_width=True)
        r.plotly_chart(px.line(ops,x="date",y="orders",title="Expected Orders"),use_container_width=True)
        st.plotly_chart(px.scatter(ops,x="rainfall_mm",y="avg_delivery_min",color="severity",size="orders",title="Rainfall vs Delivery Time"),use_container_width=True)
    with t2:
        bridge=pd.DataFrame({"component":["Gross Contribution","Rider Surge","SLA Penalties"],"value":[(ops.orders*(1-ops.cancellation_rate)*CITY_MARGIN[city]).sum(),-ops.surge_cost_inr.sum(),-ops.sla_penalty_inr.sum()]})
        fig=go.Figure(go.Waterfall(x=bridge.component,y=bridge.value,measure=["relative","relative","total"])); fig.update_layout(title="Contribution Margin Bridge")
        st.plotly_chart(fig,use_container_width=True); st.dataframe(ops[["date","severity","orders","revenue_inr","surge_cost_inr","sla_penalty_inr","contribution_margin_inr"]],use_container_width=True,hide_index=True)
    with t3:
        st.plotly_chart(px.line(ops,x="date",y="rider_availability_pct",title="Rider Availability"),use_container_width=True)
        st.plotly_chart(px.bar(ops,x="date",y="disruption_index",color="severity",title="Daily Disruption Index"),use_container_width=True)
    with t4:
        rain=st.slider("Assumed daily rainfall",0.0,150.0,float(max(ops.rainfall_mm.mean(),5)),1.0)
        sev=severity(rain); mult,delay,cancel,rider=RULES[sev]; orders=CITY_BASE[city]*mult; delivery=13.2+delay; canc=.024+cancel
        revenue=orders*(1-canc)*390; margin=orders*(1-canc)*CITY_MARGIN[city]-orders*(1-rider)/25*85-orders*canc*22
        a,b,c,d=st.columns(4); a.metric("Scenario Orders",f"{orders:,.0f}"); b.metric("Delivery",f"{delivery:.1f} min"); c.metric("Cancellation",f"{canc:.1%}"); d.metric("Contribution Margin",f"₹{margin:,.0f}")
        st.info("Sensitivity analysis only: the disruption model is rule-based and not a causal forecast.")
