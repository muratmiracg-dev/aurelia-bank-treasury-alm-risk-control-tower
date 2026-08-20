"""Structural foreign-exchange position and stress analytics."""

from __future__ import annotations

import pandas as pd


def fx_open_position(
    portfolio: pd.DataFrame,
    hedge_overlay: dict[str, float] | None = None,
) -> pd.DataFrame:
    frame = portfolio.loc[
        portfolio["currency"].ne("TRY") & portfolio["side"].isin(["asset", "liability"])
    ].copy()
    frame["signed_try_mn"] = frame["balance_try_mn"].where(
        frame["side"] == "asset", -frame["balance_try_mn"]
    )
    net = frame.groupby("currency", as_index=False)["signed_try_mn"].sum()
    net = net.rename(columns={"signed_try_mn": "gross_open_position_try_mn"})
    overlay = hedge_overlay or {}
    net["hedge_overlay_try_mn"] = net["currency"].map(overlay).fillna(0.0)
    net["net_open_position_try_mn"] = (
        net["gross_open_position_try_mn"] + net["hedge_overlay_try_mn"]
    )
    equity = float(portfolio.loc[portfolio["side"] == "equity", "balance_try_mn"].sum())
    net["open_position_equity_pct"] = 100.0 * net["net_open_position_try_mn"].abs() / equity
    for shock_pct in (-20.0, -10.0, 10.0, 20.0):
        label = f"fx_{shock_pct:+.0f}pct_pnl_try_mn".replace("+", "up_").replace("-", "down_")
        net[label] = net["net_open_position_try_mn"] * shock_pct / 100.0
    return net.round(6)


def aggregate_fx_limit_ratio(fx_positions: pd.DataFrame, equity_try_mn: float) -> float:
    return 100.0 * float(fx_positions["net_open_position_try_mn"].abs().sum()) / equity_try_mn
