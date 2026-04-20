"""Shared visualization utilities for task 2 sensitivity analyses."""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_DIR = SCRIPT_DIR.parents[1]
INPUT_ROOT = TASK_DIR / "sensitivity_analysis" / "results"
OUTPUT_ROOT = SCRIPT_DIR / "results"

METRIC_LABELS = {
    "mae": "MAE",
    "rmse": "RMSE",
    "smape": "sMAPE",
    "hit10": "Hit10",
    "total_relative_error": "Total Rel. Error",
    "share_l1": "Hourly Share L1",
    "stock_mae": "Stock MAE",
    "risk_diff": "Risk Difference",
}
PANEL_METRICS = ["mae", "rmse", "smape", "hit10", "share_l1", "stock_mae"]
DELTA_METRICS = [
    "delta_vs_base_mae",
    "delta_vs_base_rmse",
    "delta_vs_base_smape",
    "delta_vs_base_hit10",
    "delta_vs_base_share_l1",
    "delta_vs_base_stock_mae",
]
LOWER_BETTER_DELTA = {
    "delta_vs_base_mae",
    "delta_vs_base_rmse",
    "delta_vs_base_smape",
    "delta_vs_base_total_relative_error",
    "delta_vs_base_share_l1",
    "delta_vs_base_stock_mae",
    "delta_vs_base_risk_diff",
}


def set_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": "#111827",
            "axes.titlecolor": "#111827",
            "axes.grid": True,
            "grid.color": "#E5E7EB",
            "grid.linewidth": 0.8,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "xtick.color": "#374151",
            "ytick.color": "#374151",
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        }
    )


def wrap_label(label: str, width: int = 18) -> str:
    return "\n".join(textwrap.wrap(str(label), width=width, break_long_words=False))


def clean_zone(zone: str) -> str:
    return str(zone).split(" (", maxsplit=1)[0]


def read_table(analysis_slug: str, suffix: str) -> pd.DataFrame:
    path = INPUT_ROOT / analysis_slug / f"{analysis_slug}_{suffix}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing sensitivity result file: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def load_analysis_tables(analysis_slug: str) -> dict[str, pd.DataFrame]:
    return {
        "summary": read_table(analysis_slug, "scenario_summary"),
        "station": read_table(analysis_slug, "station_metrics"),
        "zone": read_table(analysis_slug, "zone_metrics"),
        "risk": read_table(analysis_slug, "risk_metrics"),
        "weights": read_table(analysis_slug, "station_weights"),
    }


def output_dir(analysis_slug: str) -> Path:
    out = OUTPUT_ROOT / analysis_slug
    out.mkdir(parents=True, exist_ok=True)
    return out


def savefig(analysis_slug: str, filename: str) -> None:
    plt.savefig(output_dir(analysis_slug) / filename)
    plt.close()


def scenario_colors(n: int) -> list[str]:
    cmap = plt.get_cmap("tab10")
    return [cmap(i % 10) for i in range(n)]


def plot_scenario_metric_overview(analysis_slug: str, title: str, summary: pd.DataFrame) -> None:
    scenarios = summary["scenario_id"].tolist()
    colors = scenario_colors(len(scenarios))
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))

    for ax, metric in zip(axes.ravel(), PANEL_METRICS):
        values = summary[metric].values
        ax.bar(range(len(scenarios)), values, color=colors, width=0.68)
        ax.set_title(METRIC_LABELS[metric])
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([wrap_label(s, 16) for s in scenarios], rotation=30, ha="right")
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
        best_idx = int(np.argmax(values) if metric == "hit10" else np.argmin(values))
        ax.patches[best_idx].set_edgecolor("#111827")
        ax.patches[best_idx].set_linewidth(2.0)

    fig.suptitle(f"{title}: Scenario Metric Overview", fontsize=15, fontweight="bold")
    fig.tight_layout()
    savefig(analysis_slug, "01_scenario_metric_overview.png")


def plot_delta_vs_base(analysis_slug: str, title: str, summary: pd.DataFrame) -> None:
    available = [metric for metric in DELTA_METRICS if metric in summary.columns]
    if not available:
        return

    scenarios = summary["scenario_id"].tolist()
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for ax, delta_col in zip(axes.ravel(), available):
        values = summary[delta_col].values
        colors = ["#2563EB" if value < 0 else "#F59E0B" for value in values]
        if delta_col == "delta_vs_base_hit10":
            colors = ["#2563EB" if value > 0 else "#F59E0B" for value in values]
        ax.axhline(0, color="#111827", linewidth=1)
        ax.bar(range(len(scenarios)), values, color=colors, width=0.68)
        label = delta_col.replace("delta_vs_base_", "")
        ax.set_title(f"Delta {METRIC_LABELS.get(label, label)} vs Base")
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([wrap_label(s, 16) for s in scenarios], rotation=30, ha="right")
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    for ax in axes.ravel()[len(available):]:
        ax.axis("off")
    fig.suptitle(f"{title}: Change Relative to Base Model", fontsize=15, fontweight="bold")
    fig.tight_layout()
    savefig(analysis_slug, "02_delta_vs_base_model.png")


