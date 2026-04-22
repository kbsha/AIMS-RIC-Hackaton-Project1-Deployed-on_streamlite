"""
demo.py — Quick demo for hackathon judges / live defense
Runs everything in < 5 seconds. All output is self-explanatory.
"""

from pricer import (
    Product, suggest_price, simulate_7_days,
    format_sms, print_comparison_report, freshness_factor
)


def demo_single_price():
    """Show how one pricing call works, step by step."""
    print("\n" + "━"*60)
    print("  DEMO 1: Single Price Recommendation")
    print("━"*60)

    tomato = Product(
        sku="TOMATO-A",
        cost=1000,
        shelf_life_days=7,
        p_ref=1800,
        Q0=50,
        alpha=1.5,
    )

    competitors = [1600, 1700, 1900]

    for age in [0, 2, 3.5, 5, 6]:
        result = suggest_price(tomato, age, competitors)
        freshness = result["freshness"]
        price = result["suggested_price"]
        label = result["freshness_label"]
        print(f"  Day {age:>3.1f} | Freshness: {freshness:.3f} ({label:<10}) "
              f"→ Price: {price:>7.0f} UGX | "
              f"Margin: {result['margin_pct']:>5.1f}%")


def demo_freshness_table():
    """Show the sigmoid freshness curve — great for interview visuals."""
    print("\n" + "━"*60)
    print("  DEMO 2: Freshness Curve (why sigmoid beats linear)")
    print("━"*60)
    print(f"  {'Day':<6} {'Sigmoid':>10} {'Linear':>10} {'Difference':>12}")
    print("  " + "-"*42)

    shelf = 7
    for day in range(8):
        sigmoid = freshness_factor(day, shelf)
        linear = max(0, 1 - day / shelf)
        diff = sigmoid - linear
        bar = "█" * int(sigmoid * 20)
        print(f"  {day:<6} {sigmoid:>10.3f} {linear:>10.3f} {diff:>+12.3f}  {bar}")


def demo_what_at_half_life():
    """Interview: what happens at half shelf life?"""
    print("\n" + "━"*60)
    print("  DEMO 3: The Half-Life Moment (key interview talking point)")
    print("━"*60)

    tomato = Product(
        sku="TOMATO-A", cost=1000, shelf_life_days=7,
        p_ref=1800, Q0=50, alpha=1.5,
    )
    half_life = tomato.shelf_life_days / 2  # Day 3.5

    fresh_result = suggest_price(tomato, 0, [1600, 1700])
    mid_result   = suggest_price(tomato, half_life, [1600, 1700])
    late_result  = suggest_price(tomato, 6, [1600, 1700])

    print(f"  Day 0   (fresh):     {fresh_result['suggested_price']:>7.0f} UGX — {fresh_result['freshness_label']}")
    print(f"  Day 3.5 (half-life): {mid_result['suggested_price']:>7.0f} UGX — {mid_result['freshness_label']}")
    print(f"  Day 6   (near-exp):  {late_result['suggested_price']:>7.0f} UGX — {late_result['freshness_label']}")
    print()
    price_drop = (fresh_result['suggested_price'] - mid_result['suggested_price'])
    print(f"  → At half-life, price drops {price_drop:.0f} UGX ({price_drop/fresh_result['suggested_price']*100:.0f}%)")
    print("  → This is the inflection point — aggressive discounting begins")
    print("  → Exactly where the sigmoid inflects: steepest rate of change")


def demo_sms():
    """Show SMS output for different freshness levels."""
    print("\n" + "━"*60)
    print("  DEMO 4: SMS Output (African Market Feature)")
    print("━"*60)

    tomato = Product(
        sku="TOM", cost=1000, shelf_life_days=7,
        p_ref=1800, Q0=50, alpha=1.5,
    )

    for age in [0, 3, 5, 6]:
        result = suggest_price(tomato, age, [1600, 1700, 1900])
        sms = format_sms(result, "UGX")
        print(f"  Day {age}: [{len(sms):>3}chr] {sms}")


def demo_simulation():
    """Full 7-day comparison across 3 strategies."""
    tomato = Product(
        sku="TOMATO", cost=1000, shelf_life_days=7,
        p_ref=1800, Q0=50, alpha=1.5,
    )
    print_comparison_report(tomato, [1600, 1700, 1900])

    # Second product: bread (shorter shelf life, different dynamics)
    bread = Product(
        sku="BREAD", cost=2500, shelf_life_days=3,
        p_ref=4000, Q0=30, alpha=2.0,
        k=10.0  # Sharper cliff for bread
    )
    print_comparison_report(bread, [3800, 3900])


if __name__ == "__main__":
    demo_single_price()
    demo_freshness_table()
    demo_what_at_half_life()
    demo_sms()
    demo_simulation()

    print("\n✅ All demos complete. Ready for live defense.")
