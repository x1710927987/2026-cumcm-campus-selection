"""Shared utilities for task 2 sensitivity analysis scripts."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_DIR = SCRIPT_DIR.parent
BASIC_MODEL_DIR = TASK_DIR / "basic_model"
RESULTS_ROOT = SCRIPT_DIR / "results"

if str(BASIC_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(BASIC_MODEL_DIR))

import basic_model as bm  # noqa: E402


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    params: bm.Params
    use_global_template: bool = True
    finalization_mode: str = "cap"
    data: bm.DataBundle | None = None


def ensure_results_dir(analysis_slug: str) -> Path:
    output_dir = RESULTS_ROOT / analysis_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_base_params(data: bm.DataBundle | None = None) -> bm.Params:
    params_path = BASIC_MODEL_DIR / "results" / "basic_model_selected_parameters.csv"
    if params_path.exists():
        params_table = pd.read_csv(params_path, encoding="utf-8-sig")
        row = params_table.iloc[0]
        return bm.Params(
            lambdas=(float(row["lambda_1"]), float(row["lambda_2"]), float(row["lambda_3"])),
            theta=float(row["theta"]),
            w_min=float(row["w_min"]),
            w_max=float(row["w_max"]),
        )
    if data is None:
        data = bm.load_data()
    params, _ = bm.calibrate_params(data)
    return params


def finalize_variant(
    data: bm.DataBundle,
    raw: pd.DataFrame,
    variable: str,
    target_d: int,
    mode: str,
) -> pd.DataFrame:
    if mode == "cap":
        return bm.finalize_prediction(data, raw, variable, target_d)
    if mode == "round_only":
        return pd.DataFrame(
            np.rint(np.maximum(0, raw.astype(float))),
            index=raw.index,
            columns=raw.columns,
        ).astype(int)
    if mode == "nonnegative_continuous":
        return pd.DataFrame(
            np.maximum(0, raw.astype(float)),
            index=raw.index,
            columns=raw.columns,
        )
    if mode == "raw_continuous":
        return raw.astype(float)
    raise ValueError(f"Unknown finalization mode: {mode}")


def predict_model_variant(
    data: bm.DataBundle,
    variable: str,
    target_d: int,
    scenario: Scenario,
) -> bm.PredictionResult:
    baseline_d = bm.choose_baseline_day(target_d, data.day_types)
    x0, totals, station_share, zone_total, zone_share, global_share = bm.compute_templates(
        data,
        variable,
        baseline_d,
    )
    lambda_1, lambda_2, lambda_3 = scenario.params.lambdas
    max_total = max(float(totals.max()), 1.0)
    xi = (x0 == 0).sum(axis=1) / len(bm.HOURS)
    pi = pd.Series(index=data.stations, dtype=float)
    for station in data.stations:
        if totals.loc[station] > 0:
            pi.loc[station] = float(x0.loc[station].max() / totals.loc[station])
        else:
            pi.loc[station] = 1.0

    weights = (
        lambda_1 * (totals / max_total)
        + lambda_2 * (1 - xi)
        + lambda_3 * (1 - pi)
    ).clip(lower=scenario.params.w_min, upper=scenario.params.w_max)

    zone = data.info[data.columns.zone]
    total_pred = pd.Series(index=data.stations, dtype=float)
    share_pred = pd.DataFrame(index=data.stations, columns=bm.HOURS, dtype=float)

    for station in data.stations:
        z = str(zone.loc[station])
        z_total = zone_total.get(z, float(totals.mean()))
        z_share = zone_share.get(z, global_share)
        if scenario.use_global_template:
            template_share = scenario.params.theta * z_share + (1 - scenario.params.theta) * global_share
        else:
            template_share = z_share

        total_pred.loc[station] = weights.loc[station] * totals.loc[station] + (1 - weights.loc[station]) * z_total
        share = weights.loc[station] * station_share.loc[station].astype(float) + (1 - weights.loc[station]) * template_share
        share_sum = float(share.sum())
        if share_sum > 0:
            share = share / share_sum
        else:
            share = global_share.copy()
        share_pred.loc[station] = share.values

    raw = share_pred.mul(total_pred, axis=0)
    final = finalize_variant(data, raw, variable, target_d, scenario.finalization_mode)
    weights_table = pd.DataFrame(
        {
            "station_id": data.stations,
            "variable": bm.variable_to_label(data, variable),
            "baseline_total": [float(totals.loc[s]) for s in data.stations],
            "zero_hour_ratio": [float(xi.loc[s]) for s in data.stations],
            "peak_concentration": [float(pi.loc[s]) for s in data.stations],
            "credibility_weight": [float(weights.loc[s]) for s in data.stations],
            "scenario_id": scenario.scenario_id,
        }
    )
    return bm.PredictionResult(
        raw=raw,
        final=final,
        total_pred=total_pred,
        share_pred=share_pred,
        weights=weights_table,
    )


def build_predictions_for_scenario(
    data: bm.DataBundle,
    target_d: int,
    scenario: Scenario,
) -> tuple[dict[str, dict[str, bm.PredictionResult]], dict[str, pd.DataFrame]]:
    actuals = {
        "borrow": bm.pivot_counts(data, data.columns.borrow, target_d),
        "return": bm.pivot_counts(data, data.columns.return_, target_d),
    }
    predictions = {
        scenario.scenario_id: {
            "borrow": predict_model_variant(data, data.columns.borrow, target_d, scenario),
            "return": predict_model_variant(data, data.columns.return_, target_d, scenario),
        }
    }
    return predictions, actuals


def add_scenario_columns(df: pd.DataFrame, scenario: Scenario, analysis_slug: str) -> pd.DataFrame:
    output = df.copy()
    metadata_cols = [
        "analysis",
        "scenario_id",
        "scenario_description",
        "parameter_label",
        "use_global_template",
        "finalization_mode",
    ]
    output = output.drop(columns=[col for col in metadata_cols if col in output.columns])
    output.insert(0, "analysis", analysis_slug)
    output.insert(1, "scenario_id", scenario.scenario_id)
    output.insert(2, "scenario_description", scenario.description)
    output.insert(3, "parameter_label", scenario.params.label)
    output.insert(4, "use_global_template", scenario.use_global_template)
    output.insert(5, "finalization_mode", scenario.finalization_mode)
    return output


def evaluate_scenarios(
    analysis_slug: str,
    scenarios: list[Scenario],
    target_d: int = bm.TARGET_D,
) -> dict[str, pd.DataFrame]:
    overall_frames: list[pd.DataFrame] = []
    station_frames: list[pd.DataFrame] = []
    zone_frames: list[pd.DataFrame] = []
    risk_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []

    for scenario in scenarios:
        data = scenario.data or bm.load_data()
        predictions, actuals = build_predictions_for_scenario(data, target_d, scenario)
        overall_frames.append(add_scenario_columns(bm.build_overall_metrics(predictions, actuals, target_d), scenario, analysis_slug))
        station_frames.append(add_scenario_columns(bm.build_station_metrics(data, predictions, actuals, target_d), scenario, analysis_slug))
        zone_frames.append(add_scenario_columns(bm.build_zone_metrics(data, predictions, actuals, target_d), scenario, analysis_slug))
        risk_metrics, _ = bm.calc_risk_metrics(data, predictions, actuals, target_d)
        risk_frames.append(add_scenario_columns(risk_metrics, scenario, analysis_slug))
        weight_frames.append(add_scenario_columns(collect_station_weights(predictions), scenario, analysis_slug))

    overall = pd.concat(overall_frames, ignore_index=True)
    station = pd.concat(station_frames, ignore_index=True)
    zone = pd.concat(zone_frames, ignore_index=True)
    risk = pd.concat(risk_frames, ignore_index=True)
    weights = pd.concat(weight_frames, ignore_index=True)
    summary = build_summary(overall, risk)
    return {
        "overall_metrics": overall,
        "station_metrics": station,
        "zone_metrics": zone,
        "risk_metrics": risk,
        "station_weights": weights,
        "scenario_summary": summary,
    }


def collect_station_weights(predictions: dict[str, dict[str, bm.PredictionResult]]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for method, method_predictions in predictions.items():
        for _, result in method_predictions.items():
            if result.weights is not None:
                frame = result.weights.copy()
                frame["method"] = method
                frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_summary(overall: pd.DataFrame, risk: pd.DataFrame) -> pd.DataFrame:
    combined = overall[overall["variable"] == "combined"].copy()
    combined = combined[
        [
            "analysis",
            "scenario_id",
            "scenario_description",
            "parameter_label",
            "use_global_template",
            "finalization_mode",
            "mae",
            "rmse",
            "smape",
            "hit10",
            "total_relative_error",
            "share_l1",
        ]
    ]
    risk_summary = (
        risk.groupby(["analysis", "scenario_id"], as_index=False)
        .agg(stock_mae=("stock_mae", "mean"), risk_diff=("risk_diff", "mean"))
    )
    summary = combined.merge(risk_summary, on=["analysis", "scenario_id"], how="left")

    if "base_model" in set(summary["scenario_id"]):
        base = summary[summary["scenario_id"] == "base_model"].iloc[0]
        lower_better = ["mae", "rmse", "smape", "total_relative_error", "share_l1", "stock_mae", "risk_diff"]
        higher_better = ["hit10"]
        for metric in lower_better:
            summary[f"delta_vs_base_{metric}"] = summary[metric] - float(base[metric])
        for metric in higher_better:
            summary[f"delta_vs_base_{metric}"] = summary[metric] - float(base[metric])
    return summary.sort_values(["mae", "rmse"]).reset_index(drop=True)


def write_outputs(
    analysis_slug: str,
    title: str,
    outputs: dict[str, pd.DataFrame],
    notes: list[str] | None = None,
) -> Path:
    output_dir = ensure_results_dir(analysis_slug)
    for name, table in outputs.items():
        table.to_csv(output_dir / f"{analysis_slug}_{name}.csv", index=False, encoding="utf-8-sig")
    report = build_report(title, analysis_slug, outputs["scenario_summary"], notes or [])
    (output_dir / f"{analysis_slug}_conclusion.md").write_text(report, encoding="utf-8")
    return output_dir


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    subset = df[columns].copy()
    for col in subset.columns:
        if pd.api.types.is_numeric_dtype(subset[col]):
            subset[col] = subset[col].map(lambda value: f"{value:.4f}")
    header = "| " + " | ".join(subset.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(subset.columns)) + " |"
    rows = ["| " + " | ".join(str(value) for value in row) + " |" for row in subset.to_numpy()]
    return "\n".join([header, sep, *rows])


def build_report(title: str, analysis_slug: str, summary: pd.DataFrame, notes: list[str]) -> str:
    best_mae = summary.sort_values("mae").iloc[0]
    best_rmse = summary.sort_values("rmse").iloc[0]
    best_structure = summary.sort_values("share_l1").iloc[0]
    best_stock = summary.sort_values("stock_mae").iloc[0]
    columns = [
        "scenario_id",
        "mae",
        "rmse",
        "smape",
        "hit10",
        "total_relative_error",
        "share_l1",
        "stock_mae",
        "risk_diff",
    ]
    lines = [
        f"# {title}",
        "",
        "## 情景汇总",
        "",
        markdown_table(summary, columns),
        "",
        "## 主要结论",
        "",
        f"- MAE 最优情景：`{best_mae['scenario_id']}`，MAE={best_mae['mae']:.4f}。",
        f"- RMSE 最优情景：`{best_rmse['scenario_id']}`，RMSE={best_rmse['rmse']:.4f}。",
        f"- 小时结构 L1 最优情景：`{best_structure['scenario_id']}`，ShareL1={best_structure['share_l1']:.4f}。",
        f"- 库存轨迹误差最优情景：`{best_stock['scenario_id']}`，StockMAE={best_stock['stock_mae']:.4f}。",
    ]
    if "base_model" in set(summary["scenario_id"]):
        base = summary[summary["scenario_id"] == "base_model"].iloc[0]
        model_rank = int(summary.reset_index().set_index("scenario_id").loc["base_model", "index"]) + 1
        lines.append(f"- 基准模型在本组情景中的 MAE 排名为第 {model_rank} 名，MAE={base['mae']:.4f}。")
    if notes:
        lines.extend(["", "## 备注", ""])
        lines.extend([f"- {note}" for note in notes])
    lines.extend(
        [
            "",
            "## 输出文件说明",
            "",
            f"- `{analysis_slug}_scenario_summary.csv`：情景级综合指标，最适合用于论文表格和可视化。",
            f"- `{analysis_slug}_overall_metrics.csv`：全体站点、借出/归还/综合三个层面的指标。",
            f"- `{analysis_slug}_station_metrics.csv`：站点层指标，可用于画站点改进图。",
            f"- `{analysis_slug}_zone_metrics.csv`：功能区层指标，可用于画功能区对比图。",
            f"- `{analysis_slug}_risk_metrics.csv`：库存轨迹和空桩/满桩风险指标。",
            f"- `{analysis_slug}_station_weights.csv`：站点可信度权重及其组成变量。",
        ]
    )
    return "\n".join(lines) + "\n"


def clone_data_with_zone(data: bm.DataBundle, zone_series: pd.Series) -> bm.DataBundle:
    new_info = data.info.copy()
    new_records = data.records.copy()
    zone_series = zone_series.reindex(data.stations).astype(str)
    new_info[data.columns.zone] = zone_series
    new_records[data.columns.zone] = new_records[data.columns.record_station].map(zone_series)
    return bm.DataBundle(
        info=new_info,
        records=new_records,
        stations=data.stations.copy(),
        dates=data.dates.copy(),
        d_to_date=data.d_to_date.copy(),
        day_types=data.day_types.copy(),
        columns=data.columns,
        info_file=data.info_file,
        records_file=data.records_file,
    )


def activity_tertile_zones(data: bm.DataBundle, target_d: int = bm.TARGET_D) -> pd.Series:
    baseline_d = bm.choose_baseline_day(target_d, data.day_types)
    activity = (
        bm.pivot_counts(data, data.columns.borrow, baseline_d).sum(axis=1)
        + bm.pivot_counts(data, data.columns.return_, baseline_d).sum(axis=1)
    )
    labels = ["ActivityLow", "ActivityMid", "ActivityHigh"]
    ranks = activity.rank(method="first")
    return pd.Series(pd.qcut(ranks, q=3, labels=labels).astype(str).values, index=activity.index)


def capacity_tertile_zones(data: bm.DataBundle) -> pd.Series:
    capacity = data.info[data.columns.capacity].astype(float)
    labels = ["CapacityLow", "CapacityMid", "CapacityHigh"]
    ranks = capacity.rank(method="first")
    return pd.Series(pd.qcut(ranks, q=3, labels=labels).astype(str).values, index=capacity.index)


def global_single_zone(data: bm.DataBundle) -> pd.Series:
    return pd.Series("SingleGlobalZone", index=data.stations)
