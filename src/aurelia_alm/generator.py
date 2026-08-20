"""Deterministic demonstration data for a fictional deposit bank.

The generated balance sheet is intentionally synthetic. Official TCMB and BDDK
observations are kept in a separate external-data layer and never presented as
Aurelia Bank records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .constants import IRRBB_BUCKETS


@dataclass(frozen=True)
class PositionTemplate:
    side: str
    product: str
    currency: str
    total_try_mn: float
    pieces: int
    rate_type: str
    rate_pct: float
    maturity_min: float
    maturity_max: float
    hqla_level: str = "NONE"
    asf_factor: float = 0.0
    rsf_factor: float = 0.0
    liquidity_days: int = 30
    deposit_beta: float = 0.0


def _templates() -> tuple[PositionTemplate, ...]:
    return (
        # TRY assets: TRY 150.0bn
        PositionTemplate(
            "asset",
            "cash_and_reserves",
            "TRY",
            12_000,
            4,
            "overnight",
            34.0,
            0.01,
            0.08,
            "LEVEL_1",
            rsf_factor=0.00,
            liquidity_days=1,
        ),
        PositionTemplate(
            "asset",
            "interbank_assets",
            "TRY",
            8_000,
            4,
            "floating",
            39.0,
            0.08,
            0.50,
            "LEVEL_1",
            rsf_factor=0.10,
            liquidity_days=7,
        ),
        PositionTemplate(
            "asset",
            "government_securities",
            "TRY",
            24_000,
            8,
            "fixed",
            31.5,
            1.5,
            9.0,
            "LEVEL_1",
            rsf_factor=0.05,
            liquidity_days=1,
        ),
        PositionTemplate(
            "asset",
            "corporate_bonds",
            "TRY",
            4_000,
            4,
            "fixed",
            35.0,
            1.0,
            5.0,
            "LEVEL_2A",
            rsf_factor=0.15,
            liquidity_days=7,
        ),
        PositionTemplate(
            "asset",
            "retail_loans_fixed",
            "TRY",
            13_000,
            6,
            "fixed",
            46.5,
            1.0,
            4.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        PositionTemplate(
            "asset",
            "retail_loans_floating",
            "TRY",
            13_000,
            6,
            "floating",
            44.5,
            1.0,
            4.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        PositionTemplate(
            "asset",
            "mortgages",
            "TRY",
            22_000,
            8,
            "fixed",
            37.0,
            4.0,
            12.0,
            rsf_factor=0.85,
            liquidity_days=180,
        ),
        PositionTemplate(
            "asset",
            "sme_loans",
            "TRY",
            25_000,
            8,
            "floating",
            45.0,
            0.75,
            4.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        PositionTemplate(
            "asset",
            "corporate_loans_fixed",
            "TRY",
            14_000,
            6,
            "fixed",
            42.0,
            1.0,
            5.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        PositionTemplate(
            "asset",
            "corporate_loans_floating",
            "TRY",
            15_000,
            6,
            "floating",
            41.0,
            0.75,
            4.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        # USD assets: TRY 18.0bn equivalent
        PositionTemplate(
            "asset",
            "cash_and_reserves",
            "USD",
            3_000,
            3,
            "overnight",
            4.0,
            0.01,
            0.08,
            "LEVEL_1",
            rsf_factor=0.00,
            liquidity_days=1,
        ),
        PositionTemplate(
            "asset",
            "government_securities",
            "USD",
            4_000,
            4,
            "fixed",
            5.2,
            1.0,
            7.0,
            "LEVEL_1",
            rsf_factor=0.05,
            liquidity_days=1,
        ),
        PositionTemplate(
            "asset",
            "corporate_loans",
            "USD",
            11_000,
            6,
            "floating",
            8.5,
            0.5,
            4.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        # EUR assets: TRY 12.0bn equivalent
        PositionTemplate(
            "asset",
            "cash_and_reserves",
            "EUR",
            2_000,
            3,
            "overnight",
            2.5,
            0.01,
            0.08,
            "LEVEL_1",
            rsf_factor=0.00,
            liquidity_days=1,
        ),
        PositionTemplate(
            "asset",
            "government_securities",
            "EUR",
            3_000,
            4,
            "fixed",
            4.0,
            1.0,
            7.0,
            "LEVEL_1",
            rsf_factor=0.05,
            liquidity_days=1,
        ),
        PositionTemplate(
            "asset",
            "corporate_loans",
            "EUR",
            7_000,
            5,
            "floating",
            7.0,
            0.5,
            4.0,
            rsf_factor=0.85,
            liquidity_days=90,
        ),
        # TRY liabilities: TRY 120.0bn
        PositionTemplate(
            "liability",
            "demand_deposits",
            "TRY",
            35_000,
            10,
            "non_maturity",
            18.0,
            2.0,
            5.0,
            asf_factor=0.90,
            liquidity_days=1,
            deposit_beta=0.42,
        ),
        PositionTemplate(
            "liability",
            "term_deposits",
            "TRY",
            57_000,
            12,
            "fixed",
            36.5,
            0.08,
            1.0,
            asf_factor=0.90,
            liquidity_days=30,
        ),
        PositionTemplate(
            "liability",
            "interbank_funding",
            "TRY",
            10_000,
            5,
            "floating",
            39.5,
            0.08,
            0.75,
            asf_factor=0.50,
            liquidity_days=7,
        ),
        PositionTemplate(
            "liability",
            "repo_funding",
            "TRY",
            8_000,
            4,
            "floating",
            39.0,
            0.02,
            0.25,
            asf_factor=0.00,
            liquidity_days=7,
        ),
        PositionTemplate(
            "liability",
            "issued_debt",
            "TRY",
            10_000,
            5,
            "fixed",
            32.0,
            1.0,
            6.0,
            asf_factor=1.00,
            liquidity_days=180,
        ),
        # USD liabilities: TRY 24.0bn equivalent
        PositionTemplate(
            "liability",
            "demand_deposits",
            "USD",
            8_000,
            5,
            "non_maturity",
            1.5,
            2.0,
            5.0,
            asf_factor=0.90,
            liquidity_days=1,
            deposit_beta=0.30,
        ),
        PositionTemplate(
            "liability",
            "term_deposits",
            "USD",
            10_000,
            6,
            "fixed",
            3.5,
            0.08,
            1.0,
            asf_factor=0.90,
            liquidity_days=30,
        ),
        PositionTemplate(
            "liability",
            "wholesale_funding",
            "USD",
            6_000,
            4,
            "floating",
            5.8,
            0.25,
            2.0,
            asf_factor=0.50,
            liquidity_days=30,
        ),
        # EUR liabilities: TRY 13.5bn equivalent
        PositionTemplate(
            "liability",
            "demand_deposits",
            "EUR",
            4_500,
            4,
            "non_maturity",
            1.0,
            2.0,
            5.0,
            asf_factor=0.90,
            liquidity_days=1,
            deposit_beta=0.28,
        ),
        PositionTemplate(
            "liability",
            "term_deposits",
            "EUR",
            6_000,
            5,
            "fixed",
            2.6,
            0.08,
            1.0,
            asf_factor=0.90,
            liquidity_days=30,
        ),
        PositionTemplate(
            "liability",
            "wholesale_funding",
            "EUR",
            3_000,
            3,
            "floating",
            4.5,
            0.25,
            2.0,
            asf_factor=0.50,
            liquidity_days=30,
        ),
        # Capital closes the synthetic accounting identity.
        PositionTemplate(
            "equity",
            "tier1_capital",
            "TRY",
            22_500,
            1,
            "non_interest",
            0.0,
            25.0,
            25.0,
            asf_factor=1.00,
            liquidity_days=10_000,
        ),
    )


def build_market_curves(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    curve_config = config["assumptions"]["curve_calibration"]
    for currency in ("TRY", "USD", "EUR"):
        for bucket, rate in zip(IRRBB_BUCKETS, curve_config[currency], strict=True):
            rows.append(
                {
                    "currency": currency,
                    "bucket": bucket.label,
                    "midpoint_years": bucket.midpoint_years,
                    "base_rate_pct": float(rate),
                    "classification": "synthetic_curve_calibrated_to_public_market_context",
                }
            )
    return pd.DataFrame(rows)


def build_portfolio(config: dict[str, Any], seed: int = 20260819) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    fx_rates = config["assumptions"]["fx_rates"]
    rows: list[dict[str, Any]] = []
    position_number = 1

    for template in _templates():
        raw_weights = rng.dirichlet(np.ones(template.pieces) * 2.5)
        amounts = np.round(raw_weights * template.total_try_mn, 6)
        amounts[-1] += template.total_try_mn - float(amounts.sum())
        for amount in amounts:
            maturity = float(rng.uniform(template.maturity_min, template.maturity_max))
            if template.rate_type == "fixed":
                repricing = maturity
            elif template.rate_type == "non_maturity":
                repricing = float(rng.uniform(0.20, 0.75))
            elif template.rate_type == "overnight":
                repricing = min(maturity, 1 / 365)
            elif template.rate_type == "non_interest":
                repricing = maturity
            else:
                repricing = min(maturity, float(rng.uniform(1 / 12, 0.50)))

            rate = max(0.0, template.rate_pct + float(rng.normal(0.0, 0.35)))
            fx = float(fx_rates[template.currency])
            rows.append(
                {
                    "position_id": f"AUR-{position_number:04d}",
                    "side": template.side,
                    "product": template.product,
                    "currency": template.currency,
                    "notional_ccy_mn": amount / fx,
                    "fx_to_try": fx,
                    "balance_try_mn": amount,
                    "rate_type": template.rate_type,
                    "current_rate_pct": rate,
                    "maturity_years": maturity,
                    "repricing_years": repricing,
                    "hqla_level": template.hqla_level,
                    "asf_factor": template.asf_factor,
                    "rsf_factor": template.rsf_factor,
                    "liquidity_days": template.liquidity_days,
                    "deposit_beta": template.deposit_beta,
                    "data_classification": "deterministic_synthetic_bank_position",
                }
            )
            position_number += 1

    portfolio = pd.DataFrame(rows)
    portfolio["maturity_years"] = portfolio["maturity_years"].round(6)
    portfolio["repricing_years"] = portfolio["repricing_years"].round(6)
    portfolio["current_rate_pct"] = portfolio["current_rate_pct"].round(6)
    portfolio["notional_ccy_mn"] = portfolio["notional_ccy_mn"].round(6)
    portfolio["balance_try_mn"] = portfolio["balance_try_mn"].round(6)
    return portfolio


def build_cashflows(portfolio: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for position in portfolio.itertuples(index=False):
        if position.side == "equity":
            continue
        sign = 1.0 if position.side == "asset" else -1.0
        balance = float(position.balance_try_mn)
        annual_rate = float(position.current_rate_pct) / 100.0

        if position.rate_type == "non_maturity":
            times = np.array([0.25, 0.50, 1.0, 2.0, 3.0, 5.0])
            weights = np.array([0.10, 0.15, 0.22, 0.23, 0.18, 0.12])
            outstanding = balance
            previous = 0.0
            for time_years, weight in zip(times, weights, strict=True):
                principal = balance * float(weight)
                coupon = outstanding * annual_rate * (time_years - previous)
                rows.append(_cashflow_row(position, time_years, sign * coupon, "interest"))
                rows.append(_cashflow_row(position, time_years, sign * principal, "principal"))
                outstanding -= principal
                previous = time_years
            continue

        effective_maturity = float(position.maturity_years)
        if position.rate_type in {"floating", "overnight"}:
            effective_maturity = min(effective_maturity, float(position.repricing_years))
        effective_maturity = max(effective_maturity, 1 / 365)

        amortising = any(token in position.product for token in ("loans", "mortgages"))
        frequency = 0.25 if effective_maturity <= 1 else 0.50
        periods = max(1, int(np.ceil(effective_maturity / frequency)))
        period_times = np.linspace(effective_maturity / periods, effective_maturity, periods)
        outstanding = balance
        principal_per_period = balance / periods if amortising else 0.0
        previous = 0.0
        for index, time_years in enumerate(period_times, start=1):
            delta = float(time_years - previous)
            coupon = outstanding * annual_rate * delta
            rows.append(_cashflow_row(position, float(time_years), sign * coupon, "interest"))
            principal = (
                principal_per_period if amortising else (balance if index == periods else 0.0)
            )
            if principal:
                rows.append(
                    _cashflow_row(position, float(time_years), sign * principal, "principal")
                )
                outstanding -= principal
            previous = float(time_years)

    cashflows = pd.DataFrame(rows)
    cashflows["time_years"] = cashflows["time_years"].round(6)
    cashflows["cashflow_try_mn"] = cashflows["cashflow_try_mn"].round(6)
    return cashflows


def _cashflow_row(
    position: Any, time_years: float, amount: float, flow_type: str
) -> dict[str, Any]:
    return {
        "position_id": position.position_id,
        "side": position.side,
        "product": position.product,
        "currency": position.currency,
        "time_years": time_years,
        "cashflow_try_mn": amount,
        "cashflow_type": flow_type,
    }


def build_demo_data(config: dict[str, Any], seed: int = 20260819) -> dict[str, pd.DataFrame]:
    portfolio = build_portfolio(config, seed=seed)
    return {
        "positions": portfolio,
        "cashflows": build_cashflows(portfolio),
        "market_curves": build_market_curves(config),
    }
