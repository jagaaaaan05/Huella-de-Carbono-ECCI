"""Inventory calculation service for auditable, backend-first GHG computation."""

from dataclasses import dataclass

from carbon_footprint.models import (
    ElectricityConsumption,
    ExtinguisherRefill,
    FieldPracticeTrip,
    Flight,
    FuelConsumption,
    GroundTransportRecord,
    IndustrialProcessEmission,
    LodgingRecord,
    NaturalGasConsumption,
    PaperConsumption,
    RemovalRecord,
    VehicleFleetConsumption,
    WasteRecord,
    WaterConsumption,
)

from .emission_factors import factor_rows_to_payload, get_factor_rows
from .emission_sources import (
    SOURCE_ELECTRICITY,
    SOURCE_FUGITIVE,
    SOURCE_INDUSTRIAL,
    SOURCE_MOBILE,
    SOURCE_PAPER,
    SOURCE_REMOVALS,
    SOURCE_STATIONARY,
    SOURCE_TRANSPORT_LODGING,
    SOURCE_WASTE,
    SOURCE_WATER,
)
from .formulas_engine import aggregate_tco2e, gas_factor_to_tco2e, removals_to_negative
from .gases_catalog import DEFAULT_METHOD_PROFILE, resolve_gwp
from .uncertainty_module import inventory_uncertainty, source_uncertainty
from .units_catalog import convert_value, normalize_unit
from .validation_engine import validate_non_negative


@dataclass
class SourceCalcResult:
    source_code: str
    source_name: str
    total_tco2e: float
    uncertainty_pct: float
    traces: list[dict]
    warnings: list[str]


def _apply_campus_filter(queryset, campus_id: int | None):
    return queryset.filter(campus_id=campus_id) if campus_id else queryset


def _calc_from_factor_rows(
    source_code: str,
    activity_value: float,
    activity_unit: str,
    factor_rows_payload: list[dict],
    method_profile: str,
    formula_code: str = "gas_factor_to_tco2e",
    activity_variable: str = "activity",
    factor_selection_policy: str = "auto",
):
    contributions = []
    traces = []
    factor_uncs = []
    warnings = []

    for row in factor_rows_payload:
        factor_unit = row["unit"]
        if not factor_unit:
            warnings.append("Factor without normalized unit. Row skipped.")
            continue

        try:
            normalized_activity = convert_value(activity_value, activity_unit, factor_unit)
        except ValueError as exc:
            warnings.append(str(exc))
            continue

        gas = row["gas"] or "CO2"
        gwp = resolve_gwp(
            gas=gas,
            source_code=source_code,
            method_profile=method_profile,
            explicit_gwp=row.get("gwp_100yr"),
        )
        contribution = gas_factor_to_tco2e(normalized_activity, row["factor_value"], gwp)
        contributions.append(contribution)
        factor_uncs.append(row.get("uncertainty_pct") or 0.0)

        traces.append(
            {
                "formula": {
                    "code": formula_code,
                    "method_profile": method_profile,
                    "activity_variable": activity_variable,
                    "factor_selection_policy": factor_selection_policy,
                },
                "gas": gas,
                "gwp": gwp,
                "activity_input": {
                    "value": activity_value,
                    "unit": activity_unit,
                    "normalized_to_factor_unit": normalized_activity,
                    "factor_unit": factor_unit,
                },
                "factor": {
                    "id": row["id"],
                    "agent": row["agent"],
                    "value": row["factor_value"],
                    "unit": row["raw_unit"],
                    "source_ref": row["source_ref"],
                    "year_applic": row["year_applic"],
                    "uncertainty_pct": row["uncertainty_pct"],
                },
                "result_tco2e": contribution,
            }
        )

    avg_factor_unc = (sum(factor_uncs) / len(factor_uncs)) if factor_uncs else 0.0
    return aggregate_tco2e(contributions), traces, warnings, avg_factor_unc


def _record_emission_factor_payload(record):
    emission_factor = getattr(record, "emission_factor", None)
    if not emission_factor:
        return None
    return {
        "id": emission_factor.id,
        "agent": emission_factor.agent,
        "gas": emission_factor.gas,
        "factor_value": emission_factor.factor_value,
        "unit": normalize_unit(emission_factor.unit),
        "raw_unit": emission_factor.unit,
        "gwp_100yr": emission_factor.gwp_100yr,
        "source_ref": emission_factor.source_ref,
        "year_applic": emission_factor.year_applic,
        "uncertainty_pct": emission_factor.uncertainty_pct,
    }


