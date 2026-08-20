"""Economic-value and earnings views of interest-rate risk in the banking book."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .constants import NII_SCENARIOS
from .shocks import build_shocked_curves, interpolate_rate, shock_bps


def present_value(cashflows: pd.DataFrame, curves: pd.DataFrame) -> pd.DataFrame:
    """Discount signed cash flows by currency using continuously interpolated zero rates."""
    frames: list[pd.DataFrame] = []
    for currency, group in cashflows.groupby("currency", sort=False):
        frame = group.copy()
        tenors = frame["time_years"].to_numpy(dtype=float)
        rates = interpolate_rate(curves, currency, tenors) / 100.0
        discount_factor = np.power(1.0 + rates, -tenors)
        frame["discount_rate_pct"] = rates * 100.0
        frame["discount_factor"] = discount_factor
        frame["present_value_try_mn"] = frame["cashflow_try_mn"] * discount_factor
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def eve_sensitivity(
    portfolio: pd.DataFrame,
    cashflows: pd.DataFrame,
    base_curves: pd.DataFrame,
    shock_config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate EVE under all six Basel prescribed shocks."""
    baseline_detail = present_value(cashflows, base_curves)
    baseline_by_currency = baseline_detail.groupby("currency")["present_value_try_mn"].sum()
    shocked_curves = build_shocked_curves(base_curves, shock_config)
    tier1 = float(portfolio.loc[portfolio["side"] == "equity", "balance_try_mn"].sum())
    rows: list[dict[str, float | str]] = []

    for scenario, scenario_curves in shocked_curves.groupby("scenario", sort=False):
        shocked_detail = present_value(cashflows, scenario_curves)
        shocked_by_currency = shocked_detail.groupby("currency")["present_value_try_mn"].sum()
        for currency in baseline_by_currency.index:
            baseline = float(baseline_by_currency[currency])
            shocked = float(shocked_by_currency[currency])
            delta = shocked - baseline
            rows.append(
                {
                    "scenario": scenario,
                    "currency": currency,
                    "baseline_eve_try_mn": baseline,
                    "shocked_eve_try_mn": shocked,
                    "delta_eve_try_mn": delta,
                    "delta_eve_tier1_pct": 100.0 * delta / tier1,
                }
            )
        total_baseline = float(baseline_by_currency.sum())
        total_shocked = float(shocked_by_currency.sum())
        total_delta = total_shocked - total_baseline
        rows.append(
            {
                "scenario": scenario,
                "currency": "TOTAL",
                "baseline_eve_try_mn": total_baseline,
                "shocked_eve_try_mn": total_shocked,
                "delta_eve_try_mn": total_delta,
                "delta_eve_tier1_pct": 100.0 * total_delta / tier1,
            }
        )
    result = pd.DataFrame(rows)
    numeric = result.select_dtypes(include="number").columns
    result[numeric] = result[numeric].round(6)
    return result, shocked_curves


def dv01_by_currency(cashflows: pd.DataFrame, base_curves: pd.DataFrame) -> pd.DataFrame:
    baseline = present_value(cashflows, base_curves)
    baseline_currency = baseline.groupby("currency")["present_value_try_mn"].sum()
    one_bp = base_curves.copy()
    one_bp["shocked_rate_pct"] = one_bp["base_rate_pct"] + 0.01
    shocked = present_value(cashflows, one_bp)
    shocked_currency = shocked.groupby("currency")["present_value_try_mn"].sum()
    rows = [
        {
            "currency": currency,
            "baseline_eve_try_mn": float(baseline_currency[currency]),
            "dv01_try_mn": float(shocked_currency[currency] - baseline_currency[currency]),
        }
        for currency in baseline_currency.index
    ]
    rows.append(
        {
            "currency": "TOTAL",
            "baseline_eve_try_mn": float(baseline_currency.sum()),
            "dv01_try_mn": float(shocked_currency.sum() - baseline_currency.sum()),
        }
    )
    return pd.DataFrame(rows).round(6)


def nii_sensitivity(
    portfolio: pd.DataFrame,
    shock_config: dict[str, Any],
    assumptions: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate one-year static-balance-sheet NII sensitivity.

    Only positions that reprice within the horizon receive the shock. The approach is
    intentionally transparent and is not a claim of regulatory NII reporting.
    """
    horizon = float(assumptions.get("nii_horizon_years", 1.0))
    frame = portfolio.loc[portfolio["side"].isin(["asset", "liability"])].copy()
    frame["sign"] = np.where(frame["side"] == "asset", 1.0, -1.0)
    frame["baseline_nii_try_mn"] = (
        frame["sign"] * frame["balance_try_mn"] * frame["current_rate_pct"] / 100.0 * horizon
    )
    frame["repriced_fraction"] = np.clip(
        (horizon - frame["repricing_years"]) / horizon,
        0.0,
        1.0,
    )

    def pass_through(row: pd.Series) -> float:
        if row["rate_type"] == "non_maturity":
            return float(row["deposit_beta"])
        side_key = "asset_pass_through" if row["side"] == "asset" else "liability_pass_through"
        return float(assumptions[side_key].get(row["rate_type"], 0.0))

    frame["pass_through"] = frame.apply(pass_through, axis=1)
    detail_rows: list[pd.DataFrame] = []
    summary_rows: list[dict[str, float | str]] = []
    baseline_total = float(frame["baseline_nii_try_mn"].sum())

    for scenario in NII_SCENARIOS:
        scenario_frame = frame.copy()
        scenario_frame["scenario"] = scenario
        scenario_frame["shock_bps"] = scenario_frame.apply(
            lambda row, scenario=scenario: shock_bps(
                scenario,
                float(row["repricing_years"]),
                shock_config["currencies"][row["currency"]],
                float(shock_config.get("short_rate_decay_years", 4.0)),
            ),
            axis=1,
        )
        scenario_frame["effective_rate_change_pct"] = (
            scenario_frame["shock_bps"]
            / 100.0
            * scenario_frame["pass_through"]
            * scenario_frame["repriced_fraction"]
        )
        scenario_frame["shocked_nii_try_mn"] = (
            scenario_frame["sign"]
            * scenario_frame["balance_try_mn"]
            * (scenario_frame["current_rate_pct"] + scenario_frame["effective_rate_change_pct"])
            / 100.0
            * horizon
        )
        scenario_frame["delta_nii_try_mn"] = (
            scenario_frame["shocked_nii_try_mn"] - scenario_frame["baseline_nii_try_mn"]
        )
        detail_rows.append(scenario_frame)
        shocked_total = float(scenario_frame["shocked_nii_try_mn"].sum())
        delta = shocked_total - baseline_total
        summary_rows.append(
            {
                "scenario": scenario,
                "baseline_nii_try_mn": baseline_total,
                "shocked_nii_try_mn": shocked_total,
                "delta_nii_try_mn": delta,
                "delta_nii_pct": 100.0 * delta / abs(baseline_total),
            }
        )

    detail = pd.concat(detail_rows, ignore_index=True)
    detail_columns = [
        "scenario",
        "position_id",
        "side",
        "product",
        "currency",
        "balance_try_mn",
        "repricing_years",
        "shock_bps",
        "pass_through",
        "repriced_fraction",
        "baseline_nii_try_mn",
        "shocked_nii_try_mn",
        "delta_nii_try_mn",
    ]
    detail = detail[detail_columns]
    return pd.DataFrame(summary_rows).round(6), detail.round(6)
