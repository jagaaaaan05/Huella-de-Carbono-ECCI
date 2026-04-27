"""Formal equations used by the backend calculation engine."""


def gas_factor_to_tco2e(activity_value: float, factor_value: float, gwp: float) -> float:
    """Convert one gas contribution to tCO2e.

    Assumes factor is expressed as kg gas / activity unit.
    """
    return (activity_value * factor_value * gwp) / 1000.0


def aggregate_tco2e(contributions: list[float]) -> float:
    return float(sum(contributions))


def removals_to_negative(removal_tco2e: float) -> float:
    return -abs(float(removal_tco2e))