def plot_station_mae_heatmap(analysis_slug: str, title: str, station: pd.DataFrame) -> None:
    combined = station[station["variable"] == "combined"].copy()
    pivot = combined.pivot(index="station_id", columns="scenario_id", values="mae")
    scenario_order = combined.drop_duplicates("scenario_id")["scenario_id"].tolist()
    pivot = pivot.loc[sorted(pivot.index), scenario_order]

    fig_width = max(8, 1.5 * len(scenario_order))
    fig, ax = plt.subplots(figsize=(fig_width, 11))
    image = ax.imshow(pivot.values, aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([wrap_label(col, 13) for col in pivot.columns], rotation=35, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title(f"{title}: Station-Level MAE")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax.text(j, i, f"{pivot.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6.5, color="#111827")
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("MAE")
    fig.tight_layout()
    savefig(analysis_slug, "03_station_mae_heatmap.png")


def plot_zone_mae(analysis_slug: str, title: str, zone: pd.DataFrame) -> None:
    combined = zone[zone["variable"] == "combined"].copy()
    combined["zone_clean"] = combined["zone"].map(clean_zone)
    scenario_order = combined.drop_duplicates("scenario_id")["scenario_id"].tolist()
    zone_order = combined.drop_duplicates("zone_clean")["zone_clean"].tolist()

    fig_width = max(12, 2.3 * len(zone_order))
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    x = np.arange(len(zone_order))
    width = min(0.8 / max(len(scenario_order), 1), 0.22)
    offsets = (np.arange(len(scenario_order)) - (len(scenario_order) - 1) / 2) * width
    colors = scenario_colors(len(scenario_order))

    for offset, scenario, color in zip(offsets, scenario_order, colors):
        values = []
        for zone_name in zone_order:
            row = combined[(combined["zone_clean"] == zone_name) & (combined["scenario_id"] == scenario)]
            values.append(row["mae"].iloc[0] if not row.empty else np.nan)
        ax.bar(x + offset, values, width=width, label=wrap_label(scenario, 18), color=color)

    ax.set_xticks(x)
    ax.set_xticklabels([wrap_label(z, 16) for z in zone_order], rotation=20, ha="right")
    ax.set_ylabel("MAE")
    ax.set_title(f"{title}: Zone-Level MAE")
    ax.legend(frameon=False, ncol=min(3, len(scenario_order)))
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    savefig(analysis_slug, "04_zone_mae_comparison.png")


def plot_risk_comparison(analysis_slug: str, title: str, summary: pd.DataFrame, risk: pd.DataFrame) -> None:
    scenarios = summary["scenario_id"].tolist()
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))

    for ax, metric in zip(axes[:2], ["stock_mae", "risk_diff"]):
        values = summary.set_index("scenario_id").loc[scenarios, metric].values
        ax.bar(range(len(scenarios)), values, color=scenario_colors(len(scenarios)), width=0.68)
        ax.set_title(METRIC_LABELS[metric])
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([wrap_label(s, 14) for s in scenarios], rotation=35, ha="right")
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)

    pivot = risk.pivot_table(index="station_id", columns="scenario_id", values="stock_mae", aggfunc="mean")
    pivot = pivot.loc[sorted(pivot.index), scenarios]
    image = axes[2].imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    axes[2].set_title("Station Stock MAE")
    axes[2].set_xticks(range(len(scenarios)))
    axes[2].set_xticklabels([wrap_label(s, 12) for s in scenarios], rotation=35, ha="right")
    axes[2].set_yticks(range(len(pivot.index)))
    axes[2].set_yticklabels(pivot.index, fontsize=7)
    fig.colorbar(image, ax=axes[2], fraction=0.046, pad=0.02)
    fig.suptitle(f"{title}: Operational Risk Comparison", fontsize=15, fontweight="bold")
    fig.tight_layout()
    savefig(analysis_slug, "05_operational_risk_comparison.png")


def plot_tradeoff_scatter(analysis_slug: str, title: str, summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = scenario_colors(len(summary))
    ax.scatter(summary["mae"], summary["stock_mae"], s=80, color=colors, edgecolor="#111827", linewidth=0.8)
    for _, row in summary.iterrows():
        ax.annotate(
            row["scenario_id"],
            (row["mae"], row["stock_mae"]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )
    ax.set_xlabel("MAE")
    ax.set_ylabel("Stock MAE")
    ax.set_title(f"{title}: Prediction vs Operation Tradeoff")
    ax.grid(True)
    fig.tight_layout()
    savefig(analysis_slug, "06_mae_stock_tradeoff.png")


def write_index(analysis_slug: str, title: str) -> None:
    out = output_dir(analysis_slug)
    rows = []
    descriptions = {
        "01_scenario_metric_overview.png": "Scenario-level comparison across prediction and operation metrics.",
        "02_delta_vs_base_model.png": "Metric changes relative to the base model.",
        "03_station_mae_heatmap.png": "Station-level MAE heatmap across scenarios.",
        "04_zone_mae_comparison.png": "Zone-level MAE comparison across scenarios.",
        "05_operational_risk_comparison.png": "Inventory-risk comparison across scenarios.",
        "06_mae_stock_tradeoff.png": "Tradeoff between prediction MAE and inventory trajectory error.",
    }
    for image in sorted(out.glob("*.png")):
        rows.append({"analysis": analysis_slug, "title": title, "file_name": image.name, "description": descriptions.get(image.name, "")})
    pd.DataFrame(rows).to_csv(out / f"{analysis_slug}_visualization_index.csv", index=False, encoding="utf-8-sig")


def render_analysis(analysis_slug: str, title: str) -> None:
    set_style()
    tables = load_analysis_tables(analysis_slug)
    summary = tables["summary"]
    station = tables["station"]
    zone = tables["zone"]
    risk = tables["risk"]

    plot_scenario_metric_overview(analysis_slug, title, summary)
    plot_delta_vs_base(analysis_slug, title, summary)
    plot_station_mae_heatmap(analysis_slug, title, station)
    plot_zone_mae(analysis_slug, title, zone)
    plot_risk_comparison(analysis_slug, title, summary, risk)
    plot_tradeoff_scatter(analysis_slug, title, summary)
    write_index(analysis_slug, title)
    print(f"Rendered {analysis_slug} to {output_dir(analysis_slug)}")
