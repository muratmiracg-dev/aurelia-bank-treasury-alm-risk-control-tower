"""Repricing and maturity gap analytics."""

from __future__ import annotations

import pandas as pd

from .constants import IRRBB_BUCKETS, bucket_for_years


def repricing_gap(portfolio: pd.DataFrame) -> pd.DataFrame:
    frame = portfolio.loc[portfolio["side"].isin(["asset", "liability"])].copy()
    frame["bucket"] = frame["repricing_years"].map(
        lambda value: bucket_for_years(float(value)).label
    )
    frame["asset_try_mn"] = frame["balance_try_mn"].where(frame["side"] == "asset", 0.0)
    frame["liability_try_mn"] = frame["balance_try_mn"].where(frame["side"] == "liability", 0.0)
    grouped = frame.groupby(["currency", "bucket"], as_index=False)[
        ["asset_try_mn", "liability_try_mn"]
    ].sum()
    order = {bucket.label: index for index, bucket in enumerate(IRRBB_BUCKETS)}
    grouped["bucket_order"] = grouped["bucket"].map(order)
    grouped["gap_try_mn"] = grouped["asset_try_mn"] - grouped["liability_try_mn"]
    grouped = grouped.sort_values(["currency", "bucket_order"])
    grouped["cumulative_gap_try_mn"] = grouped.groupby("currency")["gap_try_mn"].cumsum()
    return grouped.reset_index(drop=True)


def maturity_gap(portfolio: pd.DataFrame) -> pd.DataFrame:
    frame = portfolio.loc[portfolio["side"].isin(["asset", "liability"])].copy()
    frame["bucket"] = frame["maturity_years"].map(
        lambda value: bucket_for_years(float(value)).label
    )
    frame["signed_balance_try_mn"] = frame["balance_try_mn"].where(
        frame["side"] == "asset", -frame["balance_try_mn"]
    )
    grouped = frame.groupby(["currency", "bucket"], as_index=False)["signed_balance_try_mn"].sum()
    order = {bucket.label: index for index, bucket in enumerate(IRRBB_BUCKETS)}
    grouped["bucket_order"] = grouped["bucket"].map(order)
    grouped = grouped.sort_values(["currency", "bucket_order"])
    grouped["cumulative_gap_try_mn"] = grouped.groupby("currency")["signed_balance_try_mn"].cumsum()
    return grouped.reset_index(drop=True)
