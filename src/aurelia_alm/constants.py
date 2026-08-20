"""Controlled dimensions used across the analytical platform."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeBucket:
    label: str
    lower_years: float
    upper_years: float
    midpoint_years: float


IRRBB_BUCKETS: tuple[TimeBucket, ...] = (
    TimeBucket("ON", 0.0, 1 / 365, 1 / 730),
    TimeBucket("ON-1M", 1 / 365, 1 / 12, 1 / 24),
    TimeBucket("1M-3M", 1 / 12, 0.25, 1 / 6),
    TimeBucket("3M-6M", 0.25, 0.50, 0.375),
    TimeBucket("6M-9M", 0.50, 0.75, 0.625),
    TimeBucket("9M-1Y", 0.75, 1.0, 0.875),
    TimeBucket("1Y-1.5Y", 1.0, 1.5, 1.25),
    TimeBucket("1.5Y-2Y", 1.5, 2.0, 1.75),
    TimeBucket("2Y-3Y", 2.0, 3.0, 2.50),
    TimeBucket("3Y-4Y", 3.0, 4.0, 3.50),
    TimeBucket("4Y-5Y", 4.0, 5.0, 4.50),
    TimeBucket("5Y-6Y", 5.0, 6.0, 5.50),
    TimeBucket("6Y-7Y", 6.0, 7.0, 6.50),
    TimeBucket("7Y-8Y", 7.0, 8.0, 7.50),
    TimeBucket("8Y-9Y", 8.0, 9.0, 8.50),
    TimeBucket("9Y-10Y", 9.0, 10.0, 9.50),
    TimeBucket("10Y-15Y", 10.0, 15.0, 12.50),
    TimeBucket("15Y-20Y", 15.0, 20.0, 17.50),
    TimeBucket(">20Y", 20.0, float("inf"), 25.00),
)

LIQUIDITY_BUCKETS: tuple[tuple[str, int], ...] = (
    ("1D", 1),
    ("7D", 7),
    ("30D", 30),
    ("90D", 90),
    ("180D", 180),
    ("1Y", 365),
    (">1Y", 10_000),
)

CURRENCIES = ("TRY", "USD", "EUR")
EVE_SCENARIOS = (
    "parallel_up",
    "parallel_down",
    "steepener",
    "flattener",
    "short_up",
    "short_down",
)
NII_SCENARIOS = ("parallel_up", "parallel_down")


def bucket_for_years(years: float) -> TimeBucket:
    """Return the governed IRRBB bucket for a tenor in years."""
    if years < 0:
        raise ValueError("Tenor cannot be negative")
    for bucket in IRRBB_BUCKETS:
        if bucket.lower_years <= years < bucket.upper_years:
            return bucket
    return IRRBB_BUCKETS[-1]


def liquidity_bucket_for_days(days: int) -> str:
    """Return the first cumulative liquidity bucket containing the day count."""
    if days < 0:
        raise ValueError("Days cannot be negative")
    for label, upper in LIQUIDITY_BUCKETS:
        if days <= upper:
            return label
    return LIQUIDITY_BUCKETS[-1][0]
