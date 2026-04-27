"""Uncertainty calculations for source-level and inventory-level results."""

from math import sqrt


def source_uncertainty(activity_unc_pct: float, factor_unc_pct: float) -> float:
    """Combined source uncertainty using root-sum-square method.

    Returns a percentage value.
    """
    return sqrt((activity_unc_pct or 0.0) ** 2 + (factor_unc_pct or 0.0) ** 2)


def inventory_uncertainty(weighted_items: list[tuple[float, float]]) -> float:
    """Aggregate uncertainty weighted by emissions.

    weighted_items: list of (emission_tco2e, uncertainty_pct).
    """
    total = sum(max(item[0], 0.0) for item in weighted_items)
    if total <= 0:
        return 0.0
    quadratic = sum(((e * (u / 100.0)) ** 2) for e, u in weighted_items if e > 0)
    return (sqrt(quadratic) / total) * 100.0
