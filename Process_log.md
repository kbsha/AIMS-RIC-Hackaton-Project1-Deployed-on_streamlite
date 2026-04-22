# Process Log — AIMS KTT Hackathon  
**Project:** AI Hybrid Retail Dynamic Pricing System  
**Author:** Kibremoges Fenta  

---

## ⏱️ Timeline (Hour-by-Hour)

**Hour 1 — Problem Understanding & Design**
- Reviewed the challenge: dynamic pricing for perishable goods.
- Identified key variables: freshness, demand, price sensitivity, competition.
- Decided to model freshness as a function of product age and shelf life.

**Hour 2 — Core Pricing Engine**
- Implemented `Product` data model.
- Designed freshness function using sigmoid decay.
- Built demand model: exponential price elasticity with freshness scaling.
- Implemented profit function and grid-search optimization.

**Hour 3 — Strategy & Simulation**
- Added competitor-aware price adjustment.
- Built `suggest_price()` main engine.
- Implemented 7-day simulation comparing:
  - Dynamic engine
  - Cost-plus baseline
  - Cheapest competitor strategy
- Verified outputs and sanity-checked results.

**Hour 4 — Interface & Visualization**
- Built Streamlit app:
  - Input controls (cost, shelf life, competitors)
  - Real-time price recommendation
  - Freshness curve visualization
  - SMS output for vendors
- Fixed data formatting and chart issues.

**Hour 5 — Machine Learning Integration**
- Used synthetic dataset (`sales_history.csv`) to train demand model.
- Trained regression model (XGBoost) to predict demand.
- Saved model and integrated into Streamlit.
- Compared ML vs rule-based profit outputs.

**Hour 6 — Deployment & Debugging**
- Deployed app to Hugging Face Spaces.
- Fixed file path issues (model loading).
- Switched to remote model loading via Hugging Face Hub.
- Ensured reproducibility and no local dependencies.

---

## 🧰 Tools & LLM Usage

| Tool | Purpose |
|------|--------|
| Python (NumPy, Pandas) | Data processing and simulation |
| Streamlit | Frontend UI and visualization |
| XGBoost | Machine learning demand model |
| Hugging Face Hub | Model hosting and deployment |
| ChatGPT | Architecture guidance, debugging, and optimization |

### Why LLM was used:
- To accelerate design decisions (e.g., sigmoid vs linear decay)
- To debug environment and deployment issues
- To structure the Streamlit + ML integration cleanly

---

## 💬 Sample Prompts Used

### Prompt 1 (used)
> “How to design a pricing model for perishable goods using freshness decay and demand elasticity?”

✔ Helped define the core economic model.

---

### Prompt 2 (used)
> “How to integrate a trained XGBoost model into a Streamlit app for real-time prediction?”

✔ Used to connect ML model with UI.

---

### Prompt 3 (used)
> “How to deploy a Streamlit app with a model on Hugging Face Spaces without file errors?”

✔ Solved deployment and file path issues.

---

### Prompt 4 (discarded)
> “Generate a fully automatic AI pricing system with deep reinforcement learning.”

❌ Discarded because:
- Too complex for hackathon scope
- Hard to explain during live defense
- Reduced interpretability

---

## ⚖️ Hardest Decision

The hardest decision was choosing between a purely machine learning approach and a rule-based economic model.

A fully ML-based system could learn complex patterns but lacks interpretability and requires large, high-quality datasets. On the other hand, a rule-based system is transparent, fast, and reliable but less adaptive.

I chose a **hybrid approach**:
- Rule-based model for pricing logic and interpretability
- Machine learning model for demand estimation and validation

This balances **explainability, performance, and real-world practicality**, especially in low-resource retail environments.

---

## ✅ Summary

The final system combines:
- Freshness-aware pricing (sigmoid decay)
- Demand modeling (economic + ML)
- Competitive adjustment
- Real-time UI (Streamlit)
- SMS-based output for local usability

The solution is designed not only for accuracy, but for **practical deployment in real market conditions**.