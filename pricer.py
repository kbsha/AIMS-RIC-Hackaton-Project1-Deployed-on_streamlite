"""
pricer.py — Perishable Goods Dynamic Pricing Engine
AIMS KTT Hackathon Solution
Author: [Your Name]

CORE IDEA:
  Price should fall as goods age — but not linearly.
  Freshness drops like a sigmoid cliff near expiry.
  We find the price that maximizes (profit per unit) × (expected demand).
"""

import math
import argparse
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────
# 1. DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class Product:
    """Everything the engine needs to know about one SKU."""
    sku: str
    cost: float          # What you paid per unit (UGX / KES / local currency)
    shelf_life_days: int # Days until unsellable
    p_ref: float         # "Normal" full-price when perfectly fresh
    Q0: float            # Expected daily demand at reference price & full freshness
    alpha: float = 1.5   # Price sensitivity: higher = customers more price-sensitive
    margin_floor: float  = 1.10  # Never sell below cost × this (e.g. 1.10 = 10% min margin)
    k: float = 8.0       # Sigmoid sharpness: higher = sharper freshness cliff


# ─────────────────────────────────────────────
# 2. FRESHNESS FUNCTION  (The Heart of the Engine)
# ─────────────────────────────────────────────

def freshness_factor(age_days: float, shelf_life: int, k: float = 8.0) -> float:
    """
    Returns a value in (0, 1] representing how 'fresh' the product is.

    FORMULA:
        freshness = 1 / (1 + exp(k * (age - shelf_life/2) / shelf_life))

    WHY SIGMOID, NOT LINEAR?
        - Linear decay: tomato loses equal value every day. Unrealistic.
        - Sigmoid: product stays near full value for the first half of shelf life,
          then VALUE COLLAPSES near expiry — matching real buyer psychology.
        - At age=0:         freshness ≈ 1.0  (perfectly fresh)
        - At age=half-life: freshness = 0.5  (midpoint — important for interviews!)
        - At age=shelf_life: freshness ≈ 0.02 (near-expired, almost worthless)

    INTERVIEW ANSWER for "What happens at half shelf life?":
        "The price is roughly halfway between full price and minimum floor.
         This is intentional — it's the inflection point where we start aggressive
         discounting to clear stock before waste occurs."
    """
    if age_days >= shelf_life:
        return 0.001  # Expired: unsellable (near-zero, not zero, to avoid log errors)

    ratio = (age_days - shelf_life / 2.0) / shelf_life
    return 1.0 / (1.0 + math.exp(k * ratio))


# ─────────────────────────────────────────────
# 3. DEMAND MODEL
# ─────────────────────────────────────────────

def expected_demand(price: float, product: Product, freshness: float) -> float:
    """
    Q(p) = Q0 × exp(-α × (p - p_ref) / p_ref) × freshness

    HOW TO READ THIS:
        - If p = p_ref (reference price): demand = Q0 × freshness
        - If p > p_ref: demand falls exponentially (customers walk away)
        - If p < p_ref: demand rises (bargain hunters come in)
        - freshness scales everything: near-expired goods sell less regardless of price

    This is a standard "constant elasticity" demand model — simple, defensible,
    and widely used in revenue management literature.
    """
    price_effect = math.exp(-product.alpha * (price - product.p_ref) / product.p_ref)
    return product.Q0 * price_effect * freshness


# ─────────────────────────────────────────────
# 4. PROFIT FUNCTION
# ─────────────────────────────────────────────

def expected_profit(price: float, product: Product, freshness: float) -> float:
    """
    Profit = (price - cost) × expected_demand(price)

    We maximise this over a grid of candidate prices.
    Simple grid search — fast, transparent, no black box.
    """
    margin = price - product.cost
    if margin <= 0:
        return 0.0  # Never sell at a loss
    return margin * expected_demand(price, product, freshness)


# ─────────────────────────────────────────────
# 5. COMPETITOR ADJUSTMENT
# ─────────────────────────────────────────────

