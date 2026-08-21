"""Reproducible analytical figures used by README and executive reporting."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

NAVY = "#0B1F33"
BLUE = "#1F5A94"
TEAL = "#00A6A6"
AMBER = "#F4A261"
RED = "#D1495B"
BURGUNDY = "#8C1C3A"
LIGHT = "#E8EEF4"
LIQUIDITY_COLORS = {
    "base": TEAL,
    "market_wide": BLUE,
    "idiosyncratic": AMBER,
    "combined": RED,
    "rapid_digital_run": BURGUNDY,
}


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#B7C3D0",
            "axes.labelcolor": NAVY,
            "axes.titlecolor": NAVY,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "grid.color": "#DDE5EC",
            "grid.linewidth": 0.7,
            "xtick.color": "#41566B",
            "ytick.color": "#41566B",
        }
    )


def create_figures(results: dict[str, pd.DataFrame], output_dir: str | Path) -> list[Path]:
    _style()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = [
        _plot_eve(results["eve"], output / "eve-sensitivity.png"),
        _plot_gap(results["repricing_gap"], output / "repricing-gap.png"),
        _plot_liquidity(results["liquidity"], output / "liquidity-stress.png"),
        _plot_fx(results["fx"], output / "fx-open-position.png"),
        _plot_executive(results, output / "executive-overview.png"),
    ]
    return paths


def _plot_eve(frame: pd.DataFrame, path: Path) -> Path:
    total = frame.loc[frame["currency"] == "TOTAL"].copy()
    total["scenario_label"] = total["scenario"].str.replace("_", " ").str.title()
    colors = [RED if value < 0 else TEAL for value in total["delta_eve_try_mn"]]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(total["scenario_label"], total["delta_eve_try_mn"], color=colors)
    ax.axhline(0, color=NAVY, linewidth=1)
    ax.set_title("IRRBB economic value sensitivity - six prescribed scenarios")
    ax.set_ylabel("Delta EVE (TRY million)")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y")
    ax.bar_label(bars, fmt="%+.0f", padding=3, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _plot_gap(frame: pd.DataFrame, path: Path) -> Path:
    pivot = frame.pivot_table(
        index="bucket_order", columns="currency", values="gap_try_mn", fill_value=0
    )
    labels = (
        frame[["bucket_order", "bucket"]]
        .drop_duplicates()
        .sort_values("bucket_order")["bucket"]
        .tolist()
    )
    fig, ax = plt.subplots(figsize=(12, 5.5))
    bottom = np.zeros(len(pivot))
    for currency, color in zip(("TRY", "USD", "EUR"), (BLUE, TEAL, AMBER), strict=True):
        values = pivot.get(currency, pd.Series(0, index=pivot.index)).to_numpy()
        ax.bar(labels, values, bottom=bottom, label=currency, color=color)
        bottom += values
    ax.axhline(0, color=NAVY, linewidth=1)
    ax.set_title("Contractual repricing gap by IRRBB time bucket")
    ax.set_ylabel("Assets less liabilities (TRY million)")
    ax.tick_params(axis="x", rotation=50)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _plot_liquidity(frame: pd.DataFrame, path: Path) -> Path:
    order = ["base", "market_wide", "idiosyncratic", "combined", "rapid_digital_run"]
    plotted = frame.set_index("scenario").reindex(order).reset_index()
    colors = [LIQUIDITY_COLORS[scenario] for scenario in plotted["scenario"]]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    bars = ax.bar(
        plotted["scenario"].str.replace("_", " ").str.title(),
        plotted["lcr_proxy_pct"],
        color=colors,
    )
    ax.axhline(100, color=NAVY, linestyle="--", linewidth=1.5, label="Illustrative 100% threshold")
    ax.set_title("Liquidity Coverage Ratio proxy under stress")
    ax.set_ylabel("LCR proxy (%)")
    ax.grid(axis="y")
    ax.legend(frameon=False)
    ax.bar_label(bars, fmt="%.0f%%", padding=3)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _plot_fx(frame: pd.DataFrame, path: Path) -> Path:
    colors = [TEAL if value >= 0 else RED for value in frame["net_open_position_try_mn"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    bars = ax.bar(frame["currency"], frame["net_open_position_try_mn"], color=colors, width=0.55)
    ax.axhline(0, color=NAVY, linewidth=1)
    ax.set_title("Structural foreign-exchange open position")
    ax.set_ylabel("Net open position (TRY million)")
    ax.grid(axis="y")
    ax.bar_label(bars, fmt="%+.0f", padding=3)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _plot_executive(results: dict[str, pd.DataFrame], path: Path) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    eve = results["eve"].loc[results["eve"]["currency"] == "TOTAL"]
    axes[0, 0].bar(
        eve["scenario"].str.replace("_", " "),
        eve["delta_eve_tier1_pct"],
        color=[RED if value < 0 else TEAL for value in eve["delta_eve_tier1_pct"]],
    )
    axes[0, 0].axhline(0, color=NAVY, linewidth=1)
    axes[0, 0].set_title("Delta EVE / Tier 1")
    axes[0, 0].set_ylabel("Percent")
    axes[0, 0].tick_params(axis="x", rotation=20)

    nii = results["nii"]
    axes[0, 1].bar(
        nii["scenario"].str.replace("_", " "),
        nii["delta_nii_pct"],
        color=[RED if value < 0 else TEAL for value in nii["delta_nii_pct"]],
        width=0.55,
    )
    axes[0, 1].axhline(0, color=NAVY, linewidth=1)
    axes[0, 1].set_title("One-year delta NII")
    axes[0, 1].set_ylabel("Percent")

    liquidity = results["liquidity"]
    axes[1, 0].bar(
        liquidity["scenario"].str.replace("_", " "),
        liquidity["lcr_proxy_pct"],
        color=[LIQUIDITY_COLORS.get(scenario, BLUE) for scenario in liquidity["scenario"]],
    )
    axes[1, 0].axhline(100, color=NAVY, linestyle="--")
    axes[1, 0].set_title("LCR proxy")
    axes[1, 0].set_ylabel("Percent")
    axes[1, 0].tick_params(axis="x", rotation=15)

    fx = results["fx"]
    axes[1, 1].bar(fx["currency"], fx["net_open_position_try_mn"], color=[TEAL, RED])
    axes[1, 1].axhline(0, color=NAVY, linewidth=1)
    axes[1, 1].set_title("FX open position")
    axes[1, 1].set_ylabel("TRY million")

    for ax in axes.flat:
        ax.grid(axis="y")
    fig.suptitle(
        "Aurelia Bank Treasury & ALM Risk Control Tower", fontsize=18, fontweight="bold", color=NAVY
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path
