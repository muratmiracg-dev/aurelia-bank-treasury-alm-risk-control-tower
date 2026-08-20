"""Illustrative, bounded hedge-sizing analysis for ALCO review."""

from __future__ import annotations

import pandas as pd


def propose_hedges(
    dv01: pd.DataFrame,
    fx_positions: pd.DataFrame,
    interest_rate_target_reduction: float = 0.50,
    fx_target_reduction: float = 0.80,
    reference_swap_duration_years: float = 4.0,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for row in dv01.loc[dv01["currency"] != "TOTAL"].itertuples(index=False):
        target_offset = -float(row.dv01_try_mn) * interest_rate_target_reduction
        notional = abs(target_offset) / (reference_swap_duration_years * 0.0001)
        direction = "PAY_FIXED_RECEIVE_FLOAT" if row.dv01_try_mn < 0 else "RECEIVE_FIXED_PAY_FLOAT"
        rows.append(
            {
                "risk_type": "IRRBB_DV01",
                "currency": row.currency,
                "instrument": "plain_vanilla_interest_rate_swap",
                "direction": direction,
                "recommended_notional_try_mn": notional,
                "pre_hedge_exposure": float(row.dv01_try_mn),
                "target_post_hedge_exposure": float(row.dv01_try_mn) + target_offset,
                "target_reduction_pct": 100.0 * interest_rate_target_reduction,
                "approval_status": "ALCO_REVIEW_REQUIRED",
            }
        )

    for row in fx_positions.itertuples(index=False):
        target_offset = -float(row.net_open_position_try_mn) * fx_target_reduction
        direction = "SELL_FX_BUY_TRY" if row.net_open_position_try_mn > 0 else "BUY_FX_SELL_TRY"
        rows.append(
            {
                "risk_type": "FX_OPEN_POSITION",
                "currency": row.currency,
                "instrument": "fx_swap_or_forward",
                "direction": direction,
                "recommended_notional_try_mn": abs(target_offset),
                "pre_hedge_exposure": float(row.net_open_position_try_mn),
                "target_post_hedge_exposure": float(row.net_open_position_try_mn) + target_offset,
                "target_reduction_pct": 100.0 * fx_target_reduction,
                "approval_status": "ALCO_REVIEW_REQUIRED",
            }
        )
    return pd.DataFrame(rows).round(6)
