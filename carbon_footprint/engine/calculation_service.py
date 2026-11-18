"""Inventory calculation service for auditable, backend-first GHG computation.

Equations follow the ECCI corporate carbon footprint tool (Excel, 2024) and the
2022 inventory report: per-gas emissions times AR6 GWP, biogenic CO2 from the
10 % biofuel blend reported apart, and removals subtracted from the gross total.
"""

from dataclasses import dataclass, field
from math import sqrt

from carbon_footprint.models import (
    ElectricityConsumption,
    ExtinguisherRefill,
    FieldPracticeTrip,
    Flight,
    FuelConsumption,
    GroundTransportRecord,
    IndustrialProcessEmission,
    LodgingRecord,
    LubricantConsumption,
    NaturalGasConsumption,
    PaperConsumption,
    RemovalRecord,
    VehicleFleetConsumption,
    WasteRecord,
    WaterConsumption,
)

from .emission_factors import factor_rows_to_payload, select_agent_rows, sibling_gas_rows
from .emission_sources import (
    SOURCE_ELECTRICITY,
    SOURCE_FUGITIVE,
    SOURCE_INDUSTRIAL,
    SOURCE_LUBRICANTS,
    SOURCE_MOBILE,
    SOURCE_PAPER,
    SOURCE_REMOVALS,
    SOURCE_STATIONARY,
    SOURCE_TRANSPORT_LODGING,
    SOURCE_WASTE,
    SOURCE_WATER,
)
from .formulas_engine import gas_factor_to_tco2e, removals_to_negative
from .gases_catalog import DEFAULT_METHOD_PROFILE, is_biogenic, resolve_gwp
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
    biogenic_tco2e: float = 0.0
    by_gas: dict = field(default_factory=dict)


@dataclass
class RowsCalc:
    """Result of applying one agent's gas rows to one activity value."""
    total_tco2e: float
    biogenic_tco2e: float
    uncertainty_pct: float
    traces: list[dict]
    warnings: list[str]
    by_gas: dict


class SourceAccumulator:
    """Collects per-record results of one emission source."""

    def __init__(self, source_code: str, source_name: str):
        self.source_code = source_code
        self.source_name = source_name
        self.total = 0.0
        self.biogenic = 0.0
        self.weighted: list[tuple[float, float]] = []
        self.traces: list[dict] = []
        self.warnings: list[str] = []
        self.by_gas: dict[str, float] = {}

    def add(self, record_id, record_type: str, calc: RowsCalc):
        self.total += calc.total_tco2e
        self.biogenic += calc.biogenic_tco2e
        self.weighted.append((calc.total_tco2e, calc.uncertainty_pct))
        self.traces.append({"record_id": record_id, "record_type": record_type, "items": calc.traces})
        self.warnings.extend(calc.warnings)
        for gas, value in calc.by_gas.items():
            self.by_gas[gas] = self.by_gas.get(gas, 0.0) + value

    def result(self) -> SourceCalcResult:
        return SourceCalcResult(
            source_code=self.source_code,
            source_name=self.source_name,
            total_tco2e=self.total,
            uncertainty_pct=inventory_uncertainty(self.weighted),
            traces=self.traces,
            warnings=self.warnings,
            biogenic_tco2e=self.biogenic,
            by_gas=self.by_gas,
        )


def _apply_campus_filter(queryset, campus_id: int | None):
    return queryset.filter(campus_id=campus_id) if campus_id else queryset


def _keyword_hints(text: str | None, keywords: list[tuple[str, str]]) -> list[str]:
    """Map words found in a free-text description to catalog agent names."""
    lowered = (text or "").lower()
    return [agent for word, agent in keywords if word in lowered]