def apply_competitor_pressure(
    optimal_price: float,
    competitor_prices: list[float],
    beta: float = 0.20
) -> float:
    """
    Nudge price down if we're significantly more expensive than competitors.

    FORMULA:
        if p* > min_competitor:
            discount = β × (p* - min_competitor) / p*
            p_final = p* × (1 - discount)

    WHY NOT JUST MATCH LOWEST PRICE?
        Because undercutting on price is a race to the bottom.
        We only adjust partially (β = 0.20 = 20% of the gap).
        This maintains margin while staying competitive.
    """
    if not competitor_prices:
        return optimal_price

    min_comp = min(competitor_prices)

    if optimal_price <= min_comp:
        return optimal_price  # Already competitive, no change needed

    gap_ratio = (optimal_price - min_comp) / optimal_price
    discount_fraction = beta * gap_ratio
    adjusted = optimal_price * (1.0 - discount_fraction)
    return adjusted


# ─────────────────────────────────────────────
# 6. THE MAIN PRICING FUNCTION
# ─────────────────────────────────────────────

def suggest_price(
    product: Product,
    age_days: float,
    competitor_prices: Optional[list[float]] = None,
    grid_steps: int = 200,
    beta: float = 0.20
) -> dict:
    """
    THE CORE ENGINE.

    Given a product, its age, and competitor prices:
    → Find the price that maximises expected profit
    → Enforce minimum margin floor
    → Adjust for competition
    → Return price + explanation

    STEPS:
        1. Compute freshness
        2. Build price grid from floor to ceiling
        3. Score each price by expected profit
        4. Pick winner
        5. Competitor adjustment
        6. Enforce margin floor (safety net)
        7. Return result + reasoning
    """
    competitor_prices = competitor_prices or []

    # Step 1: How fresh is this product right now?
    freshness = freshness_factor(age_days, product.shelf_life_days, product.k)

    # Step 2: Build candidate price range
    min_price = product.cost * product.margin_floor   # Hard floor: must cover cost
    max_price = product.p_ref * 1.5                   # Ceiling: don't be absurd

    if min_price >= max_price:
        # Edge case: cost is too high relative to market — flag it
        return {
            "sku": product.sku,
            "suggested_price": min_price,
            "freshness": round(freshness, 3),
            "expected_demand": 0.0,
            "expected_profit": 0.0,
            "note": "WARNING: Cost floor exceeds max price. Check cost data.",
            "age_days": age_days,
        }

    # Step 3: Grid search — test 200 candidate prices
    # KEY INSIGHT: as freshness drops, the "effective" demand ceiling drops,
    # so the profit-maximising price shifts LEFT (lower).
    # We also shrink max_price by freshness so we search a relevant range.
    effective_max = min_price + (max_price - min_price) * max(freshness, 0.05)

    step = (effective_max - min_price) / grid_steps
    best_price = min_price
    best_profit = 0.0

    for i in range(grid_steps + 1):
        candidate = min_price + i * step
        profit = expected_profit(candidate, product, freshness)
        if profit > best_profit:
            best_profit = profit
            best_price = candidate

    # Step 4: Apply competitor pressure
    adjusted_price = apply_competitor_pressure(best_price, competitor_prices, beta)

    # Step 5: Enforce margin floor (safety net — can never go below this)
    final_price = max(adjusted_price, product.cost * product.margin_floor)

    # Step 6: Build explanation (critical for interviews + SMS output)
    days_left = product.shelf_life_days - age_days
    demand_at_price = expected_demand(final_price, product, freshness)

    if freshness > 0.8:
        freshness_label = "FRESH"
    elif freshness > 0.5:
        freshness_label = "GOOD"
    elif freshness > 0.2:
        freshness_label = "AGING"
    else:
        freshness_label = "CLEAR NOW"

    return {
        "sku": product.sku,
        "suggested_price": round(final_price, 2),
        "freshness": round(freshness, 3),
        "freshness_label": freshness_label,
        "days_left": round(days_left, 1),
        "expected_demand_units": round(demand_at_price, 1),
        "expected_daily_profit": round((final_price - product.cost) * demand_at_price, 2),
        "margin_pct": round((final_price - product.cost) / product.cost * 100, 1),
        "competitor_min": round(min(competitor_prices), 2) if competitor_prices else None,
        "note": freshness_label,
    }


