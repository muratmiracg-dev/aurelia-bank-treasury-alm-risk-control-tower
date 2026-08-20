"""Transparent liquidity stress, LCR proxy and NSFR proxy calculations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _hqla(portfolio: pd.DataFrame, haircuts: dict[str, float]) -> float:
    assets = portfolio.loc[portfolio["side"] == "asset"].copy()
    assets["haircut"] = assets["hqla_level"].map(haircuts).fillna(1.0)
    assets["eligible_hqla_try_mn"] = assets["balance_try_mn"] * (1.0 - assets["haircut"])
    return float(assets["eligible_hqla_try_mn"].sum())


def nsfr_proxy(portfolio: pd.DataFrame) -> dict[str, float]:
    funding = portfolio.loc[portfolio["side"].isin(["liability", "equity"])].copy()
    assets = portfolio.loc[portfolio["side"] == "asset"].copy()
    asf = float((funding["balance_try_mn"] * funding["asf_factor"]).sum())
    rsf = float((assets["balance_try_mn"] * assets["rsf_factor"]).sum())
    return {
        "available_stable_funding_try_mn": asf,
        "required_stable_funding_try_mn": rsf,
        "nsfr_proxy_pct": 100.0 * asf / rsf if rsf else np.inf,
    }


def liquidity_stress(
    portfolio: pd.DataFrame,
    cashflows: pd.DataFrame,
    liquidity_config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    haircuts = liquidity_config["hqla_haircuts"]
    hqla = _hqla(portfolio, haircuts)
    nsfr = nsfr_proxy(portfolio)
    liabilities = portfolio.loc[portfolio["side"] == "liability"]
    position_liquidity = portfolio[["position_id", "hqla_level"]]
    positive_cashflows = cashflows.loc[cashflows["cashflow_try_mn"] > 0].merge(
        position_liquidity, on="position_id", how="left", validate="many_to_one"
    )
    # HQLA is already in the numerator and cannot also be recognised as a cash inflow.
    positive_cashflows = positive_cashflows.loc[positive_cashflows["hqla_level"] == "NONE"]
    commitments = 0.08 * float(
        portfolio.loc[portfolio["product"].str.contains("loans"), "balance_try_mn"].sum()
    )
    day_grid = (1, 7, 30, 90, 180, 365)
    outflow_profile = {1: 0.25, 7: 0.55, 30: 1.00, 90: 1.15, 180: 1.25, 365: 1.40}
    summary_rows: list[dict[str, float | str]] = []
    ladder_rows: list[dict[str, float | str | int]] = []

    for scenario, params in liquidity_config["scenarios"].items():
        demand = float(
            liabilities.loc[liabilities["product"] == "demand_deposits", "balance_try_mn"].sum()
        )
        term = float(
            liabilities.loc[liabilities["product"] == "term_deposits", "balance_try_mn"].sum()
        )
        wholesale = float(
            liabilities.loc[
                liabilities["product"].isin(
                    ["interbank_funding", "repo_funding", "wholesale_funding"]
                ),
                "balance_try_mn",
            ].sum()
        )
        outflows_30d = (
            demand * float(params["demand_deposit_runoff"])
            + term * float(params["term_deposit_runoff"])
            + wholesale * float(params["wholesale_runoff"])
            + commitments * float(params["committed_facility_draw"])
        )
        inflows_30d = float(
            positive_cashflows.loc[
                positive_cashflows["time_years"] <= 30 / 365, "cashflow_try_mn"
            ].sum()
        ) * float(params["inflow_realisation"])
        capped_inflows = min(inflows_30d, 0.75 * outflows_30d)
        net_outflows = max(outflows_30d - capped_inflows, 1e-9)
        lcr = 100.0 * hqla / net_outflows

        survival_days = 365
        for day in day_grid:
            inflows = float(
                positive_cashflows.loc[
                    positive_cashflows["time_years"] <= day / 365, "cashflow_try_mn"
                ].sum()
            ) * float(params["inflow_realisation"])
            cumulative_outflows = outflows_30d * outflow_profile[day]
            cumulative_net = hqla + inflows - cumulative_outflows
            ladder_rows.append(
                {
                    "scenario": scenario,
                    "day": day,
                    "hqla_try_mn": hqla,
                    "cumulative_inflows_try_mn": inflows,
                    "cumulative_outflows_try_mn": cumulative_outflows,
                    "cumulative_net_liquidity_try_mn": cumulative_net,
                }
            )
            if cumulative_net < 0 and survival_days == 365:
                survival_days = day

        summary_rows.append(
            {
                "scenario": scenario,
                "hqla_try_mn": hqla,
                "gross_outflows_30d_try_mn": outflows_30d,
                "eligible_inflows_30d_try_mn": capped_inflows,
                "net_outflows_30d_try_mn": net_outflows,
                "lcr_proxy_pct": lcr,
                "survival_horizon_days": survival_days,
                **nsfr,
            }
        )
    return pd.DataFrame(summary_rows).round(6), pd.DataFrame(ladder_rows).round(6)