def _calc_from_factor_rows(
    source_code: str,
    activity_value: float,
    activity_unit: str,
    factor_rows_payload: list[dict],
    method_profile: str,
    formula_code: str = "gas_factor_to_tco2e",
    activity_variable: str = "activity",
    factor_selection_policy: str = "auto",
    activity_unc_pct: float = 0.0,
) -> RowsCalc:
    total = 0.0
    biogenic = 0.0
    traces = []
    warnings = []
    by_gas: dict[str, float] = {}
    weighted = []

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
        biogenic_row = is_biogenic(gas)
        if biogenic_row:
            biogenic += contribution
        else:
            total += contribution
            # Excel: per-gas RSS of activity and factor uncertainty, weighted by emissions.
            weighted.append((contribution, source_uncertainty(activity_unc_pct, row.get("uncertainty_pct") or 0.0)))
        by_gas[gas] = by_gas.get(gas, 0.0) + contribution

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
                "biogenic": biogenic_row,
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

    return RowsCalc(
        total_tco2e=total,
        biogenic_tco2e=biogenic,
        uncertainty_pct=inventory_uncertainty(weighted),
        traces=traces,
        warnings=warnings,
        by_gas=by_gas,
    )


def _resolve_rows_for_record(record, source_code: str, year: int, hints: list[str]):
    explicit = getattr(record, "emission_factor", None)
    if explicit:
        return factor_rows_to_payload(sibling_gas_rows(explicit)), "record_explicit_factor"
    rows, matched_hint = select_agent_rows(source_code=source_code, year=year, hints=hints)
    policy = "source_catalog_hint" if matched_hint else "source_catalog_single_agent"
    return factor_rows_to_payload(rows), policy


def _calc_record(
    acc: SourceAccumulator,
    record,
    record_type: str,
    value: float,
    unit: str,
    year: int,
    hints: list[str],
    method_profile: str,
    formula_code: str,
    activity_variable: str,
    activity_unc_pct: float,
):
    rows, factor_policy = _resolve_rows_for_record(record, acc.source_code, year, hints)
    if not rows:
        acc.warnings.append(f"No emission factor found for {record_type} record {record.id}.")
        return
    calc = _calc_from_factor_rows(
        source_code=acc.source_code,
        activity_value=value,
        activity_unit=unit,
        factor_rows_payload=rows,
        method_profile=method_profile,
        formula_code=formula_code,
        activity_variable=activity_variable,
        factor_selection_policy=factor_policy,
        activity_unc_pct=activity_unc_pct,
    )
    acc.add(record.id, record_type, calc)


def _calculate_electricity(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        ElectricityConsumption.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_ELECTRICITY, "Electricidad")
    for record in records:
        acc.warnings.extend(validate_non_negative(record.kwh, "Electricity kWh"))
        _calc_record(
            acc, record, "electricity", record.kwh, "kwh", record.period.year,
            hints=["Electricidad", "UPME", "XM"],
            method_profile=method_profile,
            formula_code="electricity_activity_x_factor",
            activity_variable="consumo_kwh",
            activity_unc_pct=1.0,
        )
    return acc.result()


