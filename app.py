import streamlit as st
from pricer import Product, suggest_price, freshness_factor
import pandas as pd

st.set_page_config(page_title="Dynamic Pricing Engine", layout="centered")

st.title("📊 Perishable Goods Dynamic Pricing")

# -------------------------
# INPUT SECTION
# -------------------------
st.header("🔧 Input Parameters")

cost = st.number_input("Cost (UGX)", 100, 10000, 1000)
shelf_life = st.number_input("Shelf Life (days)", 1, 30, 7)
age = st.slider("Current Age (days)", 0.0, float(shelf_life), 2.0)

p_ref = st.number_input("Reference Price", 100, 10000, 1800)
Q0 = st.number_input("Base Demand (Q0)", 1, 500, 50)
alpha = st.slider("Price Sensitivity (alpha)", 0.1, 3.0, 1.5)

competitors_input = st.text_input(
    "Competitor Prices (comma-separated)",
    "1600,1700,1900"
)

competitors = [float(x.strip()) for x in competitors_input.split(",")]

# -------------------------
# COMPUTE PRICE
# -------------------------
product = Product(
    sku="PRODUCT",
    cost=cost,
    shelf_life_days=shelf_life,
    p_ref=p_ref,
    Q0=Q0,
    alpha=alpha,
)

if st.button("💰 Suggest Price"):
    result = suggest_price(product, age, competitors)

    st.success(f"Recommended Price: {result['suggested_price']} UGX")
    st.write(f"Freshness: {result['freshness']:.3f}")
    st.write(f"Status: {result['freshness_label']}")
    st.write(f"Margin: {result['margin_pct']:.1f}%")

    if result["freshness"] < 0.3:
        st.warning("⚠️ Sell fast! Product near expiry")

# -------------------------
# FRESHNESS CURVE
# -------------------------
st.header("📉 Freshness Curve")

days = list(range(0, int(shelf_life)+1))
sigmoid = [freshness_factor(d, shelf_life) for d in days]
linear = [max(0, 1 - d / shelf_life) for d in days]

df = pd.DataFrame({
    "Day": days,
    "Sigmoid": sigmoid,
    "Linear": linear
})

st.line_chart(df.set_index("Day"))

# -------------------------
# DEMO TABLE
# -------------------------
st.header("📊 Price Evolution")

demo_data = []
for d in [0, 2, shelf_life/2, shelf_life-1]:
    res = suggest_price(product, d, competitors)
    demo_data.append({
        "Day": d,
        "Price": res["suggested_price"],
        "Freshness": round(res["freshness"], 3),
        "Label": res["freshness_label"]
    })

st.table(pd.DataFrame(demo_data))

# -------------------------
# SMS OUTPUT
# -------------------------
st.header("📱 SMS Output")

if st.button("Generate SMS"):
    res = suggest_price(product, age, competitors)
    sms = f"{product.sku} {int(res['suggested_price'])} UGX | SELL FAST"
    st.code(sms)