# ─────────────────────────────────────────────
# 7. SIMULATION ENGINE
# ─────────────────────────────────────────────

def simulate_7_days(product: Product, competitor_prices: list[float], strategy: str = "engine") -> dict:
    """
    Run a 7-day simulation for one product under a given strategy.

    STRATEGIES:
        "engine"     — Our dynamic pricing engine
        "cost_plus"  — Naive: always sell at cost × 1.30
        "cheapest"   — Always match the cheapest competitor
    """
    total_profit = 0.0
    total_units_sold = 0.0
    total_waste = 0.0
    daily_log = []

    opening_stock = product.Q0 * product.shelf_life_days * 0.8  # Realistic starting stock
    stock = opening_stock

    for day in range(product.shelf_life_days):
        age = day  # Age in days (0 = just stocked)
        freshness = freshness_factor(age, product.shelf_life_days, product.k)

        # Determine price by strategy
        if strategy == "engine":
            result = suggest_price(product, age, competitor_prices)
            price = result["suggested_price"]

        elif strategy == "cost_plus":
            price = product.cost * 1.30  # Simple 30% markup, never changes

        elif strategy == "cheapest":
            comp_min = min(competitor_prices) if competitor_prices else product.p_ref
            price = max(comp_min, product.cost * product.margin_floor)

        # Demand realisation: add small randomness to simulate real market
        demand = expected_demand(price, product, freshness)
        # Slight noise: ±10%
        import random
        random.seed(day * 7 + hash(strategy) % 100)
        noise = random.uniform(0.90, 1.10)
        actual_demand = demand * noise

        # Units sold = min(demand, available stock)
        units_sold = min(actual_demand, stock)
        revenue = units_sold * price
        cost_of_goods = units_sold * product.cost
        profit = revenue - cost_of_goods

        stock -= units_sold

        # Track waste on last day
        if day == product.shelf_life_days - 1:
            waste = max(stock, 0)
            total_waste += waste
            stock = 0

        total_profit += profit
        total_units_sold += units_sold

        daily_log.append({
            "day": day + 1,
            "price": round(price, 2),
            "freshness": round(freshness, 3),
            "units_sold": round(units_sold, 1),
            "profit": round(profit, 2),
            "stock_remaining": round(stock, 1),
        })

    # Final waste: any remaining stock
    total_waste += max(stock, 0)

    return {
        "strategy": strategy,
        "total_profit": round(total_profit, 2),
        "total_units_sold": round(total_units_sold, 1),
        "waste_units": round(total_waste, 1),
        "waste_pct": round(total_waste / opening_stock * 100, 1),
        "avg_daily_profit": round(total_profit / product.shelf_life_days, 2),
        "daily_log": daily_log,
    }


# ─────────────────────────────────────────────
# 8. SMS FORMATTER  (African Market Feature)
# ─────────────────────────────────────────────

def format_sms(result: dict, currency: str = "UGX") -> str:
    """
    Format pricing recommendation as an SMS under 160 characters.

    DESIGN PRINCIPLE:
        Vendors in low-bandwidth markets use feature phones.
        160 chars = one SMS = one price recommendation.
        No app needed. No smartphone needed. No internet needed.
    """
    sku = result["sku"][:6].upper()
    price = int(result["suggested_price"])
    label = result.get("freshness_label", "OK")
    days = result.get("days_left", "?")
    margin = result.get("margin_pct", 0)

    msg = (
        f"PRICE:{sku} {currency}{price} [{label}] "
        f"{days}d left. Margin:{margin}%. "
        f"Reply HELP for options."
    )

    # Truncate to 160 if needed (shouldn't happen with this template)
    return msg[:160]


