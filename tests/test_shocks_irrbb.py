import numpy as np
import pandas as pd
import pytest

from aurelia_alm.irrbb import dv01_by_currency, eve_sensitivity, nii_sensitivity, present_value
from aurelia_alm.shocks import build_shocked_curves, interpolate_rate, shock_bps


def test_try_parallel_shocks(config):
    params = config["shocks"]["currencies"]["TRY"]
    assert shock_bps("parallel_up", 2.0, params) == 400
    assert shock_bps("parallel_down", 2.0, params) == -400


def test_short_shock_decays(config):
    params = config["shocks"]["currencies"]["TRY"]
    near = shock_bps("short_up", 0.1, params)
    far = shock_bps("short_up", 20.0, params)
    assert near > far > 0


def test_rotation_formulas(config):
    params = config["shocks"]["currencies"]["EUR"]
    steep = shock_bps("steepener", np.array([0.0, 25.0]), params)
    flat = shock_bps("flattener", np.array([0.0, 25.0]), params)
    assert steep[0] < 0 < steep[1]
    assert flat[0] > 0 > flat[1]


def test_unknown_shock_rejected(config):
    with pytest.raises(ValueError):
        shock_bps("unknown", 1.0, config["shocks"]["currencies"]["TRY"])


def test_shocked_curve_count(config, demo):
    curves = build_shocked_curves(demo["market_curves"], config["shocks"])
    assert len(curves) == 57 * 6
    assert curves["shocked_rate_pct"].min() >= 0


def test_interpolate_missing_currency(demo):
    with pytest.raises(ValueError):
        interpolate_rate(demo["market_curves"], "GBP", np.array([1.0]))


def test_present_value_simple():
    cashflows = pd.DataFrame([{"currency": "TRY", "time_years": 1.0, "cashflow_try_mn": 110.0}])
    curve = pd.DataFrame(
        [
            {"currency": "TRY", "midpoint_years": 0.0, "base_rate_pct": 10.0},
            {"currency": "TRY", "midpoint_years": 2.0, "base_rate_pct": 10.0},
        ]
    )
    result = present_value(cashflows, curve)
    assert result["present_value_try_mn"].iloc[0] == pytest.approx(100.0)


def test_eve_has_six_scenarios(config, demo):
    eve, _ = eve_sensitivity(
        demo["positions"], demo["cashflows"], demo["market_curves"], config["shocks"]
    )
    total = eve.loc[eve["currency"] == "TOTAL"]
    assert len(total) == 6
    assert total.loc[total["scenario"] == "parallel_up", "delta_eve_try_mn"].iloc[0] < 0


def test_dv01_has_total(demo):
    result = dv01_by_currency(demo["cashflows"], demo["market_curves"])
    assert set(result["currency"]) == {"TRY", "USD", "EUR", "TOTAL"}
    components = result.loc[result["currency"] != "TOTAL", "dv01_try_mn"].sum()
    total = result.loc[result["currency"] == "TOTAL", "dv01_try_mn"].iloc[0]
    assert total == pytest.approx(components, abs=1e-5)


def test_nii_parallel_shocks_are_symmetric(config, demo):
    summary, detail = nii_sensitivity(demo["positions"], config["shocks"], config["assumptions"])
    up = summary.loc[summary["scenario"] == "parallel_up", "delta_nii_try_mn"].iloc[0]
    down = summary.loc[summary["scenario"] == "parallel_down", "delta_nii_try_mn"].iloc[0]
    assert up == pytest.approx(-down)
    assert len(detail) == 2 * len(demo["positions"].query("side != 'equity'"))