def _calculate_stationary(period_id: int, campus_id: int | None, method_profile: str):
    gas_records = _apply_campus_filter(
        NaturalGasConsumption.objects.filter(period_id=period_id).select_related("period", "fuel_type", "emission_factor"),
        campus_id,
    )
    fuel_records = _apply_campus_filter(
        FuelConsumption.objects.filter(period_id=period_id).select_related("period", "fuel_type", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_STATIONARY, "Combustion estacionaria")

    for record in gas_records:
        _calc_record(
            acc, record, "natural_gas", record.m3, "m3", record.period.year,
            hints=["Gas natural", record.fuel_type.description, record.fuel_type.fuel_code],
            method_profile=method_profile,
            formula_code="stationary_combustion",
            activity_variable="m3",
            activity_unc_pct=3.0,
        )

    for record in fuel_records:
        _calc_record(
            acc, record, "fuel_stationary", record.amount, normalize_unit(record.unit) or "gal", record.period.year,
            hints=[record.fuel_type.description, record.fuel_type.fuel_code],
            method_profile=method_profile,
            formula_code="stationary_combustion",
            activity_variable="amount",
            activity_unc_pct=0.5,
        )

    return acc.result()


def _calculate_mobile(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        VehicleFleetConsumption.objects.filter(period_id=period_id).select_related("period", "fuel_type", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_MOBILE, "Combustion movil")
    for record in records:
        _calc_record(
            acc, record, "mobile_fleet", record.amount, normalize_unit(record.unit) or "gal", record.period.year,
            hints=[record.fuel_type.description, record.fuel_type.fuel_code],
            method_profile=method_profile,
            formula_code="mobile_combustion",
            activity_variable="amount",
            activity_unc_pct=0.5,
        )
    return acc.result()


def _calculate_industrial(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        IndustrialProcessEmission.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_INDUSTRIAL, "Procesos industriales")
    for record in records:
        _calc_record(
            acc, record, "industrial_process", record.activity, normalize_unit(record.unit) or "t", record.period.year,
            hints=[record.process_type, record.description],
            method_profile=method_profile,
            formula_code="industrial_process_q_x_factor",
            activity_variable="activity",
            activity_unc_pct=1.0,
        )
    return acc.result()


def _calculate_lubricants(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        LubricantConsumption.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_LUBRICANTS, "Lubricantes")
    for record in records:
        hints = _keyword_hints(record.description, [("grasa", "Grasa lubricante"), ("aceite", "Aceites lubricantes")])
        _calc_record(
            acc, record, "lubricant", record.amount, normalize_unit(record.unit) or "gal", record.period.year,
            hints=hints + [record.description, "Aceites lubricantes"],
            method_profile=method_profile,
            formula_code="lubricant_amount_x_factor",
            activity_variable="amount",
            activity_unc_pct=1.0,
        )
    return acc.result()


def _calculate_fugitive(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        ExtinguisherRefill.objects.filter(period_id=period_id).select_related("ext_type", "period", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_FUGITIVE, "Emisiones fugitivas")

    for record in records:
        activity_unit = normalize_unit(record.unit) or "kg"
        rows, factor_policy = _resolve_rows_for_record(
            record=record,
            source_code=SOURCE_FUGITIVE,
            year=record.period.year,
            hints=[record.ext_type.description, record.ext_type.ext_code],
        )

        # Usual case: mass of the agent times its GWP from the extinguisher catalog.
        if not rows:
            gwp = record.ext_type.gwp_100yr or resolve_gwp(
                gas=record.ext_type.ext_code,
                source_code=SOURCE_FUGITIVE,
                method_profile=method_profile,
            )
            try:
                amount_kg = convert_value(record.amount, activity_unit, "kg")
            except ValueError:
                amount_kg = record.amount
            contribution = gas_factor_to_tco2e(amount_kg, 1.0, gwp)
            calc = RowsCalc(
                total_tco2e=contribution,
                biogenic_tco2e=0.0,
                uncertainty_pct=source_uncertainty(0.1, 0.0),
                traces=[
                    {
                        "gas": record.ext_type.ext_code,
                        "gwp": gwp,
                        "biogenic": False,
                        "formula": {
                            "code": "fugitive_mass_x_gwp",
                            "method_profile": method_profile,
                            "activity_variable": "amount",
                            "factor_selection_policy": "extinguisher_type_gwp",
                        },
                        "activity_input": {
                            "value": record.amount,
                            "unit": activity_unit,
                            "normalized_to_factor_unit": amount_kg,
                            "factor_unit": "kg",
                        },
                        "factor": {
                            "id": None,
                            "agent": record.ext_type.description,
                            "value": 1.0,
                            "unit": "kg",
                            "source_ref": "extinguisher_type_gwp",
                            "year_applic": record.period.year,
                            "uncertainty_pct": None,
                        },
                        "result_tco2e": contribution,
                    }
                ],
                warnings=[],
                by_gas={record.ext_type.ext_code: contribution},
            )
            acc.add(record.id, "extinguisher_refill", calc)
            continue

        calc = _calc_from_factor_rows(
            source_code=SOURCE_FUGITIVE,
            activity_value=record.amount,
            activity_unit=activity_unit,
            factor_rows_payload=rows,
            method_profile=method_profile,
            formula_code="fugitive_mass_x_gwp",
            activity_variable="amount",
            factor_selection_policy=factor_policy,
            activity_unc_pct=0.1,
        )
        acc.add(record.id, "extinguisher_refill", calc)

    return acc.result()


def _calculate_waste(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        WasteRecord.objects.filter(period_id=period_id).select_related("period", "waste_type", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_WASTE, "Residuos")
    for record in records:
        _calc_record(
            acc, record, "waste", record.amount, normalize_unit(record.unit) or "kg", record.period.year,
            hints=[record.waste_type.treatment or "", record.waste_type.description],
            method_profile=method_profile,
            formula_code="waste_activity_x_factor",
            activity_variable="amount",
            activity_unc_pct=0.1,
        )
    return acc.result()


TRANSPORT_MODE_KEYWORDS = [
    ("transmilenio", "Transmilenio (pasajero-km)"),
    ("moto", "Motocicleta (pasajero-km)"),
    ("taxi", "Carro/taxi (pasajero-km)"),
    ("carro", "Carro/taxi (pasajero-km)"),
    ("bus", "Bus/SITP/Intermunicipal (pasajero-km)"),
    ("sitp", "Bus/SITP/Intermunicipal (pasajero-km)"),
    ("intermunicipal", "Bus/SITP/Intermunicipal (pasajero-km)"),
]

LODGING_KEYWORDS = [
    ("desayuno", "Hospedaje alojamiento y desayuno"),
    ("b&b", "Hospedaje alojamiento y desayuno"),
    ("hotel", "Hospedaje hotel"),
]


def _flight_hints(flight) -> list[str]:
    trip = "Ida y regreso" if flight.round_trip else "Un trayecto"
    origin, destination = flight.origin.strip(), flight.destination.strip()
    # The ICAO table is keyed Bogotá - <city>; a flight back to Bogotá uses the same route.
    return [f"Vuelo {origin} - {destination} ({trip})", f"Vuelo {destination} - {origin} ({trip})"]


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
    # Flights are institution-wide (no campus), so they only count in whole-university runs.
    flight_records = (
        Flight.objects.filter(period_id=period_id).select_related("period", "emission_factor")
        if not campus_id
        else Flight.objects.none()
    )
    acc = SourceAccumulator(SOURCE_TRANSPORT_LODGING, "Transporte y hospedaje")

    for record in flight_records:
        _calc_record(
            acc, record, "flight", record.passengers, "viaje", record.period.year,
            hints=_flight_hints(record),
            method_profile=method_profile,
            formula_code="flight_passengers_x_route_factor",
            activity_variable="passengers",
            activity_unc_pct=0.5,
        )

    for record in practice_records:
        _calc_record(
            acc, record, "field_practice", record.total_km, "km", record.period.year,
            hints=[record.description or "", "Salida de campo"],
            method_profile=method_profile,
            formula_code="field_trip_km_over_yield_x_fuel_factor",
            activity_variable="total_km",
            activity_unc_pct=0.5,
        )

    for record in ground_records:
        _calc_record(
            acc, record, "ground_transport", record.amount, record.unit, record.period.year,
            hints=[record.description] + _keyword_hints(record.description, TRANSPORT_MODE_KEYWORDS),
            method_profile=method_profile,
            formula_code="transport_activity_x_factor",
            activity_variable="amount",
            activity_unc_pct=0.5,
        )

    for record in lodging_records:
        _calc_record(
            acc, record, "lodging", record.nights, "nights", record.period.year,
            hints=_keyword_hints(record.description, LODGING_KEYWORDS) + ["Hospedaje hotel"],
            method_profile=method_profile,
            formula_code="lodging_nights_x_factor",
            activity_variable="nights",
            activity_unc_pct=0.5,
        )

    return acc.result()


def _calculate_paper(period_id: int, campus_id: int | None, method_profile: str):
    records = _apply_campus_filter(
        PaperConsumption.objects.filter(period_id=period_id).select_related("period", "size", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_PAPER, "Consumo de papel")
    for record in records:
        paper_kg = record.reams * record.size.kg_per_ream
        _calc_record(
            acc, record, "paper", paper_kg, "kg", record.period.year,
            hints=["Papel reciclado" if record.recycled else "Papel bond", "Papel"],
            method_profile=method_profile,
            formula_code="paper_consumption",
            activity_variable="paper_kg",
            activity_unc_pct=1.0,
        )
    return acc.result()


def _calculate_water(period_id: int, campus_id: int | None, method_profile: str):
    # Not part of the ECCI Excel tool, so it is kept out of the inventory total (decision 2026-10-18).
    # Records are still stored; call this function explicitly to estimate water emissions.
    records = _apply_campus_filter(
        WaterConsumption.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    acc = SourceAccumulator(SOURCE_WATER, "Consumo de agua potable")
    for record in records:
        acc.warnings.extend(validate_non_negative(record.m3, "Water m3"))
        _calc_record(
            acc, record, "water", record.m3, "m3", record.period.year,
            hints=["Agua potable", "Agua"],
            method_profile=method_profile,
            formula_code="water_activity_x_factor",
            activity_variable="m3",
            activity_unc_pct=5.0,
        )
    return acc.result()


def _calculate_removals(period_id: int, campus_id: int | None, method_profile: str = DEFAULT_METHOD_PROFILE):
    records = _apply_campus_filter(
        RemovalRecord.objects.filter(period_id=period_id).select_related("period", "emission_factor"),
        campus_id,
    )
    traces = []
    warnings = []
    total_negative = 0.0
    weighted = []

    for record in records:
        # Calculated removal: trees x capture per tree, or recovered kg x CH4 avoided x GWP.
        if record.activity_value is not None:
            rows, factor_policy = _resolve_rows_for_record(
                record, SOURCE_REMOVALS, record.period.year, hints=[record.description or "", record.rtype]
            )
            if not rows:
                warnings.append(f"No removal factor found for removal record {record.id}.")
                continue
            calc = _calc_from_factor_rows(
                source_code=SOURCE_REMOVALS,
                activity_value=record.activity_value,
                activity_unit=record.activity_unit or rows[0]["unit"],
                factor_rows_payload=rows,
                method_profile=method_profile,
                formula_code="removal_activity_x_factor",
                activity_variable="activity_value",
                factor_selection_policy=factor_policy,
            )
            warnings.extend(calc.warnings)
            contribution = removals_to_negative(calc.total_tco2e)
            items = calc.traces
            unc = calc.uncertainty_pct
        else:
            if record.tco2e is None:
                warnings.append(f"Removal record {record.id} has neither activity nor tCO2e.")
                continue
            warnings.extend(validate_non_negative(record.tco2e, "Removal tCO2e"))
            contribution = removals_to_negative(record.tco2e)
            items = [{"formula": "removals_to_negative", "input_tco2e": record.tco2e}]
            unc = source_uncertainty(0.1, 0.0)

        total_negative += contribution
        traces.append(
            {
                "record_id": record.id,
                "record_type": "removal",
                "rtype": record.rtype,
                "result_tco2e": contribution,
                "items": items,
            }
        )
        weighted.append((abs(contribution), unc))

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
        _calculate_lubricants(period_id, campus_id, method_profile),
        _calculate_electricity(period_id, campus_id, method_profile),
        _calculate_transport(period_id, campus_id, method_profile),
        _calculate_paper(period_id, campus_id, method_profile),
        _calculate_waste(period_id, campus_id, method_profile),
        _calculate_removals(period_id, campus_id, method_profile),
    ]

    gross_total = sum(result.total_tco2e for result in source_results if result.source_code != SOURCE_REMOVALS)
    removals_total = sum(result.total_tco2e for result in source_results if result.source_code == SOURCE_REMOVALS)
    net_total = gross_total + removals_total
    biogenic_total = sum(result.biogenic_tco2e for result in source_results)

    gas_breakdown: dict[str, float] = {}
    for result in source_results:
        for gas, value in result.by_gas.items():
            gas_breakdown[gas] = gas_breakdown.get(gas, 0.0) + value

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
            "biogenic_tco2e": biogenic_total,
            "uncertainty_pct": run_uncertainty,
            "gas_breakdown": gas_breakdown,
        },
        "sources": [
            {
                "source_code": result.source_code,
                "source_name": result.source_name,
                "total_tco2e": result.total_tco2e,
                "biogenic_tco2e": result.biogenic_tco2e,
                "uncertainty_pct": result.uncertainty_pct,
                "gas_breakdown": result.by_gas,
                "warnings": result.warnings,
                "traces": result.traces if include_traces else [],
            }
            for result in source_results
        ],
        "warnings": [warning for result in source_results for warning in result.warnings],
    }
