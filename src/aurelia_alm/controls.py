"""Data-quality, reconciliation and risk-limit controls."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .constants import CURRENCIES, EVE_SCENARIOS


def data_quality_controls(
    portfolio: pd.DataFrame,
    cashflows: pd.DataFrame,
    curves: pd.DataFrame,
) -> pd.DataFrame:
    assets = float(portfolio.loc[portfolio["side"] == "asset", "balance_try_mn"].sum())
    liabilities = float(portfolio.loc[portfolio["side"] == "liability", "balance_try_mn"].sum())
    equity = float(portfolio.loc[portfolio["side"] == "equity", "balance_try_mn"].sum())
    principal = (
        cashflows.loc[cashflows["cashflow_type"] == "principal"]
        .groupby("position_id")["cashflow_try_mn"]
        .sum()
    )
    expected_principal = portfolio.loc[portfolio["side"].isin(["asset", "liability"])].set_index(
        "position_id"
    )
    expected_signed = expected_principal["balance_try_mn"].where(
        expected_principal["side"] == "asset", -expected_principal["balance_try_mn"]
    )
    principal_aligned = principal.reindex(expected_signed.index)
    max_principal_error = float((principal_aligned - expected_signed).abs().max())

    tests = [
        (
            "DQ01",
            "position identifiers are unique",
            portfolio["position_id"].is_unique,
            int(portfolio["position_id"].duplicated().sum()),
            0,
        ),
        (
            "DQ02",
            "critical position fields are complete",
            not portfolio.isna().any().any(),
            int(portfolio.isna().sum().sum()),
            0,
        ),
        (
            "DQ03",
            "currencies are governed",
            set(portfolio["currency"]).issubset(CURRENCIES),
            ",".join(sorted(set(portfolio["currency"]) - set(CURRENCIES))) or "none",
            "none",
        ),
        (
            "DQ04",
            "balances are positive",
            bool((portfolio["balance_try_mn"] > 0).all()),
            float(portfolio["balance_try_mn"].min()),
            ">0",
        ),
        (
            "DQ05",
            "rates are non-negative",
            bool((portfolio["current_rate_pct"] >= 0).all()),
            float(portfolio["current_rate_pct"].min()),
            ">=0",
        ),
        (
            "DQ06",
            "repricing does not exceed maturity",
            bool((portfolio["repricing_years"] <= portfolio["maturity_years"] + 1e-9).all()),
            float((portfolio["repricing_years"] - portfolio["maturity_years"]).max()),
            "<=0",
        ),
        (
            "DQ07",
            "accounting identity balances",
            abs(assets - liabilities - equity) < 1e-6,
            assets - liabilities - equity,
            0,
        ),
        (
            "DQ08",
            "principal cash flows reconcile",
            max_principal_error < 1e-4,
            max_principal_error,
            "<0.0001",
        ),
        (
            "DQ09",
            "all currencies have 19 curve points",
            bool((curves.groupby("currency").size() == 19).all()),
            curves.groupby("currency").size().to_dict(),
            19,
        ),
        (
            "DQ10",
            "curve rates are finite",
            bool(np.isfinite(curves["base_rate_pct"]).all()),
            int((~np.isfinite(curves["base_rate_pct"])).sum()),
            0,
        ),
    ]
    return pd.DataFrame(
        [
            {
                "control_id": control_id,
                "control": description,
                "status": "PASS" if passed else "FAIL",
                "observed": str(observed),
                "threshold": str(threshold),
                "severity": "CRITICAL" if control_id in {"DQ07", "DQ08"} else "HIGH",
            }
            for control_id, description, passed, observed, threshold in tests
        ]
    )


def risk_limit_controls(
    eve: pd.DataFrame,
    nii: pd.DataFrame,
    liquidity: pd.DataFrame,
    fx_ratio_pct: float,
    limits_config: dict[str, Any],
) -> pd.DataFrame:
    limits = limits_config["limits"]
    total_eve = eve.loc[eve["currency"] == "TOTAL"]
    worst_eve_loss = max(0.0, -float(total_eve["delta_eve_tier1_pct"].min()))
    worst_nii = float(nii["delta_nii_pct"].abs().max())
    combined = liquidity.loc[liquidity["scenario"] == "combined"].iloc[0]
    scenarios_present = set(total_eve["scenario"]) == set(EVE_SCENARIOS)
    checks = [
        ("RL01", "six prescribed EVE scenarios are present", scenarios_present, len(total_eve), 6),
        (
            "RL02",
            "maximum EVE decline / Tier 1",
            worst_eve_loss <= float(limits["max_delta_eve_loss_tier1_pct"]),
            worst_eve_loss,
            limits["max_delta_eve_loss_tier1_pct"],
        ),
        (
            "RL03",
            "absolute delta NII",
            worst_nii <= float(limits["max_abs_delta_nii_pct"]),
            worst_nii,
            limits["max_abs_delta_nii_pct"],
        ),
        (
            "RL04",
            "base LCR proxy",
            float(liquidity.loc[liquidity["scenario"] == "base", "lcr_proxy_pct"].iloc[0])
            >= float(limits["min_lcr_proxy_pct"]),
            float(liquidity.loc[liquidity["scenario"] == "base", "lcr_proxy_pct"].iloc[0]),
            limits["min_lcr_proxy_pct"],
        ),
        (
            "RL05",
            "NSFR proxy",
            float(combined["nsfr_proxy_pct"]) >= float(limits["min_nsfr_proxy_pct"]),
            float(combined["nsfr_proxy_pct"]),
            limits["min_nsfr_proxy_pct"],
        ),
        (
            "RL06",
            "combined survival horizon",
            float(combined["survival_horizon_days"]) >= float(limits["min_combined_survival_days"]),
            float(combined["survival_horizon_days"]),
            limits["min_combined_survival_days"],
        ),
        (
            "RL07",
            "aggregate FX open position / equity",
            fx_ratio_pct <= float(limits["max_fx_open_position_equity_pct"]),
            fx_ratio_pct,
            limits["max_fx_open_position_equity_pct"],
        ),
    ]
    return pd.DataFrame(
        [
            {
                "control_id": control_id,
                "control": description,
                "status": "WITHIN_LIMIT" if passed else "BREACH",
                "observed": round(float(observed), 6)
                if isinstance(observed, (int, float))
                else observed,
                "limit": limit,
                "severity": "HIGH" if passed else "CRITICAL",
            }
            for control_id, description, passed, observed, limit in checks
        ]
    )
