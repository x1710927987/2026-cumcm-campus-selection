"""Visualizations for the task 2 basic model.

The script reads structured outputs from ``task_2/basic_model/results`` and
writes PNG figures to ``task_2/visualizatioon/basic_model/results``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_DIR = SCRIPT_DIR.parents[1]
MODEL_RESULTS_DIR = TASK_DIR / "basic_model" / "results"
OUTPUT_DIR = SCRIPT_DIR / "results"

METHOD_ORDER = ["base1", "base2", "model"]
METHOD_LABELS = {
    "base1": "Base1: copy baseline day",
    "base2": "Base2: zone template",
    "model": "Proposed model",
    "actual": "Actual",
}
METHOD_COLORS = {
    "actual": "#111827",
    "base1": "#9CA3AF",
    "base2": "#F59E0B",
    "model": "#2563EB",
}
VARIABLE_LABELS = {"borrow": "Borrow", "return": "Return", "combined": "Combined"}
METRIC_LABELS = {
    "mae": "MAE",
    "rmse": "RMSE",
    "smape": "sMAPE",
    "hit10": "Hit10",
    "total_relative_error": "Total Relative Error",
    "share_l1": "Hourly Share L1",
    "stock_mae": "Stock MAE",
    "risk_diff": "Risk Difference",
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


def clean_zone(zone: str) -> str:
    return str(zone).split(" (", maxsplit=1)[0]


def read_csv(name: str) -> pd.DataFrame:
    path = MODEL_RESULTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing basic model output: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def savefig(name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    plt.savefig(path)
    plt.close()


def add_bar_labels(ax: plt.Axes, values: Iterable[float], fmt: str = "{:.3f}") -> None:
    for patch, value in zip(ax.patches, values):
        height = patch.get_height()
        ax.annotate(
            fmt.format(value),
            (patch.get_x() + patch.get_width() / 2, height),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#374151",
            xytext=(0, 2),
            textcoords="offset points",
        )


def plot_overall_metrics(overall: pd.DataFrame) -> None:
    combined = overall[overall["variable"] == "combined"].copy()
    metrics = ["mae", "rmse", "smape", "hit10", "total_relative_error", "share_l1"]

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for ax, metric in zip(axes.ravel(), metrics):
        data = combined.set_index("method").loc[METHOD_ORDER]
        values = data[metric].values
        ax.bar(METHOD_ORDER, values, color=[METHOD_COLORS[m] for m in METHOD_ORDER], width=0.62)
        ax.set_title(METRIC_LABELS[metric])
        ax.set_xticks(range(len(METHOD_ORDER)))
        ax.set_xticklabels([METHOD_LABELS[m].split(":")[0] for m in METHOD_ORDER], rotation=0)
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
        add_bar_labels(ax, values)
    fig.suptitle("Overall Metrics on Target Day: Combined Borrow and Return", fontsize=15, fontweight="bold")
    fig.tight_layout()
    savefig("01_overall_metrics_combined.png")


def plot_variable_metrics(overall: pd.DataFrame) -> None:
    metrics = ["mae", "rmse", "smape", "hit10"]
    variables = ["borrow", "return"]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    x = np.arange(len(variables))
    width = 0.24
    for ax, metric in zip(axes.ravel(), metrics):
        for offset, method in zip([-width, 0, width], METHOD_ORDER):
            values = [
                overall[(overall["variable"] == var) & (overall["method"] == method)][metric].iloc[0]
                for var in variables
            ]
            ax.bar(x + offset, values, width=width, label=METHOD_LABELS[method], color=METHOD_COLORS[method])
        ax.set_xticks(x)
        ax.set_xticklabels([VARIABLE_LABELS[var] for var in variables])
        ax.set_title(METRIC_LABELS[metric])
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Metrics by Borrow / Return", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig("02_metrics_by_variable.png")


def plot_station_improvement(station_metrics: pd.DataFrame) -> None:
    combined = station_metrics[station_metrics["variable"] == "combined"].copy()
    pivot = combined.pivot(index="station_id", columns="method", values="mae").sort_index()
    improvement_base1 = pivot["base1"] - pivot["model"]
    improvement_base2 = pivot["base2"] - pivot["model"]
    x = np.arange(len(pivot.index))

    fig, ax = plt.subplots(figsize=(16, 6))
    ax.axhline(0, color="#111827", linewidth=1)
    ax.bar(x - 0.18, improvement_base1, width=0.36, label="Base1 MAE - Model MAE", color="#2563EB")
    ax.bar(x + 0.18, improvement_base2, width=0.36, label="Base2 MAE - Model MAE", color="#F59E0B")
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")
    ax.set_ylabel("Positive value means model is better")
    ax.set_title("Station-Level MAE Improvement of Proposed Model")
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    savefig("03_station_mae_improvement.png")


def plot_station_metric_heatmap(station_metrics: pd.DataFrame) -> None:
    combined = station_metrics[station_metrics["variable"] == "combined"].copy()
    values = combined.pivot(index="station_id", columns="method", values="mae").loc[:, METHOD_ORDER]

    fig, ax = plt.subplots(figsize=(7, 11))
    image = ax.imshow(values.values, aspect="auto", cmap="YlGnBu")
    ax.set_xticks(np.arange(len(METHOD_ORDER)))
    ax.set_xticklabels([METHOD_LABELS[m].split(":")[0] for m in METHOD_ORDER])
    ax.set_yticks(np.arange(len(values.index)))
    ax.set_yticklabels(values.index)
    ax.set_title("Station-Level MAE Heatmap")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f"{values.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7, color="#111827")
    cbar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("MAE")
    fig.tight_layout()
    savefig("04_station_mae_heatmap.png")


def plot_zone_metrics(zone_metrics: pd.DataFrame) -> None:
    combined = zone_metrics[zone_metrics["variable"] == "combined"].copy()
    combined["zone_clean"] = combined["zone"].map(clean_zone)
    zones = combined["zone_clean"].drop_duplicates().tolist()
    metrics = ["mae", "rmse", "share_l1"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    x = np.arange(len(zones))
    width = 0.24
    for ax, metric in zip(axes, metrics):
        for offset, method in zip([-width, 0, width], METHOD_ORDER):
            values = []
            for zone in zones:
                row = combined[(combined["zone_clean"] == zone) & (combined["method"] == method)]
                values.append(row[metric].iloc[0])
            ax.bar(x + offset, values, width=width, label=METHOD_LABELS[method], color=METHOD_COLORS[method])
        ax.set_xticks(x)
        ax.set_xticklabels(zones, rotation=20, ha="right")
        ax.set_title(METRIC_LABELS[metric])
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Zone-Level Metrics: Combined Borrow and Return", fontsize=15, fontweight="bold", y=1.04)
    fig.tight_layout()
    savefig("05_zone_metrics_combined.png")


def plot_selected_hourly_fit(hourly: pd.DataFrame, selection: pd.DataFrame, variable: str) -> None:
    selected = selection["station_id"].tolist()
    fig, axes = plt.subplots(len(selected), 1, figsize=(14, 2.6 * len(selected)), sharex=True)
    if len(selected) == 1:
        axes = [axes]

    for ax, station in zip(axes, selected):
        data = hourly[(hourly["station_id"] == station) & (hourly["variable"] == variable)].sort_values("hour")
        reason = selection[selection["station_id"] == station]["selection_reason"].iloc[0]
        ax.plot(data["hour"], data["actual"], color=METHOD_COLORS["actual"], linewidth=2.0, marker="o", markersize=3, label="Actual")
        for method in METHOD_ORDER:
            ax.plot(
                data["hour"],
                data[f"{method}_pred"],
                color=METHOD_COLORS[method],
                linewidth=1.5,
                alpha=0.92,
                label=METHOD_LABELS[method].split(":")[0],
            )
        ax.set_title(f"{station} | {reason}")
        ax.set_ylabel(VARIABLE_LABELS[variable])
        ax.set_xticks(range(0, 24, 2))
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    axes[-1].set_xlabel("Hour")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    fig.suptitle(f"Selected Stations Hourly Fit: {VARIABLE_LABELS[variable]}", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    savefig(f"06_selected_hourly_fit_{variable}.png")


def plot_heatmap(hourly: pd.DataFrame, variable: str) -> None:
    data = hourly[hourly["variable"] == variable].copy()
    stations = sorted(data["station_id"].unique())
    actual = data.pivot(index="station_id", columns="hour", values="actual").loc[stations]
    model = data.pivot(index="station_id", columns="hour", values="model_pred").loc[stations]
    error = model - actual

    vmax = max(float(actual.max().max()), float(model.max().max()))
    abs_err = max(abs(float(error.min().min())), abs(float(error.max().max())))

    fig, axes = plt.subplots(1, 3, figsize=(18, 9), sharey=True)
    panels = [
        ("Actual", actual.values, "YlGnBu", 0, vmax),
        ("Model prediction", model.values, "YlGnBu", 0, vmax),
        ("Model - Actual", error.values, "RdBu_r", -abs_err, abs_err),
    ]
    for ax, (title, matrix, cmap, vmin, vmax_panel) in zip(axes, panels):
        im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax_panel)
        ax.set_title(title)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xticklabels(range(0, 24, 3))
        ax.set_xlabel("Hour")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    axes[0].set_yticks(np.arange(len(stations)))
    axes[0].set_yticklabels(stations)
    axes[0].set_ylabel("Station")
    fig.suptitle(f"Station-Hour Heatmap: {VARIABLE_LABELS[variable]}", fontsize=15, fontweight="bold")
    fig.tight_layout()
    savefig(f"07_heatmap_actual_model_error_{variable}.png")


def plot_zone_average_curves(hourly: pd.DataFrame) -> None:
    data = hourly.copy()
    data["zone_clean"] = data["zone"].map(clean_zone)
    zones = data["zone_clean"].drop_duplicates().tolist()
    variables = ["borrow", "return"]
    fig, axes = plt.subplots(len(zones), len(variables), figsize=(15, 3.2 * len(zones)), sharex=True)
    if len(zones) == 1:
        axes = np.array([axes])

    for i, zone in enumerate(zones):
        for j, variable in enumerate(variables):
            ax = axes[i, j]
            subset = data[(data["zone_clean"] == zone) & (data["variable"] == variable)]
            grouped = subset.groupby("hour")[["actual", "base1_pred", "base2_pred", "model_pred"]].mean()
            ax.plot(grouped.index, grouped["actual"], color=METHOD_COLORS["actual"], linewidth=2.2, label="Actual")
            ax.plot(grouped.index, grouped["base1_pred"], color=METHOD_COLORS["base1"], linewidth=1.6, label="Base1")
            ax.plot(grouped.index, grouped["base2_pred"], color=METHOD_COLORS["base2"], linewidth=1.6, label="Base2")
            ax.plot(grouped.index, grouped["model_pred"], color=METHOD_COLORS["model"], linewidth=1.8, label="Model")
            ax.set_title(f"{zone} | {VARIABLE_LABELS[variable]}")
            ax.set_xticks(range(0, 24, 3))
            ax.grid(axis="y")
            ax.grid(axis="x", visible=False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    fig.suptitle("Zone Average Hourly Curves", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig("08_zone_average_hourly_curves.png")


def plot_stock_trajectories(stock: pd.DataFrame, selection: pd.DataFrame) -> None:
    selected = selection["station_id"].tolist()
    fig, axes = plt.subplots(len(selected), 1, figsize=(14, 2.5 * len(selected)), sharex=True)
    if len(selected) == 1:
        axes = [axes]

    for ax, station in zip(axes, selected):
        subset = stock[stock["station_id"] == station].copy()
        reason = selection[selection["station_id"] == station]["selection_reason"].iloc[0]
        for method in ["actual", *METHOD_ORDER]:
            series = subset[subset["method"] == method].sort_values("hour")
            ax.plot(
                series["hour"],
                series["stock"],
                color=METHOD_COLORS[method],
                linewidth=2.0 if method in ("actual", "model") else 1.5,
                label=METHOD_LABELS[method].split(":")[0],
            )
        ax.set_title(f"{station} | {reason}")
        ax.set_ylabel("Stock")
        ax.set_xticks(range(0, 24, 2))
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    axes[-1].set_xlabel("Hour")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    fig.suptitle("Inventory Trajectory Comparison for Selected Stations", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    savefig("09_selected_stock_trajectories.png")


def plot_risk_metrics(risk: pd.DataFrame) -> None:
    stations = sorted(risk["station_id"].unique())
    x = np.arange(len(stations))
    width = 0.24

    fig, axes = plt.subplots(2, 1, figsize=(16, 9), sharex=True)
    for ax, metric in zip(axes, ["stock_mae", "risk_diff"]):
        for offset, method in zip([-width, 0, width], METHOD_ORDER):
            values = risk[risk["method"] == method].set_index("station_id").loc[stations, metric].values
            ax.bar(x + offset, values, width=width, label=METHOD_LABELS[method], color=METHOD_COLORS[method])
        ax.set_ylabel(METRIC_LABELS[metric])
        ax.set_title(METRIC_LABELS[metric])
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(stations, rotation=45, ha="right")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Operational Risk Metrics by Station", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig("10_risk_metrics_by_station.png")


def plot_selected_station_metric_cards(selected_metrics: pd.DataFrame) -> None:
    selected = selected_metrics[selected_metrics["variable"] == "combined"].copy()
    stations = selected["station_id"].drop_duplicates().tolist()
    metrics = ["mae", "rmse", "stock_mae"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    x = np.arange(len(stations))
    width = 0.24
    for ax, metric in zip(axes, metrics):
        for offset, method in zip([-width, 0, width], METHOD_ORDER):
            values = selected[selected["method"] == method].set_index("station_id").loc[stations, metric].values
            ax.bar(x + offset, values, width=width, color=METHOD_COLORS[method], label=METHOD_LABELS[method])
        ax.set_title(METRIC_LABELS[metric])
        ax.set_xticks(x)
        ax.set_xticklabels(stations, rotation=30, ha="right")
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Selected Station Metrics", fontsize=15, fontweight="bold", y=1.04)
    fig.tight_layout()
    savefig("11_selected_station_metrics.png")


def write_visualization_index(image_names: list[str]) -> None:
    rows = []
    descriptions = {
        "01_overall_metrics_combined.png": "Overall comparison of Base1, Base2, and the proposed model on combined borrow/return metrics.",
        "02_metrics_by_variable.png": "Borrow and return metrics shown separately.",
        "03_station_mae_improvement.png": "Station-level MAE improvement of the proposed model relative to Base1 and Base2.",
        "04_station_mae_heatmap.png": "Station-level MAE heatmap for the three prediction methods.",
        "05_zone_metrics_combined.png": "Functional-zone comparison under combined borrow/return metrics.",
        "06_selected_hourly_fit_borrow.png": "Hourly borrow curves for six objectively selected stations.",
        "06_selected_hourly_fit_return.png": "Hourly return curves for six objectively selected stations.",
        "07_heatmap_actual_model_error_borrow.png": "Station-hour borrow heatmap for actual values, model predictions, and errors.",
        "07_heatmap_actual_model_error_return.png": "Station-hour return heatmap for actual values, model predictions, and errors.",
        "08_zone_average_hourly_curves.png": "Average hourly curves by functional zone.",
        "09_selected_stock_trajectories.png": "Inventory trajectories driven by actual and predicted borrow/return values.",
        "10_risk_metrics_by_station.png": "Operational risk metrics by station.",
        "11_selected_station_metrics.png": "Metric summary for the six selected stations.",
    }
    for name in image_names:
        rows.append({"file_name": name, "description": descriptions.get(name, "")})
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "visualization_index.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    set_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    overall = read_csv("basic_model_results.csv")
    station_metrics = read_csv("basic_model_station_metrics.csv")
    zone_metrics = read_csv("basic_model_zone_metrics.csv")
    hourly = read_csv("basic_model_hourly_predictions.csv")
    risk = read_csv("basic_model_risk_metrics.csv")
    selection = read_csv("basic_model_station_selection.csv")
    stock = read_csv("basic_model_stock_trajectories.csv")
    selected_metrics = read_csv("basic_model_selected_station_metrics.csv")

    plot_overall_metrics(overall)
    plot_variable_metrics(overall)
    plot_station_improvement(station_metrics)
    plot_station_metric_heatmap(station_metrics)
    plot_zone_metrics(zone_metrics)
    plot_selected_hourly_fit(hourly, selection, "borrow")
    plot_selected_hourly_fit(hourly, selection, "return")
    plot_heatmap(hourly, "borrow")
    plot_heatmap(hourly, "return")
    plot_zone_average_curves(hourly)
    plot_stock_trajectories(stock, selection)
    plot_risk_metrics(risk)
    plot_selected_station_metric_cards(selected_metrics)

    image_names = sorted(path.name for path in OUTPUT_DIR.glob("*.png"))
    write_visualization_index(image_names)
    print(f"Generated {len(image_names)} figures in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
