"""End-to-end governed analytical pipeline."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .config import load_project_config
from .controls import data_quality_controls, risk_limit_controls
from .fx import aggregate_fx_limit_ratio, fx_open_position
from .gap import maturity_gap, repricing_gap
from .generator import build_demo_data
from .hedging import propose_hedges
from .irrbb import dv01_by_currency, eve_sensitivity, nii_sensitivity
from .liquidity import liquidity_stress
from .reporting import create_figures


def run_pipeline(root: str | Path, seed: int = 20260819) -> dict[str, Any]:
    root = Path(root).resolve()
    config = load_project_config(root)
    data = build_demo_data(config, seed=seed)
    _write_frames(data, root / "data" / "demo")

    gap = repricing_gap(data["positions"])
    maturity = maturity_gap(data["positions"])
    eve, shocked_curves = eve_sensitivity(
        data["positions"], data["cashflows"], data["market_curves"], config["shocks"]
    )
    dv01 = dv01_by_currency(data["cashflows"], data["market_curves"])
    nii, nii_detail = nii_sensitivity(data["positions"], config["shocks"], config["assumptions"])
    liquidity, liquidity_ladder = liquidity_stress(
        data["positions"], data["cashflows"], config["assumptions"]["liquidity"]
    )
    fx = fx_open_position(data["positions"])
    equity = float(
        data["positions"].loc[data["positions"]["side"] == "equity", "balance_try_mn"].sum()
    )
    fx_ratio = aggregate_fx_limit_ratio(fx, equity)
    hedges = propose_hedges(dv01, fx)
    dq_controls = data_quality_controls(data["positions"], data["cashflows"], data["market_curves"])
    limit_controls = risk_limit_controls(eve, nii, liquidity, fx_ratio, config["limits"])

    results = {
        "repricing_gap": gap,
        "maturity_gap": maturity,
        "eve": eve,
        "shocked_curves": shocked_curves,
        "dv01": dv01,
        "nii": nii,
        "nii_detail": nii_detail,
        "liquidity": liquidity,
        "liquidity_ladder": liquidity_ladder,
        "fx": fx,
        "hedges": hedges,
        "data_quality_controls": dq_controls,
        "risk_limit_controls": limit_controls,
    }
    _write_frames(results, root / "artifacts" / "results")
    figures = create_figures(results, root / "artifacts" / "figures")
    summary = _executive_summary(data["positions"], results, config, seed)
    summary_path = root / "artifacts" / "results" / "executive_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_sqlite(root / "artifacts" / "aurelia_alm_demo.sqlite", {**data, **results})
    _write_manifest(root, figures)
    return summary


def _write_frames(frames: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, float_format="%.6f")


def _executive_summary(
    positions: pd.DataFrame,
    results: dict[str, pd.DataFrame],
    config: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    assets = float(positions.loc[positions["side"] == "asset", "balance_try_mn"].sum())
    liabilities = float(positions.loc[positions["side"] == "liability", "balance_try_mn"].sum())
    equity = float(positions.loc[positions["side"] == "equity", "balance_try_mn"].sum())
    deposits = float(
        positions.loc[
            positions["product"].isin(["demand_deposits", "term_deposits"]), "balance_try_mn"
        ].sum()
    )
    total_eve = results["eve"].loc[results["eve"]["currency"] == "TOTAL"]
    worst_eve_row = total_eve.loc[total_eve["delta_eve_try_mn"].idxmin()]
    worst_nii_row = results["nii"].loc[results["nii"]["delta_nii_try_mn"].idxmin()]
    base_liquidity = results["liquidity"].loc[results["liquidity"]["scenario"] == "base"].iloc[0]
    combined_liquidity = (
        results["liquidity"].loc[results["liquidity"]["scenario"] == "combined"].iloc[0]
    )
    rapid_digital_run = (
        results["liquidity"].loc[results["liquidity"]["scenario"] == "rapid_digital_run"].iloc[0]
    )
    fx_ratio = aggregate_fx_limit_ratio(results["fx"], equity)
    return {
        "project": "Aurelia Bank Treasury, ALM & Risk Control Tower",
        "as_of_date": config["assumptions"]["as_of_date"],
        "reporting_currency": "TRY million",
        "seed": seed,
        "data_posture": {
            "bank_positions": "deterministic synthetic",
            "market_anchors": "official TCMB snapshot",
            "sector_benchmark": "official BDDK June 2026 snapshot",
        },
        "balance_sheet": {
            "assets_try_mn": round(assets, 3),
            "liabilities_try_mn": round(liabilities, 3),
            "tier1_capital_try_mn": round(equity, 3),
            "deposits_try_mn": round(deposits, 3),
        },
        "irrbb": {
            "baseline_eve_try_mn": round(float(worst_eve_row["baseline_eve_try_mn"]), 3),
            "worst_scenario": str(worst_eve_row["scenario"]),
            "worst_delta_eve_try_mn": round(float(worst_eve_row["delta_eve_try_mn"]), 3),
            "worst_delta_eve_tier1_pct": round(float(worst_eve_row["delta_eve_tier1_pct"]), 3),
            "baseline_nii_try_mn": round(float(worst_nii_row["baseline_nii_try_mn"]), 3),
            "worst_nii_scenario": str(worst_nii_row["scenario"]),
            "worst_delta_nii_try_mn": round(float(worst_nii_row["delta_nii_try_mn"]), 3),
            "worst_delta_nii_pct": round(float(worst_nii_row["delta_nii_pct"]), 3),
        },
        "liquidity": {
            "base_lcr_proxy_pct": round(float(base_liquidity["lcr_proxy_pct"]), 3),
            "combined_lcr_proxy_pct": round(float(combined_liquidity["lcr_proxy_pct"]), 3),
            "rapid_digital_run_lcr_proxy_pct": round(float(rapid_digital_run["lcr_proxy_pct"]), 3),
            "nsfr_proxy_pct": round(float(combined_liquidity["nsfr_proxy_pct"]), 3),
            "combined_survival_horizon_days": int(combined_liquidity["survival_horizon_days"]),
            "rapid_digital_run_survival_horizon_days": int(
                rapid_digital_run["survival_horizon_days"]
            ),
            "rapid_digital_run_hqla_market_value_loss_try_mn": round(
                float(rapid_digital_run["hqla_market_value_loss_try_mn"]), 3
            ),
        },
        "fx": {"aggregate_open_position_equity_pct": round(fx_ratio, 3)},
        "controls": {
            "data_quality_passed": int(
                (results["data_quality_controls"]["status"] == "PASS").sum()
            ),
            "data_quality_total": int(len(results["data_quality_controls"])),
            "risk_limit_breaches": int(
                (results["risk_limit_controls"]["status"] == "BREACH").sum()
            ),
            "risk_limits_total": int(len(results["risk_limit_controls"])),
        },
    }


def _write_sqlite(path: Path, frames: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        for name, frame in frames.items():
            frame.to_sql(name, connection, if_exists="replace", index=False)


def _write_manifest(root: Path, figures: list[Path]) -> None:
    candidates = list((root / "data" / "demo").glob("*.csv"))
    candidates += list((root / "artifacts" / "results").glob("*.csv"))
    candidates += [root / "artifacts" / "results" / "executive_summary.json", *figures]
    lines: list[str] = []
    for path in sorted(candidates):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
