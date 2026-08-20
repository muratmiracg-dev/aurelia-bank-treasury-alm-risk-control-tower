"""Basel IRRBB curve shock construction."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .constants import EVE_SCENARIOS


def shock_bps(
    scenario: str,
    tenor_years: float | np.ndarray,
    parameters: dict[str, float],
    decay_years: float = 4.0,
) -> float | np.ndarray:
    """Return the Basel scenario shock in basis points at a tenor."""
    if scenario not in EVE_SCENARIOS:
        raise ValueError(f"Unknown IRRBB scenario: {scenario}")
    tenor = np.asarray(tenor_years, dtype=float)
    alpha_short = np.exp(-tenor / decay_years)
    parallel = float(parameters["parallel"])
    short = float(parameters["short"]) * alpha_short
    long = float(parameters["long"]) * (1.0 - alpha_short)

    scenario_map = {
        "parallel_up": np.full_like(tenor, parallel),
        "parallel_down": np.full_like(tenor, -parallel),
        "steepener": -0.65 * short + 0.90 * long,
        "flattener": 0.80 * short - 0.60 * long,
        "short_up": short,
        "short_down": -short,
    }
    result = scenario_map[scenario]
    if np.isscalar(tenor_years):
        return float(result)
    return result


def build_shocked_curves(
    base_curves: pd.DataFrame,
    shock_config: dict[str, Any],
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    currency_config = shock_config["currencies"]
    decay = float(shock_config.get("short_rate_decay_years", 4.0))
    floor = float(shock_config.get("post_shock_floor_pct", 0.0))

    for currency, group in base_curves.groupby("currency", sort=False):
        if currency not in currency_config:
            raise ValueError(f"Missing shock parameters for {currency}")
        for scenario in EVE_SCENARIOS:
            frame = group.copy()
            frame["scenario"] = scenario
            frame["shock_bps"] = shock_bps(
                scenario,
                frame["midpoint_years"].to_numpy(),
                currency_config[currency],
                decay,
            )
            frame["shocked_rate_pct"] = np.maximum(
                floor,
                frame["base_rate_pct"] + frame["shock_bps"] / 100.0,
            )
            rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def interpolate_rate(curve: pd.DataFrame, currency: str, tenor_years: np.ndarray) -> np.ndarray:
    currency_curve = curve.loc[curve["currency"] == currency].sort_values("midpoint_years")
    if currency_curve.empty:
        raise ValueError(f"Curve not found for currency {currency}")
    rate_column = "shocked_rate_pct" if "shocked_rate_pct" in currency_curve else "base_rate_pct"
    return np.interp(
        tenor_years,
        currency_curve["midpoint_years"].to_numpy(),
        currency_curve[rate_column].to_numpy(),
    )
