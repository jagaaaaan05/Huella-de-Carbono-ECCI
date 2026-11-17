"""Emission factor selection and normalization logic.

A factor "agent" (e.g. 'Diésel / ACPM') may have one row per gas (CO2, CH4, N2O,
CO2_BIO). Selection always resolves to a single agent and a single year so that
alternative agents of the same source are never summed together.
"""

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


def _best_year_rows(agent_qs, year: int | None):
    """Rows of one agent for the closest applicable year (exact, latest previous, undated, earliest)."""
    years = sorted({y for y in agent_qs.values_list("year_applic", flat=True) if y is not None})
    if year and year in years:
        return agent_qs.filter(year_applic=year)
    previous = [y for y in years if year and y < year]
    if previous:
        return agent_qs.filter(year_applic=previous[-1])
    undated = agent_qs.filter(year_applic__isnull=True)
    if undated.exists() or not years:
        return undated
    return agent_qs.filter(year_applic=years[0])


def select_agent_rows(source_code: str, year: int | None, hints: list[str]):
    """Return (rows, matched_hint) for the first hint matching an agent of the source.

    Exact agent names win over partial matches. Without a matching hint, the source's
    rows are used only when the source has a single agent; otherwise nothing is returned.
    """
    qs = EmissionFactor.objects.filter(source__code=source_code).order_by("id")
    for hint in hints:
        hint = (hint or "").strip()
        if not hint:
            continue
        match = qs.filter(agent__iexact=hint).first() or qs.filter(agent__icontains=hint).first()
        if match:
            return _best_year_rows(qs.filter(agent=match.agent), year), hint

    agents = list(qs.values_list("agent", flat=True).distinct())
    if len(agents) == 1:
        return _best_year_rows(qs.filter(agent=agents[0]), year), None
    return EmissionFactor.objects.none(), None


def sibling_gas_rows(emission_factor):
    """All gas rows sharing the agent, source and year of an explicitly chosen factor."""
    return EmissionFactor.objects.filter(
        source_id=emission_factor.source_id,
        agent=emission_factor.agent,
        year_applic=emission_factor.year_applic,
    ).order_by("id")


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
