"""Gas catalog and methodological profiles for GWP values."""

DEFAULT_METHOD_PROFILE = "ISO14064_ECCI_2022"


METHOD_PROFILES: dict[str, dict] = {
    "ISO14064_ECCI_2022": {
        "default_gwp": {
            "CO2": 1.0,
            "CH4": 27.0,
            "N2O": 273.0,
            "HCFC-123": 77.0,
        },
        "source_gwp_overrides": {
            # Report-specific values used in fuel combustion equations.
            "ED1": {"CH4": 29.8},
            "ED2": {"CH4": 29.8},
        },
    },
}


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
