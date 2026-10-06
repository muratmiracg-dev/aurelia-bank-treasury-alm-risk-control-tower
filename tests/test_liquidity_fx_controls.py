from copy import deepcopy

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
    rapid = summary.set_index("scenario").loc["rapid_digital_run"]
    assert base > combined > rapid["lcr_proxy_pct"]
    assert rapid["survival_horizon_days"] == 7
    assert rapid["hqla_market_value_loss_try_mn"] > 0
    assert len(ladder) == 30
    assert set(summary["scenario"]) == {
        "base",
        "idiosyncratic",
        "market_wide",
        "combined",
        "rapid_digital_run",
    }


def test_rapid_digital_run_front_loads_outflows(config, demo):
    _, ladder = liquidity_stress(
        demo["positions"], demo["cashflows"], config["assumptions"]["liquidity"]
    )
    indexed = ladder.set_index(["scenario", "day"])
    rapid_share = (
        indexed.loc[("rapid_digital_run", 7), "cumulative_outflows_try_mn"]
        / indexed.loc[("rapid_digital_run", 30), "cumulative_outflows_try_mn"]
    )
    combined_share = (
        indexed.loc[("combined", 7), "cumulative_outflows_try_mn"]
        / indexed.loc[("combined", 30), "cumulative_outflows_try_mn"]
    )
    assert rapid_share == pytest.approx(0.85)
    assert combined_share == pytest.approx(0.55)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("demand_deposit_runoff", -0.01),
        ("term_deposit_runoff", 1.01),
        ("inflow_realisation", float("nan")),
        ("committed_facility_draw", True),
    ],
)
def test_liquidity_stress_rejects_invalid_scenario_rates(config, demo, field, value):
    liquidity_config = deepcopy(config["assumptions"]["liquidity"])
    liquidity_config["scenarios"]["base"][field] = value
    with pytest.raises(ValueError, match=field):
        liquidity_stress(demo["positions"], demo["cashflows"], liquidity_config)


def test_liquidity_stress_rejects_non_cumulative_outflow_timing(config, demo):
    liquidity_config = deepcopy(config["assumptions"]["liquidity"])
    liquidity_config["scenarios"]["base"]["outflow_timing"] = {
        1: 0.25,
        7: 0.1,
        30: 1.0,
        90: 1.15,
        180: 1.25,
        365: 1.4,
    }
    with pytest.raises(ValueError, match="outflow timing"):
        liquidity_stress(demo["positions"], demo["cashflows"], liquidity_config)


def test_fx_positions_and_ratio(demo):
    fx = fx_open_position(demo["positions"])
    values = fx.set_index("currency")["net_open_position_try_mn"].to_dict()
    assert values == {"EUR": -1500.0, "USD": -6000.0}
    ratio = aggregate_fx_limit_ratio(fx, 22_500)
    assert ratio == pytest.approx(33.3333333333)


@pytest.mark.parametrize("equity_try_mn", [0.0, -1.0, float("nan"), float("inf")])
def test_aggregate_fx_ratio_rejects_invalid_equity(equity_try_mn):
    positions = pd.DataFrame({"net_open_position_try_mn": [100.0]})

    with pytest.raises(ValueError, match="equity_try_mn must be a finite positive value"):
        aggregate_fx_limit_ratio(positions, equity_try_mn)


def test_fx_open_position_rejects_non_positive_equity(demo):
    portfolio = demo["positions"].copy()
    portfolio.loc[portfolio["side"] == "equity", "balance_try_mn"] = 0.0

    with pytest.raises(ValueError, match="equity_try_mn must be a finite positive value"):
        fx_open_position(portfolio)


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


@pytest.mark.parametrize(
    ("parameter", "value", "message"),
    [
        ("interest_rate_target_reduction", -0.01, "interest_rate_target_reduction"),
        ("interest_rate_target_reduction", 1.01, "interest_rate_target_reduction"),
        ("fx_target_reduction", float("nan"), "fx_target_reduction"),
        ("fx_target_reduction", float("inf"), "fx_target_reduction"),
        ("reference_swap_duration_years", 0.0, "reference_swap_duration_years"),
        ("reference_swap_duration_years", -1.0, "reference_swap_duration_years"),
    ],
)
def test_hedge_proposals_reject_unsafe_parameters(config, demo, parameter, value, message):
    dv01 = dv01_by_currency(demo["cashflows"], demo["market_curves"])
    fx = fx_open_position(demo["positions"])

    with pytest.raises(ValueError, match=message):
        propose_hedges(dv01, fx, **{parameter: value})


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


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -float("inf"), True])
def test_fx_overlay_rejects_invalid_amounts(demo, amount):
    with pytest.raises(ValueError, match="finite signed numbers"):
        fx_open_position(demo["positions"], {"USD": amount})


def test_fx_overlay_rejects_unknown_currency(demo):
    with pytest.raises(ValueError, match="unknown FX currency: USDD"):
        fx_open_position(demo["positions"], {"USDD": 100})


def test_fx_overlay_preserves_signed_hedges(demo):
    base = fx_open_position(demo["positions"]).set_index("currency")
    hedged = fx_open_position(demo["positions"], {"USD": -100}).set_index("currency")
    assert hedged.loc["USD", "net_open_position_try_mn"] == pytest.approx(
        base.loc["USD", "net_open_position_try_mn"] - 100
    )
