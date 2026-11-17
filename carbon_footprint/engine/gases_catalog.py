"""Gas catalog and methodological profiles for GWP values."""

DEFAULT_METHOD_PROFILE = "ISO14064_ECCI_2022"

# Biogenic anthropogenic CO2 is reported apart from the inventory total (ISO 14064-1:2020).
BIOGENIC_GASES = {"CO2_BIO"}


METHOD_PROFILES: dict[str, dict] = {
    "ISO14064_ECCI_2022": {
        # IPCC AR6 (2021), as used by the ECCI calculation tool (sheet FE).
        "default_gwp": {
            "CO2": 1.0,
            "CO2_BIO": 1.0,
            "CH4": 27.0,  # CH4 non-fossil
            "N2O": 273.0,
            "HCFC-123": 90.4,
            "HCFC-22": 1960.0,
            "HFC-134A": 1530.0,
            "HFC-404A": 3942.8,
            "HFC-407C": 1624.21,
            "HFC-410A": 2255.5,
            "HFC-227EA": 3600.0,
            "SF6": 24300.0,
        },
        "source_gwp_overrides": {
            # CH4 fossil for combustion and industrial processes.
            "ED1": {"CH4": 29.8},
            "ED2": {"CH4": 29.8},
            "ED3": {"CH4": 29.8},
            "EI2": {"CH4": 29.8},
        },
    },
}


def is_biogenic(gas: str | None) -> bool:
    return (gas or "").upper() in BIOGENIC_GASES


def resolve_gwp(
    gas: str,
    source_code: str,
    method_profile: str = DEFAULT_METHOD_PROFILE,
    explicit_gwp: float | None = None,
) -> float:
    gas_key = (gas or "CO2").upper()
    if explicit_gwp is not None:
        return float(explicit_gwp)

    profile = METHOD_PROFILES.get(method_profile, METHOD_PROFILES[DEFAULT_METHOD_PROFILE])
    source_overrides = profile.get("source_gwp_overrides", {}).get(source_code, {})
    if gas_key in source_overrides:
        return float(source_overrides[gas_key])
    return float(profile.get("default_gwp", {}).get(gas_key, 1.0))
