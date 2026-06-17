"""Gas catalog and methodological profiles for GWP values."""

DEFAULT_METHOD_PROFILE = "ISO14064_ECCI_2022"


METHOD_PROFILES: dict[str, dict] = {
    "ISO14064_ECCI_2022": {
        "default_gwp": {
            # Source: IPCC AR6 2021, Table 7.SM.7 (100-yr GWP including climate-carbon feedback)
            "CO2": 1.0,
            "CH4": 27.0,      # CH4 no fósil (biogénico/residuos) — AR6
            "N2O": 273.0,
            "HCFC-123": 90.4, # Informe ECCI 2022 / IPCC AR6 2021
        },
        "source_gwp_overrides": {
            # CH4 fósil (combustión) = 29.8 per IPCC AR6, used in fuel sources
            "ED1": {"CH4": 29.8},
            "ED2": {"CH4": 29.8},
            "ED3": {"CH4": 29.8},
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
