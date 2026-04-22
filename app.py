import streamlit as st
import pandas as pd
import numpy as np
import joblib

from pricer import (
    Product,
    suggest_price,
    freshness_factor,
    format_sms,
    simulate_7_days
)

# -----------------------------
# LOAD TRAINED ML MODEL
# -----------------------------
ml_model = joblib.load("demand_model.pkl")

def ml_predict(price, age_hours, comp_avg, product_encoded):
    X = pd.DataFrame([[
        price,
        age_hours,
        comp_avg,
        product_encoded
    ]], columns=["price", "age_hours", "comp_avg_price", "product_encoded"])

    return ml_model.predict(X)[0]

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="AI Hybrid Pricing Engine", layout="wide")

st.title("🧠 AI Hybrid Retail Pricing System")
st.markdown("Rule-based + Machine Learning Dynamic Pricing Engine")

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.header("📦 Product Configuration")

sku = st.sidebar.text_input("Product SKU", "TOMATO-A")
cost = st.sidebar.number_input("Cost (RWF)", 500, 10000, 1000)
shelf_life = st.sidebar.number_input("Shelf Life (days)", 1, 14, 7)

p_ref = st.sidebar.number_input("Reference Price", 1000, 10000, 1800)
Q0 = st.sidebar.number_input("Base Demand (Q0)", 10, 500, 50)
alpha = st.sidebar.slider("Price Sensitivity (alpha)", 0.1, 5.0, 1.5)

age = st.sidebar.slider("Product Age (days)", 0.0, float(shelf_life), 3.0)

# Competitors
comp1 = st.sidebar.number_input("Competitor 1", 1000, 10000, 1600)
comp2 = st.sidebar.number_input("Competitor 2", 1000, 10000, 1700)
comp3 = st.sidebar.number_input("Competitor 3", 1000, 10000, 1900)

competitors = [comp1, comp2, comp3]

# -----------------------------
# PRODUCT OBJECT
# -----------------------------
product = Product(
    sku=sku,
    cost=cost,
    shelf_life_days=shelf_life,
    p_ref=p_ref,
    Q0=Q0,
    alpha=alpha
)

# -----------------------------
# RULE-BASED RESULT
# -----------------------------
result = suggest_price(product, age, competitors)

# -----------------------------
# DISPLAY METRICS
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🧊 Freshness", f"{result['freshness']:.3f}")
    st.write(result["freshness_label"])

with col2:
    st.metric("💰 Rule Price", f"{result['suggested_price']:.0f} RWF")

with col3:
    st.metric("📈 Margin %", f"{result['margin_pct']:.1f}%")

st.divider()

# -----------------------------
# SMS OUTPUT
# -----------------------------
st.subheader("📲 SMS Output")
st.code(format_sms(result, "RWF"))

# -----------------------------
# FRESHNESS CURVE
# -----------------------------
st.subheader("📉 Freshness Decay Curve")

days = np.linspace(0, shelf_life, 50)
values = [freshness_factor(d, shelf_life) for d in days]

df_curve = pd.DataFrame({
    "Day": days,
    "Freshness": values
})

st.line_chart(df_curve.set_index("Day"))

# -----------------------------
# COMPETITOR VIEW
# -----------------------------
st.subheader("🏪 Market Comparison")

df_comp = pd.DataFrame({
    "Entity": ["Competitor 1", "Competitor 2", "Competitor 3", "YOU (Rule)"],
    "Price (RWF)": [comp1, comp2, comp3, result["suggested_price"]]
})

st.dataframe(df_comp)

# -----------------------------
# ML VS RULE COMPARISON
# -----------------------------
st.subheader("⚖️ Rule Engine vs ML Model")

comp_avg = np.mean(competitors)
product_encoded = 0

rule_profit = result["expected_daily_profit"]

ml_demand = ml_predict(
    result["suggested_price"],
    age * 24,
    comp_avg,
    product_encoded
)

ml_profit = (result["suggested_price"] - cost) * ml_demand

col1, col2 = st.columns(2)

with col1:
    st.metric("📏 Rule Profit", f"{rule_profit:.2f} RWF")

with col2:
    st.metric("🤖 ML Profit", f"{ml_profit:.2f} RWF")

# -----------------------------
# PROFIT CURVE COMPARISON
# -----------------------------
st.subheader("📊 Profit Curve Comparison")

prices = np.linspace(500, 5000, 30)

ml_profits = []
rule_profits = []

for p in prices:
    ml_d = ml_predict(p, age * 24, comp_avg, product_encoded)
    ml_profits.append((p - cost) * ml_d)

    rule_profits.append(result["expected_daily_profit"])

df_compare = pd.DataFrame({
    "Price": prices,
    "ML_Profit": ml_profits,
    "Rule_Profit": rule_profits
})

st.line_chart(df_compare.set_index("Price"))

# -----------------------------
# 7-DAY SIMULATION
# -----------------------------
st.subheader("📊 7-Day Simulation")

if st.button("Run Simulation"):

    sim = simulate_7_days(product, competitors)
    df_sim = pd.DataFrame(sim)

    if "day" in df_sim.columns:
        st.line_chart(df_sim.set_index("day")[["our_price", "demand"]])

    st.dataframe(df_sim)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown("⚡ Hybrid AI Pricing System — Rule Engine + Machine Learning | AIMS-RIC Hackathon")