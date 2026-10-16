"""Tools: invoice arithmetic and amount-outlier checks."""
from shared.schemas import Signal

OUTLIER_RATIO = 1.8


def check_totals(claim) -> list[Signal]:
    total = round(sum(i.amount for i in claim.line_items), 2)
    tol = max(5.0, 0.02 * total)
    diff = round(claim.amount_claimed - total, 2)
    if abs(diff) > tol:
        return [Signal(type="arithmetic_mismatch", severity="high", weight=30,
                       evidence=f"Claimed total {claim.amount_claimed:,.2f} does not match the itemised lines ({total:,.2f}); difference {diff:,.2f}.")]
    return []


def check_outlier(repo, claim) -> list[Signal]:
    med = repo.median_amount(claim.damage_type)
    ratio = claim.amount_claimed / med if med else 1.0
    if ratio >= OUTLIER_RATIO:
        return [Signal(type="amount_outlier", severity="medium", weight=20,
                       evidence=f"Claimed amount is {ratio:.1f}x the typical {claim.damage_type} claim ({med:,.0f}).")]
    return []
