"""Governed configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .constants import CURRENCIES
from .exceptions import ConfigurationError

LIQUIDITY_SCENARIOS = {
    "base",
    "idiosyncratic",
    "market_wide",
    "combined",
    "rapid_digital_run",
}
LIQUIDITY_PARAMETER_KEYS = {
    "demand_deposit_runoff",
    "term_deposit_runoff",
    "wholesale_runoff",
    "committed_facility_draw",
    "inflow_realisation",
}
HQLA_LEVELS = {"LEVEL_1", "LEVEL_2A", "LEVEL_2B", "NONE"}
LIQUIDITY_DAY_GRID = (1, 7, 30, 90, 180, 365)


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigurationError(f"Configuration root must be a mapping: {path}")
    return payload


def load_project_config(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    config = {
        "assumptions": load_yaml(root / "config" / "assumptions.yml"),
        "shocks": load_yaml(root / "config" / "basel_shocks.yml"),
        "limits": load_yaml(root / "config" / "limits.yml"),
    }
    validate_project_config(config)
    return config


def validate_project_config(config: dict[str, Any]) -> None:
    assumptions = config.get("assumptions", {})
    shocks = config.get("shocks", {}).get("currencies", {})
    fx_rates = assumptions.get("fx_rates", {})
    curves = assumptions.get("curve_calibration", {})
    missing = [c for c in CURRENCIES if c not in fx_rates or c not in shocks or c not in curves]
    if missing:
        raise ConfigurationError(f"Missing governed currency configuration: {missing}")
    for currency in CURRENCIES:
        if len(curves[currency]) != 19:
            raise ConfigurationError(f"{currency} curve must contain 19 IRRBB bucket points")
        params = shocks[currency]
        if any(float(params[key]) <= 0 for key in ("parallel", "short", "long")):
            raise ConfigurationError(f"Shock parameters must be positive for {currency}")

    liquidity = assumptions.get("liquidity", {})
    scenarios = liquidity.get("scenarios", {})
    missing_scenarios = LIQUIDITY_SCENARIOS - set(scenarios)
    if missing_scenarios:
        raise ConfigurationError(
            f"Missing governed liquidity scenarios: {sorted(missing_scenarios)}"
        )
    for scenario, params in scenarios.items():
        missing_parameters = LIQUIDITY_PARAMETER_KEYS - set(params)
        if missing_parameters:
            raise ConfigurationError(
                f"Liquidity scenario {scenario} is missing parameters: {sorted(missing_parameters)}"
            )
        if any(not 0.0 <= float(params[key]) <= 1.0 for key in LIQUIDITY_PARAMETER_KEYS):
            raise ConfigurationError(f"Liquidity scenario rates must be in [0, 1]: {scenario}")

        market_shocks = params.get("hqla_market_value_shock", {})
        unknown_levels = set(market_shocks) - HQLA_LEVELS
        if unknown_levels:
            raise ConfigurationError(f"Unknown HQLA levels in {scenario}: {sorted(unknown_levels)}")
        if any(not 0.0 <= float(value) < 1.0 for value in market_shocks.values()):
            raise ConfigurationError(f"HQLA market-value shocks must be in [0, 1): {scenario}")

        timing = params.get("outflow_timing")
        if timing is not None:
            timing_by_day = {int(day): float(share) for day, share in timing.items()}
            if tuple(sorted(timing_by_day)) != LIQUIDITY_DAY_GRID:
                raise ConfigurationError(
                    f"Liquidity outflow timing must use {LIQUIDITY_DAY_GRID}: {scenario}"
                )
            shares = [timing_by_day[day] for day in LIQUIDITY_DAY_GRID]
            if shares != sorted(shares) or shares[2] != 1.0:
                raise ConfigurationError(
                    f"Liquidity outflow timing must be monotonic with day 30 equal to 1: {scenario}"
                )
