"""Emission factor selection and normalization logic."""

from carbon_footprint.models import EmissionFactor, EmissionSource

from .units_catalog import normalize_unit


def _filter_by_year(qs, year: int | None):
    if not year:
        return qs
    year_qs = qs.filter(year_applic=year)
    return year_qs if year_qs.exists() else qs


def _filter_by_agent(qs, agent_hint: str | None):
    if not agent_hint:
        return qs
    hinted = qs.filter(agent__icontains=agent_hint)
    return hinted if hinted.exists() else qs


def get_factor_rows(
    source_code: str,
    year: int | None = None,
    agent_hint: str | None = None,
):
    source = EmissionSource.objects.filter(code=source_code).first()
    if not source:
        return EmissionFactor.objects.none()

    qs = EmissionFactor.objects.filter(source=source)
    qs = _filter_by_year(qs, year)
    qs = _filter_by_agent(qs, agent_hint)
    return qs


def factor_rows_to_payload(factor_rows):
    return [
        {
            "id": factor.id,
            "agent": factor.agent,
            "gas": factor.gas,
            "factor_value": factor.factor_value,
            "unit": normalize_unit(factor.unit),
            "raw_unit": factor.unit,
            "gwp_100yr": factor.gwp_100yr,
            "source_ref": factor.source_ref,
            "year_applic": factor.year_applic,
            "uncertainty_pct": factor.uncertainty_pct,
        }
        for factor in factor_rows
    ]