def _resolve_rows_for_record(record, source_code: str, year: int, hints: list[str]):
    explicit = _record_emission_factor_payload(record)
    if explicit:
        return [explicit], "record_explicit_factor"
    return _resolve_rows_with_fallback(source_code=source_code, year=year, hints=hints), "source_catalog_auto"


def _resolve_rows_with_fallback(source_code: str, year: int, hints: list[str]):
    for hint in hints:
        rows = get_factor_rows(source_code=source_code, year=year, agent_hint=hint)
        if rows.exists():
            return factor_rows_to_payload(rows)
    rows = get_factor_rows(source_code=source_code, year=year)
    return factor_rows_to_payload(rows)


def _calculate_electricity(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        ElectricityConsumption.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        record_warnings = validate_non_negative(record.kwh, "Electricity kWh")
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_ELECTRICITY,
            year=record.period.year,
            hints=["Electricidad", "UPME", "XM"],
        )
        if not rows:
            warnings.append("No emission factor found for electricity.")
            continue

        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_ELECTRICITY,
            activity_value=record.kwh,
            activity_unit="kwh",
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="electricity_activity_x_factor",
            activity_variable="consumo_kwh",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(1.0, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "electricity", "items": row_traces})
        warnings.extend(record_warnings)
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_ELECTRICITY,
        source_name="Electricidad",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_stationary(period_id: int, campus_id: int | None, method_profile: str):
    gas_records = _apply_campus_filter(
        NaturalGasConsumption.objects.filter(period_id=period_id).select_related("period", "fuel_type", "emission_factor"),
        campus_id,
    )
    fuel_records = _apply_campus_filter(
        FuelConsumption.objects.filter(period_id=period_id).select_related("period", "fuel_type", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in gas_records:
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_STATIONARY,
            year=record.period.year,
            hints=[record.fuel_type.description, "Gas natural", record.fuel_type.fuel_code],
        )
        if not rows:
            warnings.append("No emission factor found for natural gas consumption.")
            continue
        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_STATIONARY,
            activity_value=record.m3,
            activity_unit="m3",
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="stationary_combustion",
            activity_variable="m3",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(3.0, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "natural_gas", "items": row_traces})
        warnings.extend(row_warnings)

    for record in fuel_records:
        unit = normalize_unit(record.unit) or "l"
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_STATIONARY,
            year=record.period.year,
            hints=[record.fuel_type.description, record.fuel_type.fuel_code],
        )
        if not rows:
            warnings.append("No emission factor found for stationary fuel consumption.")
            continue
        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_STATIONARY,
            activity_value=record.amount,
            activity_unit=unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="stationary_combustion",
            activity_variable="amount",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(0.5, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "fuel_stationary", "items": row_traces})
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_STATIONARY,
        source_name="Combustion estacionaria",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_mobile(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        VehicleFleetConsumption.objects.filter(period_id=period_id).select_related("period", "fuel_type", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        unit = normalize_unit(record.unit) or "l"
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_MOBILE,
            year=record.period.year,
            hints=[record.fuel_type.description, record.fuel_type.fuel_code],
        )
        if not rows:
            warnings.append("No emission factor found for mobile fuel consumption.")
            continue
        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_MOBILE,
            activity_value=record.amount,
            activity_unit=unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="mobile_combustion",
            activity_variable="amount",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(0.5, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "mobile_fleet", "items": row_traces})
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_MOBILE,
        source_name="Combustion movil",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_fugitive(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        ExtinguisherRefill.objects.filter(period_id=period_id).select_related("ext_type", "period", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        activity_unit = normalize_unit(record.unit) or "kg"
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_FUGITIVE,
            year=record.period.year,
            hints=[record.ext_type.description, record.ext_type.ext_code],
        )

        # Fallback to extinguisher catalog GWP if no factor row exists.
        if not rows:
            gwp = record.ext_type.gwp_100yr or resolve_gwp(
                gas=record.ext_type.ext_code,
                source_code=SOURCE_FUGITIVE,
                method_profile=method_profile,
            )
            contribution = gas_factor_to_tco2e(record.amount, 1.0, gwp)
            traces.append(
                {
                    "record_id": record.id,
                    "record_type": "extinguisher_refill",
                    "items": [
                        {
                            "gas": record.ext_type.ext_code,
                            "gwp": gwp,
                            "formula": {
                                "code": "fugitive_mass_x_gwp",
                                "method_profile": method_profile,
                                "activity_variable": "amount",
                                "factor_selection_policy": "extinguisher_type_gwp_fallback",
                            },
                            "activity_input": {
                                "value": record.amount,
                                "unit": activity_unit,
                                "normalized_to_factor_unit": record.amount,
                                "factor_unit": "kg",
                            },
                            "factor": {
                                "id": None,
                                "agent": record.ext_type.description,
                                "value": 1.0,
                                "unit": "kg",
                                "source_ref": "extinguisher_type_gwp_fallback",
                                "year_applic": record.period.year,
                                "uncertainty_pct": None,
                            },
                            "result_tco2e": contribution,
                        }
                    ],
                }
            )
            total += contribution
            weighted.append((contribution, source_uncertainty(0.1, 0.0)))
            continue

        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_FUGITIVE,
            activity_value=record.amount,
            activity_unit=activity_unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="fugitive_mass_x_gwp",
            activity_variable="amount",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(0.1, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "extinguisher_refill", "items": row_traces})
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_FUGITIVE,
        source_name="Emisiones fugitivas",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_waste(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        WasteRecord.objects.filter(period_id=period_id).select_related("period", "waste_type", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        unit = normalize_unit(record.unit) or "kg"
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_WASTE,
            year=record.period.year,
            hints=[record.waste_type.treatment or "", record.waste_type.description],
        )
        if not rows:
            warnings.append("No emission factor found for waste record.")
            continue

        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_WASTE,
            activity_value=record.amount,
            activity_unit=unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="waste_activity_x_factor",
            activity_variable="amount",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(0.1, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "waste", "items": row_traces})
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_WASTE,
        source_name="Residuos",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_transport(period_id: int, campus_id: int | None, method_profile: str):
    practice_records = _apply_campus_filter(
        FieldPracticeTrip.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    ground_records = _apply_campus_filter(
        GroundTransportRecord.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    lodging_records = _apply_campus_filter(
        LodgingRecord.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    flight_records = Flight.objects.filter(period_id=period_id).select_related("period", "emission_factor")
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    def calc_generic(record, record_type: str, value: float, unit: str, year: int, hints: list[str], activity_variable: str):
        nonlocal total
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_TRANSPORT_LODGING,
            year=year,
            hints=hints,
        )
        if not rows:
            warnings.append(f"No emission factor found for {record_type} record.")
            return
        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_TRANSPORT_LODGING,
            activity_value=value,
            activity_unit=unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="transport_or_lodging_activity_x_factor",
            activity_variable=activity_variable,
            factor_selection_policy=factor_policy,
        )
        total += calc
        weighted.append((calc, source_uncertainty(0.5, avg_factor_unc)))
        traces.append({"record_id": record.id, "record_type": record_type, "items": row_traces})
        warnings.extend(row_warnings)

    for record in practice_records:
        calc_generic(
            record=record,
            record_type="field_practice",
            value=record.total_km,
            unit="km",
            year=record.period.year,
            hints=["Transporte", "practicas"],
            activity_variable="total_km",
        )

    for record in ground_records:
        calc_generic(
            record=record,
            record_type="ground_transport",
            value=record.amount,
            unit=record.unit,
            year=record.period.year,
            hints=[record.description, "Transporte terrestre"],
            activity_variable="amount",
        )

    for record in lodging_records:
        calc_generic(
            record=record,
            record_type="lodging",
            value=record.nights,
            unit="nights",
            year=record.period.year,
            hints=["Hospedaje", record.description],
            activity_variable="nights",
        )

    for record in flight_records:
        pax_km = (record.km or 0.0) * record.passengers
        calc_generic(
            record=record,
            record_type="flight",
            value=pax_km,
            unit="pax-km",
            year=record.period.year,
            hints=["Vuelo", "Aéreo", "ICAO", record.description or ""],
            activity_variable="pax_km",
        )

    return SourceCalcResult(
        source_code=SOURCE_TRANSPORT_LODGING,
        source_name="Transporte y hospedaje",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_paper(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        PaperConsumption.objects.filter(period_id=period_id).select_related("period", "size", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        paper_kg = record.reams * record.size.kg_per_ream
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_PAPER,
            year=record.period.year,
            hints=[record.size.size, "Papel"],
        )
        if not rows:
            warnings.append("No emission factor found for paper consumption.")
            continue

        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_PAPER,
            activity_value=paper_kg,
            activity_unit="kg",
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="paper_consumption",
            activity_variable="paper_kg",
            factor_selection_policy=factor_policy,
        )
        total += calc
        weighted.append((calc, source_uncertainty(10.0, avg_factor_unc)))
        traces.append({"record_id": record.id, "record_type": "paper", "items": row_traces})
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_PAPER,
        source_name="Consumo de papel",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_industrial(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        IndustrialProcessEmission.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        unit = normalize_unit(record.unit) or "kg"
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_INDUSTRIAL,
            year=record.period.year,
            hints=[record.process_type, record.description],
        )
        if not rows:
            warnings.append(f"No emission factor found for industrial process '{record.description}'.")
            continue
        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_INDUSTRIAL,
            activity_value=record.activity,
            activity_unit=unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="industrial_process_activity_x_factor",
            activity_variable="activity",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(0.5, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "industrial_process", "items": row_traces})
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_INDUSTRIAL,
        source_name="Procesos industriales",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_water(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        WaterConsumption.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total = 0.0
    weighted = []

    for record in records:
        record_warnings = validate_non_negative(record.m3, "Water m3")
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_WATER,
            year=record.period.year,
            hints=["Agua", "Agua potable", "EAAB"],
        )
        if not rows:
            warnings.append("No emission factor found for water consumption.")
            continue
        calc, row_traces, row_warnings, avg_factor_unc = _calc_from_factor_rows(
            source_code=SOURCE_WATER,
            activity_value=record.m3,
            activity_unit="m3",
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="water_activity_x_factor",
            activity_variable="m3",
            factor_selection_policy=factor_policy,
        )
        total += calc
        source_unc = source_uncertainty(5.0, avg_factor_unc)
        weighted.append((calc, source_unc))
        traces.append({"record_id": record.id, "record_type": "water", "items": row_traces})
        warnings.extend(record_warnings)
        warnings.extend(row_warnings)

    return SourceCalcResult(
        source_code=SOURCE_WATER,
        source_name="Consumo de agua potable",
        total_tco2e=total,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def _calculate_removals(period_id: int, campus_id: int | None):
    records = _apply_campus_filter(
        RemovalRecord.objects.filter(period_id=period_id),
        campus_id,
    )
    traces = []
    warnings = []
    total_negative = 0.0
    weighted = []

    for record in records:
        warnings.extend(validate_non_negative(record.tco2e, "Removal tCO2e"))
        contribution = removals_to_negative(record.tco2e)
        total_negative += contribution
        traces.append(
            {
                "record_id": record.id,
                "record_type": "removal",
                "items": [
                    {
                        "formula": "removals_to_negative",
                        "input_tco2e": record.tco2e,
                        "result_tco2e": contribution,
                        "rtype": record.rtype,
                    }
                ],
            }
        )
        weighted.append((abs(contribution), source_uncertainty(0.1, 0.0)))

    return SourceCalcResult(
        source_code=SOURCE_REMOVALS,
        source_name="Remociones",
        total_tco2e=total_negative,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
    )


def calculate_inventory_run(
    period_id: int,
    campus_id: int | None = None,
    method_profile: str = DEFAULT_METHOD_PROFILE,
    include_traces: bool = True,
):
    """Run auditable inventory calculation for a period and optional campus."""
    source_results = [
        _calculate_stationary(period_id, campus_id, method_profile),
        _calculate_mobile(period_id, campus_id, method_profile),
        _calculate_industrial(period_id, campus_id, method_profile),
        _calculate_fugitive(period_id, campus_id, method_profile),
        _calculate_electricity(period_id, campus_id, method_profile),
        _calculate_transport(period_id, campus_id, method_profile),
        _calculate_paper(period_id, campus_id, method_profile),
        _calculate_waste(period_id, campus_id, method_profile),
        _calculate_water(period_id, campus_id, method_profile),
        _calculate_removals(period_id, campus_id),
    ]

    gross_total = sum(result.total_tco2e for result in source_results if result.source_code != SOURCE_REMOVALS)
    removals_total = sum(result.total_tco2e for result in source_results if result.source_code == SOURCE_REMOVALS)
    net_total = gross_total + removals_total

    weighted_unc = [
        (abs(result.total_tco2e), result.uncertainty_pct)
        for result in source_results
        if result.total_tco2e != 0
    ]
    run_uncertainty = inventory_uncertainty(weighted_unc)

    return {
        "method_profile": method_profile,
        "period_id": period_id,
        "campus_id": campus_id,
        "totals": {
            "gross_tco2e": gross_total,
            "removals_tco2e": removals_total,
            "net_tco2e": net_total,
            "uncertainty_pct": run_uncertainty,
        },
        "sources": [
            {
                "source_code": result.source_code,
                "source_name": result.source_name,
                "total_tco2e": result.total_tco2e,
                "uncertainty_pct": result.uncertainty_pct,
                "warnings": result.warnings,
                "traces": result.traces if include_traces else [],
            }
            for result in source_results
        ],
        "warnings": [warning for result in source_results for warning in result.warnings],
    }
