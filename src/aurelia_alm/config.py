"""Governed configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .constants import CURRENCIES
from .exceptions import ConfigurationError


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
