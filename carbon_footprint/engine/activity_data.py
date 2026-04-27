"""Activity data structures used by the calculation engine."""

from dataclasses import dataclass


@dataclass
class ActivityDatum:
    record_id: int
    source_code: str
    activity_value: float
    activity_unit: str
    period_year: int
    campus_id: int | None = None
    metadata: dict | None = None


@dataclass
class ActivityTrace:
    record_id: int
    record_type: str
    details: dict
