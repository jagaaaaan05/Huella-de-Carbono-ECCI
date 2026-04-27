"""Validation helpers for scientific consistency and data quality."""

from .units_catalog import normalize_unit


def validate_non_negative(value: float, label: str) -> list[str]:
    if value < 0:
        return [f"{label} must be non-negative."]
    return []


def validate_required(value, label: str) -> list[str]:
    if value is None:
        return [f"{label} is required."]
    return []


def validate_unit_known(unit: str | None, label: str) -> list[str]:
    if normalize_unit(unit) is None:
        return [f"{label} has an empty or unknown unit."]
    return []