# ─────────────────────────────────────────────
# 9. REPORT GENERATOR
# ─────────────────────────────────────────────

def print_comparison_report(product: Product, competitor_prices: list[float]):
    """Run all 3 strategies and print a clean comparison table."""
    print("\n" + "="*60)
    print(f"  7-DAY SIMULATION REPORT: {product.sku}")
    print("="*60)
    print(f"  Cost/unit: {product.cost} | Shelf life: {product.shelf_life_days}d")
    print(f"  Ref price: {product.p_ref} | Competitors: {competitor_prices}")
    print("-"*60)

    strategies = ["engine", "cost_plus", "cheapest"]
    results = {}

    for strat in strategies:
        r = simulate_7_days(product, competitor_prices, strat)
        results[strat] = r

    # Header
    print(f"{'Strategy':<18} {'Profit':>10} {'Units':>8} {'Waste%':>8} {'Avg/Day':>10}")
    print("-"*60)

    for strat, r in results.items():
        label = {
            "engine": "Dynamic Engine",
            "cost_plus": "Cost+30% (Naive)",
            "cheapest": "Match Cheapest",
        }[strat]
        print(
            f"{label:<18} "
            f"{r['total_profit']:>10.2f} "
            f"{r['total_units_sold']:>8.1f} "
            f"{r['waste_pct']:>7.1f}% "
            f"{r['avg_daily_profit']:>10.2f}"
        )

    # Lift calculation
    engine_profit = results["engine"]["total_profit"]
    baseline_profit = results["cost_plus"]["total_profit"]
    if baseline_profit > 0:
        lift = (engine_profit - baseline_profit) / baseline_profit * 100
        print(f"\n  ✅ Engine vs Naive: {lift:+.1f}% profit improvement")
        print(f"  ✅ Waste reduction: "
              f"{results['cost_plus']['waste_pct'] - results['engine']['waste_pct']:.1f}% less waste")

    print("="*60)

    # Sample SMS output
    print("\n  📱 SAMPLE SMS OUTPUT (Day 3):")
    day3_result = suggest_price(product, 3.0, competitor_prices)
    sms = format_sms(day3_result)
    print(f"  [{len(sms)} chars] {sms}")
    print("="*60)

    return results


# ─────────────────────────────────────────────
# 10. CLI INTERFACE
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Perishable Goods Dynamic Pricing Engine — AIMS KTT Hackathon"
    )
    parser.add_argument("--sku", default="TOMATO", help="Product SKU")
    parser.add_argument("--cost", type=float, default=1000, help="Cost per unit (local currency)")
    parser.add_argument("--shelf-life", type=int, default=7, help="Shelf life in days")
    parser.add_argument("--ref-price", type=float, default=1800, help="Reference (full) price")
    parser.add_argument("--q0", type=float, default=50, help="Base daily demand at ref price")
    parser.add_argument("--alpha", type=float, default=1.5, help="Price sensitivity (demand model)")
    parser.add_argument("--age", type=float, default=0, help="Current age in days (for single query)")
    parser.add_argument("--competitors", type=float, nargs="*", default=[1600, 1700, 1900],
                        help="Competitor prices (space-separated)")
    parser.add_argument("--simulate", action="store_true", help="Run 7-day simulation")
    parser.add_argument("--currency", default="UGX", help="Currency label for SMS output")

    args = parser.parse_args()

    product = Product(
        sku=args.sku,
        cost=args.cost,
        shelf_life_days=args.shelf_life,
        p_ref=args.ref_price,
        Q0=args.q0,
        alpha=args.alpha,
    )

    if args.simulate:
        print_comparison_report(product, args.competitors)
    else:
        result = suggest_price(product, args.age, args.competitors)
        print("\n📦 PRICING RECOMMENDATION")
        print("-" * 40)
        for k, v in result.items():
            print(f"  {k:<25}: {v}")
        print("\n📱 SMS FORMAT:")
        print(f"  {format_sms(result, args.currency)}")


if __name__ == "__main__":
    main()
