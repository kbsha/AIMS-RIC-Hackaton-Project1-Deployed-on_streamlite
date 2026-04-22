import streamlit as st
import pandas as pd
import numpy as np

from pricer import (
    Product,
    suggest_price,
    freshness_factor,
    format_sms,
    simulate_7_days
)

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AI Freshness Pricing Engine",
    layout="wide"
)

st.title("🧠 AI Freshness-Based Pricing Engine")
st.markdown("Dynamic pricing system for perishable goods (Uganda market simulation)")

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.header("📦 Product Configuration")

sku = st.sidebar.text_input("Product SKU", "TOMATO-A")
cost = st.sidebar.number_input("Cost (UGX)", 500, 10000, 1000)
shelf_life = st.sidebar.number_input("Shelf Life (days)", 1, 14, 7)

p_ref = st.sidebar.number_input("Reference Price", 1000, 10000, 1800)
Q0 = st.sidebar.number_input("Base Demand (Q0)", 10, 500, 50)
alpha = st.sidebar.slider("Price Sensitivity (alpha)", 0.1, 5.0, 1.5)

st.sidebar.markdown("---")
age = st.sidebar.slider("Product Age (days)", 0.0, float(shelf_life), 3.0)

# Competitor prices
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
# MAIN RESULT
# -----------------------------
result = suggest_price(product, age, competitors)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🧊 Freshness Score", f"{result['freshness']:.3f}")
    st.write(result["freshness_label"])

with col2:
    st.metric("💰 Suggested Price", f"{result['suggested_price']:.0f} UGX")

with col3:
    st.metric("📈 Margin %", f"{result['margin_pct']:.1f}%")

st.divider()

# -----------------------------
# SMS OUTPUT
# -----------------------------
st.subheader("📲 Farmer SMS Output")
sms = format_sms(result, "UGX")
st.code(sms)

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

# df_comp = pd.DataFrame({
#     "Competitor": ["C1", "C2", "C3"],
#     "Price (UGX)": competitors
# })

# df_comp.loc["Our Price"] = ["YOU", result["suggested_price"]]

# st.dataframe(df_comp)

st.subheader("🏪 Market Comparison")

df_comp = pd.DataFrame({
    "Entity": ["Competitor 1", "Competitor 2", "Competitor 3", "YOU"],
    "Price (UGX)": [comp1, comp2, comp3, result["suggested_price"]]
})

st.dataframe(df_comp)

# -----------------------------
# SIMULATION SECTION
# -----------------------------
st.subheader("📊 7-Day Simulation (Quick Insight)")

# if st.button("Run Simulation"):
#     sim = simulate_7_days(product, competitors)

#     st.line_chart(sim.set_index("day")[["our_price", "demand"]])

#     st.write("### Simulation Table")
#     st.dataframe(sim)


st.subheader("📊 7-Day Simulation (Quick Insight)")

if st.button("Run Simulation"):

    sim = simulate_7_days(product, competitors)

    # 🔥 Ensure it's a DataFrame
    df_sim = pd.DataFrame(sim)

    # Safety check (optional but good for hackathons)
    if "day" in df_sim.columns:
        st.line_chart(df_sim.set_index("day")[["our_price", "demand"]])

    st.dataframe(df_sim)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown("⚡ Built for Hackathon: AI Dynamic Pricing Engine")