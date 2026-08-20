import pandas as pd
import pytest

from aurelia_alm.controls import data_quality_controls, risk_limit_controls
from aurelia_alm.fx import aggregate_fx_limit_ratio, fx_open_position
from aurelia_alm.hedging import propose_hedges
from aurelia_alm.irrbb import dv01_by_currency, eve_sensitivity, nii_sensitivity
from aurelia_alm.liquidity import liquidity_stress, nsfr_proxy


def test_nsfr_proxy(config, demo):
    result = nsfr_proxy(demo["positions"])
    assert result["nsfr_proxy_pct"] > 100
    assert result["available_stable_funding_try_mn"] > result["required_stable_funding_try_mn"]


def test_liquidity_stress_order(config, demo):
    summary, ladder = liquidity_stress(
        demo["positions"], demo["cashflows"], config["assumptions"]["liquidity"]
    )
    base = summary.set_index("scenario").loc["base", "lcr_proxy_pct"]
    combined = summary.set_index("scenario").loc["combined", "lcr_proxy_pct"]
    assert base > combined
    assert len(ladder) == 24
    assert set(summary["scenario"]) == {"base", "idiosyncratic", "market_wide", "combined"}


def test_fx_positions_and_ratio(demo):
    fx = fx_open_position(demo["positions"])
    values = fx.set_index("currency")["net_open_position_try_mn"].to_dict()
    assert values == {"EUR": -1500.0, "USD": -6000.0}
    ratio = aggregate_fx_limit_ratio(fx, 22_500)
    assert ratio == pytest.approx(33.3333333333)


def test_fx_overlay_reduces_exposure(demo):
    hedged = fx_open_position(demo["positions"], {"USD": 4_800, "EUR": 1_200})
    assert hedged["net_open_position_try_mn"].abs().sum() == pytest.approx(1_500)


def test_hedge_proposals(config, demo):
    dv01 = dv01_by_currency(demo["cashflows"], demo["market_curves"])
    fx = fx_open_position(demo["positions"])
    hedges = propose_hedges(dv01, fx)
    assert len(hedges) == 5
    assert set(hedges["approval_status"]) == {"ALCO_REVIEW_REQUIRED"}
    assert (hedges["recommended_notional_try_mn"] > 0).all()


def test_data_quality_controls_pass(demo):
    controls = data_quality_controls(demo["positions"], demo["cashflows"], demo["market_curves"])
    assert len(controls) == 10
    assert set(controls["status"]) == {"PASS"}


def test_data_quality_detects_duplicate(demo):
    duplicate = pd.concat([demo["positions"], demo["positions"].iloc[[0]]], ignore_index=True)
    controls = data_quality_controls(duplicate, demo["cashflows"], demo["market_curves"])
    status = controls.set_index("control_id").loc["DQ01", "status"]
    assert status == "FAIL"


def test_risk_limits_show_fx_breach(config, demo):
    eve, _ = eve_sensitivity(
        demo["positions"], demo["cashflows"], demo["market_curves"], config["shocks"]
    )
    nii, _ = nii_sensitivity(demo["positions"], config["shocks"], config["assumptions"])
    liquidity, _ = liquidity_stress(
        demo["positions"], demo["cashflows"], config["assumptions"]["liquidity"]
    )
    fx = fx_open_position(demo["positions"])
    ratio = aggregate_fx_limit_ratio(fx, 22_500)
    controls = risk_limit_controls(eve, nii, liquidity, ratio, config["limits"])
    breaches = controls.loc[controls["status"] == "BREACH", "control_id"].tolist()
    assert breaches == ["RL07"]
