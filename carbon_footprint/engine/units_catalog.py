"""Units catalog and normalization helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitSpec:
    code: str
    dimension: str
    to_base: float
    base_unit: str


UNITS = {
    # mass
    "g": UnitSpec("g", "mass", 0.001, "kg"),
    "kg": UnitSpec("kg", "mass", 1.0, "kg"),
    "t": UnitSpec("t", "mass", 1000.0, "kg"),
    # energy
    "kwh": UnitSpec("kwh", "energy", 1.0, "kwh"),
    # volume
    "l": UnitSpec("l", "volume", 1.0, "l"),
    "lt": UnitSpec("lt", "volume", 1.0, "l"),
    "litro": UnitSpec("litro", "volume", 1.0, "l"),
    "litros": UnitSpec("litros", "volume", 1.0, "l"),
    "gal": UnitSpec("gal", "volume", 3.78541, "l"),
    "galon": UnitSpec("galon", "volume", 3.78541, "l"),
    "galones": UnitSpec("galones", "volume", 3.78541, "l"),
    "m3": UnitSpec("m3", "volume", 1000.0, "l"),
    # distance
    "km": UnitSpec("km", "distance", 1.0, "km"),
    # passenger distance
    "pkm": UnitSpec("pkm", "passenger_distance", 1.0, "pkm"),
    "pasajero-km": UnitSpec("pasajero-km", "passenger_distance", 1.0, "pkm"),
    # count
    "nights": UnitSpec("nights", "nights", 1.0, "nights"),
    "noches": UnitSpec("noches", "nights", 1.0, "nights"),
    "reams": UnitSpec("reams", "reams", 1.0, "reams"),
    "viaje": UnitSpec("viaje", "trips", 1.0, "viaje"),
    "viajes": UnitSpec("viajes", "trips", 1.0, "viaje"),
    "arbol": UnitSpec("arbol", "trees", 1.0, "arbol"),
    "arboles": UnitSpec("arboles", "trees", 1.0, "arbol"),
}


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    value = unit.strip().lower().replace(" ", "")
    return value or None


def convert_value(value: float, from_unit: str, to_unit: str) -> float:
    src = UNITS.get(normalize_unit(from_unit))
    dst = UNITS.get(normalize_unit(to_unit))
    if not src or not dst:
        raise ValueError(f"Unknown conversion from '{from_unit}' to '{to_unit}'.")
    if src.dimension != dst.dimension:
        raise ValueError(
            f"Incompatible dimensions for conversion: {from_unit} ({src.dimension}) -> {to_unit} ({dst.dimension})."
        )
    value_base = value * src.to_base
    return value_base / dst.to_base
