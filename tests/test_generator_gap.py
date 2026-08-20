import pandas as pd

from aurelia_alm.gap import maturity_gap, repricing_gap
from aurelia_alm.generator import build_cashflows, build_market_curves, build_portfolio


def test_portfolio_is_deterministic(config):
    first = build_portfolio(config, seed=123)
    second = build_portfolio(config, seed=123)
    pd.testing.assert_frame_equal(first, second)


def test_portfolio_accounting_identity(demo):
    positions = demo["positions"]
    assets = positions.loc[positions["side"] == "asset", "balance_try_mn"].sum()
    liabilities = positions.loc[positions["side"] == "liability", "balance_try_mn"].sum()
    equity = positions.loc[positions["side"] == "equity", "balance_try_mn"].sum()
    assert assets == 180_000
    assert abs(assets - liabilities - equity) < 1e-6


def test_expected_deposit_total(demo):
    positions = demo["positions"]
    deposits = positions.loc[
        positions["product"].isin(["demand_deposits", "term_deposits"]), "balance_try_mn"
    ].sum()
    assert deposits == 120_500


def test_cashflow_principal_reconciles(demo):
    positions = demo["positions"].set_index("position_id")
    principal = (
        demo["cashflows"]
        .loc[demo["cashflows"]["cashflow_type"] == "principal"]
        .groupby("position_id")["cashflow_try_mn"]
        .sum()
    )
    for position_id, amount in principal.items():
        sign = 1 if positions.loc[position_id, "side"] == "asset" else -1
        assert abs(amount - sign * positions.loc[position_id, "balance_try_mn"]) < 1e-4


def test_cashflows_exclude_equity(config):
    positions = build_portfolio(config)
    cashflows = build_cashflows(positions)
    equity_ids = set(positions.loc[positions["side"] == "equity", "position_id"])
    assert equity_ids.isdisjoint(set(cashflows["position_id"]))


def test_market_curves_have_governed_shape(config):
    curves = build_market_curves(config)
    assert len(curves) == 57
    assert set(curves.groupby("currency").size()) == {19}


def test_repricing_gap_preserves_balance(demo):
    result = repricing_gap(demo["positions"])
    assets = result["asset_try_mn"].sum()
    liabilities = result["liability_try_mn"].sum()
    assert abs(assets - 180_000) < 1e-6
    assert abs(liabilities - 157_500) < 1e-6
    assert list(
        result.groupby("currency")["bucket_order"].apply(lambda x: x.is_monotonic_increasing)
    ) == [True, True, True]


def test_maturity_gap_has_all_currencies(demo):
    result = maturity_gap(demo["positions"])
    assert set(result["currency"]) == {"TRY", "USD", "EUR"}
    assert "cumulative_gap_try_mn" in result
