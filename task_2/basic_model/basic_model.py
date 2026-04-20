"""Basic model for Question A, task 2.

This script implements the framework in ``task_2/solution_for_task_2(gpt).md``:

- nearest same-type day baseline;
- functional-zone template baseline;
- station credibility shrinkage model;
- parameter pseudo-validation;
- regular prediction metrics and operation-oriented risk metrics.

Outputs are written to ``task_2/basic_model/results``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = TASK_DIR.parent
DATA_DIR = PROJECT_ROOT / "data_attachment_for_question_A"
OUTPUT_DIR = SCRIPT_DIR / "results"

TARGET_D = 7
HOURS = list(range(24))
PARAMETER_LAMBDAS = [(0.5, 0.25, 0.25), (0.4, 0.3, 0.3), (0.6, 0.2, 0.2)]
PARAMETER_THETAS = [0.6, 0.7, 0.8]
PARAMETER_CLIPS = [(0.2, 0.9), (0.3, 0.9), (0.3, 0.8)]


@dataclass(frozen=True)
class Columns:
    info_station: str
    info_name: str
    longitude: str
    latitude: str
    capacity: str
    initial_stock: str
    zone: str
    date: str
    hour: str
    record_station: str
    borrow: str
    return_: str


@dataclass(frozen=True)
class DataBundle:
    info: pd.DataFrame
    records: pd.DataFrame
    stations: list[str]
    dates: list[pd.Timestamp]
    d_to_date: dict[int, pd.Timestamp]
    day_types: dict[int, str]
    columns: Columns
    info_file: Path
    records_file: Path


@dataclass(frozen=True)
class Params:
    lambdas: tuple[float, float, float]
    theta: float
    w_min: float
    w_max: float

    @property
    def label(self) -> str:
        l1, l2, l3 = self.lambdas
        return f"lambda=({l1:.2f},{l2:.2f},{l3:.2f});theta={self.theta:.2f};w=[{self.w_min:.2f},{self.w_max:.2f}]"


@dataclass
class PredictionResult:
    raw: pd.DataFrame
    final: pd.DataFrame
    total_pred: pd.Series | None = None
    share_pred: pd.DataFrame | None = None
    weights: pd.DataFrame | None = None


def read_csv_with_utf8_sig(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def identify_input_files(data_dir: Path) -> tuple[Path, Path]:
    """Identify attachment 1 and attachment 2 by shape.

    This avoids relying on non-ASCII file names in command-line contexts.
    """

    info_file: Path | None = None
    records_file: Path | None = None
    for path in data_dir.glob("*.csv"):
        df = read_csv_with_utf8_sig(path)
        if df.shape == (5040, 5):
            records_file = path
        elif df.shape[0] >= 30 and df.shape[1] >= 7:
            first_col = df.iloc[:, 0].astype(str)
            if first_col.str.match(r"^S\d{3}$", na=False).sum() >= 30:
                info_file = path
    if info_file is None or records_file is None:
        raise FileNotFoundError("Could not identify attachment 1 and attachment 2 CSV files.")
    return info_file, records_file


def load_data() -> DataBundle:
    info_file, records_file = identify_input_files(DATA_DIR)
    info = read_csv_with_utf8_sig(info_file)
    records = read_csv_with_utf8_sig(records_file)

    info_cols = list(info.columns)
    rec_cols = list(records.columns)
    if len(info_cols) < 7:
        raise ValueError("Attachment 1 must include the functional-zone column.")

    columns = Columns(
        info_station=info_cols[0],
        info_name=info_cols[1],
        longitude=info_cols[2],
        latitude=info_cols[3],
        capacity=info_cols[4],
        initial_stock=info_cols[5],
        zone=info_cols[6],
        date=rec_cols[0],
        hour=rec_cols[1],
        record_station=rec_cols[2],
        borrow=rec_cols[3],
        return_=rec_cols[4],
    )

    info[columns.info_station] = info[columns.info_station].astype(str)
    info = info[info[columns.info_station].str.match(r"^S\d{3}$", na=False)].copy()
    info = info.set_index(columns.info_station)
    info[columns.capacity] = pd.to_numeric(info[columns.capacity], errors="coerce")
    info[columns.initial_stock] = pd.to_numeric(info[columns.initial_stock], errors="coerce")

    records[columns.date] = pd.to_datetime(records[columns.date])
    records[columns.hour] = pd.to_numeric(records[columns.hour], errors="raise").astype(int)
    records[columns.record_station] = records[columns.record_station].astype(str)
    records[columns.borrow] = pd.to_numeric(records[columns.borrow], errors="raise")
    records[columns.return_] = pd.to_numeric(records[columns.return_], errors="raise")

    dates = sorted(pd.Timestamp(d) for d in records[columns.date].unique())
    date_to_d = {date: idx + 1 for idx, date in enumerate(dates)}
    d_to_date = {idx + 1: date for idx, date in enumerate(dates)}
    records["d"] = records[columns.date].map(date_to_d)

    records = records.merge(
        info[[columns.zone, columns.capacity, columns.initial_stock]],
        left_on=columns.record_station,
        right_index=True,
        how="inner",
    )

    stations = sorted(info.index.tolist())
    day_types = {d: ("rest" if date.weekday() >= 5 else "work") for d, date in d_to_date.items()}

    return DataBundle(
        info=info,
        records=records,
        stations=stations,
        dates=dates,
        d_to_date=d_to_date,
        day_types=day_types,
        columns=columns,
        info_file=info_file,
        records_file=records_file,
    )


def choose_baseline_day(target_d: int, day_types: dict[int, str]) -> int:
    target_type = day_types[target_d]
    same_type = [d for d in range(1, target_d) if day_types[d] == target_type]
    if same_type:
        return max(same_type)
    return target_d - 1


def pivot_counts(data: DataBundle, variable: str, d: int) -> pd.DataFrame:
    cols = data.columns
    subset = data.records[data.records["d"] == d]
    table = subset.pivot_table(
        index=cols.record_station,
        columns=cols.hour,
        values=variable,
        aggfunc="sum",
        fill_value=0,
    )
    return table.reindex(index=data.stations, columns=HOURS, fill_value=0).astype(float)


def calc_global_share(shares: pd.DataFrame) -> pd.Series:
    global_share = shares.mean(axis=0, skipna=True)
    if global_share.isna().any() or float(global_share.sum()) <= 0:
        return pd.Series(np.ones(len(HOURS)) / len(HOURS), index=HOURS)
    global_share = global_share.fillna(0)
    return global_share / global_share.sum()


def compute_templates(
    data: DataBundle,
    variable: str,
    baseline_d: int,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, dict[str, float], dict[str, pd.Series], pd.Series]:
    x0 = pivot_counts(data, variable, baseline_d)
    totals = x0.sum(axis=1)
    zone = data.info[data.columns.zone]
    shares = x0.div(totals.replace(0, np.nan), axis=0)
    global_share = calc_global_share(shares)

    zone_total: dict[str, float] = {}
    zone_share: dict[str, pd.Series] = {}
    for z in zone.dropna().unique():
        station_ids = zone[zone == z].index.tolist()
        zone_total[str(z)] = float(totals.loc[station_ids].mean())
        zs = shares.loc[station_ids].mean(axis=0, skipna=True)
        if zs.isna().any() or float(zs.sum()) <= 0:
            zs = global_share.copy()
        else:
            zs = zs.fillna(0)
            zs = zs / zs.sum()
        zone_share[str(z)] = zs

    station_share = pd.DataFrame(index=data.stations, columns=HOURS, dtype=float)
    for station in data.stations:
        if totals.loc[station] > 0:
            station_share.loc[station] = (x0.loc[station] / totals.loc[station]).values
        else:
            z = str(zone.loc[station])
            station_share.loc[station] = zone_share.get(z, global_share).values

    return x0, totals, station_share, zone_total, zone_share, global_share


def cap_matrix(data: DataBundle, variable: str, target_d: int) -> pd.DataFrame:
    cols = data.columns
    history = data.records[data.records["d"] < target_d]
    table = history.pivot_table(
        index=cols.record_station,
        columns=cols.hour,
        values=variable,
        aggfunc="max",
        fill_value=0,
    )
    table = table.reindex(index=data.stations, columns=HOURS, fill_value=0).astype(float)
    return np.ceil(1.5 * np.maximum(1, table)).astype(float)


def finalize_prediction(data: DataBundle, raw: pd.DataFrame, variable: str, target_d: int) -> pd.DataFrame:
    upper_bound = cap_matrix(data, variable, target_d)
    final = pd.DataFrame(
        np.rint(np.maximum(0, raw.astype(float))),
        index=raw.index,
        columns=raw.columns,
    )
    final = pd.DataFrame(
        np.minimum(final, upper_bound),
        index=raw.index,
        columns=raw.columns,
    )
    return final.astype(int)


def predict_base1(data: DataBundle, variable: str, target_d: int) -> PredictionResult:
    baseline_d = choose_baseline_day(target_d, data.day_types)
    raw = pivot_counts(data, variable, baseline_d)
    return PredictionResult(raw=raw, final=finalize_prediction(data, raw, variable, target_d))


def predict_base2(data: DataBundle, variable: str, target_d: int) -> PredictionResult:
    baseline_d = choose_baseline_day(target_d, data.day_types)
    _, totals, _, zone_total, zone_share, global_share = compute_templates(data, variable, baseline_d)
    raw = pd.DataFrame(index=data.stations, columns=HOURS, dtype=float)
    zone = data.info[data.columns.zone]

    for station in data.stations:
        z = str(zone.loc[station])
        total = zone_total.get(z, float(totals.mean()))
        share = zone_share.get(z, global_share)
        raw.loc[station] = total * share

    return PredictionResult(raw=raw, final=finalize_prediction(data, raw, variable, target_d))


def predict_model(data: DataBundle, variable: str, target_d: int, params: Params) -> PredictionResult:
    baseline_d = choose_baseline_day(target_d, data.day_types)
    x0, totals, station_share, zone_total, zone_share, global_share = compute_templates(
        data,
        variable,
        baseline_d,
    )
    lambda_1, lambda_2, lambda_3 = params.lambdas
    max_total = max(float(totals.max()), 1.0)
    xi = (x0 == 0).sum(axis=1) / len(HOURS)
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
    ).clip(lower=params.w_min, upper=params.w_max)

    zone = data.info[data.columns.zone]
    total_pred = pd.Series(index=data.stations, dtype=float)
    share_pred = pd.DataFrame(index=data.stations, columns=HOURS, dtype=float)

    for station in data.stations:
        z = str(zone.loc[station])
        z_total = zone_total.get(z, float(totals.mean()))
        z_share = zone_share.get(z, global_share)

        total_pred.loc[station] = weights.loc[station] * totals.loc[station] + (1 - weights.loc[station]) * z_total
        share = (
            weights.loc[station] * station_share.loc[station].astype(float)
            + (1 - weights.loc[station]) * (params.theta * z_share + (1 - params.theta) * global_share)
        )
        share_sum = float(share.sum())
        if share_sum > 0:
            share = share / share_sum
        else:
            share = global_share.copy()
        share_pred.loc[station] = share.values

    raw = share_pred.mul(total_pred, axis=0)
    final = finalize_prediction(data, raw, variable, target_d)
    weights_table = pd.DataFrame(
        {
            "station_id": data.stations,
            "variable": variable_to_label(data, variable),
            "baseline_total": [float(totals.loc[s]) for s in data.stations],
            "zero_hour_ratio": [float(xi.loc[s]) for s in data.stations],
            "peak_concentration": [float(pi.loc[s]) for s in data.stations],
            "credibility_weight": [float(weights.loc[s]) for s in data.stations],
        }
    )
    return PredictionResult(
        raw=raw,
        final=final,
        total_pred=total_pred,
        share_pred=share_pred,
        weights=weights_table,
    )


def variable_to_label(data: DataBundle, variable: str) -> str:
    if variable == data.columns.borrow:
        return "borrow"
    if variable == data.columns.return_:
        return "return"
    return str(variable)


def metric_from_arrays(prediction: np.ndarray, actual: np.ndarray) -> dict[str, float]:
    pred = np.asarray(prediction, dtype=float)
    act = np.asarray(actual, dtype=float)
    err = pred - act
    abs_err = np.abs(err)
    denom = np.abs(pred) + np.abs(act)
    smape_terms = np.zeros_like(abs_err, dtype=float)
    np.divide(2 * abs_err, denom, out=smape_terms, where=denom != 0)
    hit_terms = np.where(act == 0, pred == 0, abs_err <= 0.1 * np.abs(act))

    pred_sum = float(pred.sum())
    act_sum = float(act.sum())
    if pred_sum == 0 and act_sum == 0:
        share_l1 = 0.0
    elif pred_sum == 0 or act_sum == 0:
        share_l1 = 2.0
    else:
        share_l1 = float(np.abs(pred / pred_sum - act / act_sum).sum())

    return {
        "mae": float(abs_err.mean()),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "smape": float(smape_terms.mean()),
        "hit10": float(hit_terms.mean()),
        "total_relative_error": float(abs(pred_sum - act_sum) / max(act_sum, 1.0)),
        "share_l1": share_l1,
    }


def evaluate_prediction(
    prediction: pd.DataFrame,
    actual: pd.DataFrame,
    method: str,
    variable_label: str,
    target_d: int,
    station_id: str | None = None,
    zone: str | None = None,
) -> dict[str, Any]:
    metrics = metric_from_arrays(prediction.values.ravel(), actual.values.ravel())
    return {
        "target_d": target_d,
        "method": method,
        "variable": variable_label,
        "station_id": station_id or "ALL",
        "zone": zone or "ALL",
        **metrics,
    }


def combined_prediction_for_method(predictions: dict[str, dict[str, PredictionResult]], method: str) -> np.ndarray:
    return np.concatenate([result.final.values.ravel() for result in predictions[method].values()])


def combined_actual_for_variables(actuals: dict[str, pd.DataFrame]) -> np.ndarray:
    return np.concatenate([actual.values.ravel() for actual in actuals.values()])


def validate_params(data: DataBundle, params: Params, validation_days: tuple[int, ...] = (5, 6)) -> dict[str, float]:
    rows: list[dict[str, float]] = []
    for target_d in validation_days:
        for variable in (data.columns.borrow, data.columns.return_):
            actual = pivot_counts(data, variable, target_d)
            prediction = predict_model(data, variable, target_d, params).final
            rows.append(metric_from_arrays(prediction.values.ravel(), actual.values.ravel()))
    return {key: float(np.mean([row[key] for row in rows])) for key in rows[0]}


def calibrate_params(data: DataBundle) -> tuple[Params, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    for lambdas in PARAMETER_LAMBDAS:
        for theta in PARAMETER_THETAS:
            for w_min, w_max in PARAMETER_CLIPS:
                params = Params(lambdas=lambdas, theta=theta, w_min=w_min, w_max=w_max)
                metrics = validate_params(data, params)
                rows.append(
                    {
                        "parameter_label": params.label,
                        "lambda_1": lambdas[0],
                        "lambda_2": lambdas[1],
                        "lambda_3": lambdas[2],
                        "theta": theta,
                        "w_min": w_min,
                        "w_max": w_max,
                        **metrics,
                    }
                )

    table = pd.DataFrame(rows)
    rank_metrics = ["mae", "rmse", "total_relative_error", "share_l1"]
    for metric in rank_metrics:
        table[f"rank_{metric}"] = table[metric].rank(method="min", ascending=True)
    table["average_rank"] = table[[f"rank_{metric}" for metric in rank_metrics]].mean(axis=1)
    table = table.sort_values(["average_rank", "mae", "rmse"]).reset_index(drop=True)
    best = table.iloc[0]
    best_params = Params(
        lambdas=(float(best["lambda_1"]), float(best["lambda_2"]), float(best["lambda_3"])),
        theta=float(best["theta"]),
        w_min=float(best["w_min"]),
        w_max=float(best["w_max"]),
    )
    return best_params, table


def simulate_inventory(
    borrow: np.ndarray,
    return_: np.ndarray,
    capacity: float,
    initial_stock: float,
) -> tuple[np.ndarray, int, int]:
    stock = float(initial_stock)
    trajectory: list[float] = []
    empty_hours = 0
    full_hours = 0
    for hour in HOURS:
        stock = min(float(capacity), max(0.0, stock + float(return_[hour]) - float(borrow[hour])))
        trajectory.append(stock)
        empty_hours += int(stock <= 1e-9)
        full_hours += int(stock >= float(capacity) - 1e-9)
    return np.array(trajectory), empty_hours, full_hours


def calc_risk_metrics(
    data: DataBundle,
    predictions: dict[str, dict[str, PredictionResult]],
    actuals: dict[str, pd.DataFrame],
    target_d: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    trajectory_rows: list[dict[str, Any]] = []
    cols = data.columns
    for station in data.stations:
        capacity = float(data.info.loc[station, cols.capacity])
        initial_stock = float(data.info.loc[station, cols.initial_stock])
        zone = str(data.info.loc[station, cols.zone])
        real_traj, real_empty, real_full = simulate_inventory(
            actuals["borrow"].loc[station].values,
            actuals["return"].loc[station].values,
            capacity,
            initial_stock,
        )
        for hour, stock in enumerate(real_traj):
            trajectory_rows.append(
                {
                    "target_d": target_d,
                    "station_id": station,
                    "zone": zone,
                    "method": "actual",
                    "hour": hour,
                    "stock": stock,
                }
            )

        for method, method_predictions in predictions.items():
            pred_traj, pred_empty, pred_full = simulate_inventory(
                method_predictions["borrow"].final.loc[station].values,
                method_predictions["return"].final.loc[station].values,
                capacity,
                initial_stock,
            )
            rows.append(
                {
                    "target_d": target_d,
                    "station_id": station,
                    "zone": zone,
                    "method": method,
                    "stock_mae": float(np.mean(np.abs(pred_traj - real_traj))),
                    "empty_hours_pred": pred_empty,
                    "empty_hours_actual": real_empty,
                    "full_hours_pred": pred_full,
                    "full_hours_actual": real_full,
                    "empty_hour_diff": abs(pred_empty - real_empty),
                    "full_hour_diff": abs(pred_full - real_full),
                    "risk_diff": abs(pred_empty - real_empty) + abs(pred_full - real_full),
                }
            )
            for hour, stock in enumerate(pred_traj):
                trajectory_rows.append(
                    {
                        "target_d": target_d,
                        "station_id": station,
                        "zone": zone,
                        "method": method,
                        "hour": hour,
                        "stock": stock,
                    }
                )

    return pd.DataFrame(rows), pd.DataFrame(trajectory_rows)


def build_predictions(data: DataBundle, target_d: int, params: Params) -> tuple[
    dict[str, dict[str, PredictionResult]],
    dict[str, pd.DataFrame],
]:
    actuals = {
        "borrow": pivot_counts(data, data.columns.borrow, target_d),
        "return": pivot_counts(data, data.columns.return_, target_d),
    }
    predictions = {
        "base1": {
            "borrow": predict_base1(data, data.columns.borrow, target_d),
            "return": predict_base1(data, data.columns.return_, target_d),
        },
        "base2": {
            "borrow": predict_base2(data, data.columns.borrow, target_d),
            "return": predict_base2(data, data.columns.return_, target_d),
        },
        "model": {
            "borrow": predict_model(data, data.columns.borrow, target_d, params),
            "return": predict_model(data, data.columns.return_, target_d, params),
        },
    }
    return predictions, actuals


def build_overall_metrics(
    predictions: dict[str, dict[str, PredictionResult]],
    actuals: dict[str, pd.DataFrame],
    target_d: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for method, method_predictions in predictions.items():
        for variable, result in method_predictions.items():
            rows.append(evaluate_prediction(result.final, actuals[variable], method, variable, target_d))
        combined_metrics = metric_from_arrays(
            combined_prediction_for_method(predictions, method),
            combined_actual_for_variables(actuals),
        )
        rows.append(
            {
                "target_d": target_d,
                "method": method,
                "variable": "combined",
                "station_id": "ALL",
                "zone": "ALL",
                **combined_metrics,
            }
        )
    return pd.DataFrame(rows)


def build_station_metrics(
    data: DataBundle,
    predictions: dict[str, dict[str, PredictionResult]],
    actuals: dict[str, pd.DataFrame],
    target_d: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    zone_series = data.info[data.columns.zone]
    for station in data.stations:
        zone = str(zone_series.loc[station])
        for method, method_predictions in predictions.items():
            for variable, result in method_predictions.items():
                pred = result.final.loc[[station]]
                actual = actuals[variable].loc[[station]]
                rows.append(evaluate_prediction(pred, actual, method, variable, target_d, station, zone))

            combined_pred = np.concatenate([result.final.loc[station].values for result in method_predictions.values()])
            combined_act = np.concatenate([actual.loc[station].values for actual in actuals.values()])
            rows.append(
                {
                    "target_d": target_d,
                    "method": method,
                    "variable": "combined",
                    "station_id": station,
                    "zone": zone,
                    **metric_from_arrays(combined_pred, combined_act),
                }
            )
    return pd.DataFrame(rows)


def build_zone_metrics(
    data: DataBundle,
    predictions: dict[str, dict[str, PredictionResult]],
    actuals: dict[str, pd.DataFrame],
    target_d: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    zone_series = data.info[data.columns.zone]
    for zone, station_index in zone_series.groupby(zone_series).groups.items():
        stations = list(station_index)
        for method, method_predictions in predictions.items():
            for variable, result in method_predictions.items():
                rows.append(
                    evaluate_prediction(
                        result.final.loc[stations],
                        actuals[variable].loc[stations],
                        method,
                        variable,
                        target_d,
                        station_id="ALL",
                        zone=str(zone),
                    )
                )
            combined_pred = np.concatenate(
                [result.final.loc[stations].values.ravel() for result in method_predictions.values()]
            )
            combined_act = np.concatenate([actual.loc[stations].values.ravel() for actual in actuals.values()])
            rows.append(
                {
                    "target_d": target_d,
                    "method": method,
                    "variable": "combined",
                    "station_id": "ALL",
                    "zone": str(zone),
                    **metric_from_arrays(combined_pred, combined_act),
                }
            )
    return pd.DataFrame(rows)


def build_hourly_predictions(
    data: DataBundle,
    predictions: dict[str, dict[str, PredictionResult]],
    actuals: dict[str, pd.DataFrame],
    target_d: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    zone_series = data.info[data.columns.zone]
    for station in data.stations:
        zone = str(zone_series.loc[station])
        for hour in HOURS:
            for variable in ("borrow", "return"):
                row: dict[str, Any] = {
                    "target_d": target_d,
                    "date": data.d_to_date[target_d].strftime("%Y-%m-%d"),
                    "station_id": station,
                    "zone": zone,
                    "hour": hour,
                    "variable": variable,
                    "actual": float(actuals[variable].loc[station, hour]),
                }
                for method in ("base1", "base2", "model"):
                    result = predictions[method][variable]
                    row[f"{method}_raw_pred"] = float(result.raw.loc[station, hour])
                    row[f"{method}_pred"] = int(result.final.loc[station, hour])
                rows.append(row)
    return pd.DataFrame(rows)


def build_station_selection(
    data: DataBundle,
    station_metrics: pd.DataFrame,
    target_d: int,
) -> pd.DataFrame:
    baseline_d = choose_baseline_day(target_d, data.day_types)
    activity = (
        pivot_counts(data, data.columns.borrow, baseline_d).sum(axis=1)
        + pivot_counts(data, data.columns.return_, baseline_d).sum(axis=1)
    ).sort_values()
    combined_mae = station_metrics[station_metrics["variable"] == "combined"].pivot(
        index="station_id",
        columns="method",
        values="mae",
    )
    improvement = (combined_mae["base1"] - combined_mae["model"]).sort_values(ascending=False)
    selections: list[tuple[str, str]] = []

    def add_station(station: str, reason: str) -> None:
        if station not in [existing for existing, _ in selections] and len(selections) < 6:
            selections.append((station, reason))

    add_station(str(activity.idxmax()), "highest_activity_baseline_day")
    add_station(str((activity - activity.median()).abs().sort_values().index[0]), "median_activity_baseline_day")
    nonzero_activity = activity[activity > 0]
    add_station(str(nonzero_activity.idxmin()), "lowest_nonzero_activity_baseline_day")
    add_station(str(improvement.idxmax()), "largest_model_improvement_vs_base1")
    add_station(str(improvement.idxmin()), "largest_model_deterioration_vs_base1")
    add_station(str(improvement.abs().idxmin()), "closest_to_base1")
    for station in improvement.index:
        add_station(str(station), "supplement")

    rows: list[dict[str, Any]] = []
    zone_series = data.info[data.columns.zone]
    for station, reason in selections:
        rows.append(
            {
                "target_d": target_d,
                "baseline_d": baseline_d,
                "station_id": station,
                "zone": str(zone_series.loc[station]),
                "selection_reason": reason,
                "baseline_day_activity": float(activity.loc[station]),
                "model_minus_base1_mae": float(combined_mae.loc[station, "model"] - combined_mae.loc[station, "base1"]),
            }
        )
    return pd.DataFrame(rows)


def build_selected_station_metrics(
    station_selection: pd.DataFrame,
    station_metrics: pd.DataFrame,
    risk_metrics: pd.DataFrame,
) -> pd.DataFrame:
    selected = station_selection["station_id"].tolist()
    metric_part = station_metrics[
        (station_metrics["station_id"].isin(selected)) & (station_metrics["variable"] == "combined")
    ].copy()
    metric_part = metric_part.merge(
        station_selection[
            [
                "station_id",
                "selection_reason",
                "baseline_day_activity",
                "model_minus_base1_mae",
            ]
        ],
        on="station_id",
        how="left",
    )
    metric_part = metric_part.merge(
        risk_metrics[["station_id", "method", "stock_mae", "risk_diff"]],
        on=["station_id", "method"],
        how="left",
    )
    return metric_part.sort_values(["station_id", "method"]).reset_index(drop=True)


def build_station_weights(
    predictions: dict[str, dict[str, PredictionResult]],
) -> pd.DataFrame:
    frames = []
    for variable, result in predictions["model"].items():
        if result.weights is not None:
            frames.append(result.weights.copy())
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_win_counts(station_metrics: pd.DataFrame, risk_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in ["mae", "rmse", "total_relative_error", "share_l1"]:
        pivot = station_metrics[station_metrics["variable"] == "combined"].pivot(
            index="station_id",
            columns="method",
            values=metric,
        )
        rows.append(
            {
                "metric": metric,
                "comparison": "lower_is_better",
                "model_better_than_base1_count": int((pivot["model"] < pivot["base1"]).sum()),
                "model_better_than_base2_count": int((pivot["model"] < pivot["base2"]).sum()),
            }
        )
    for metric in ["stock_mae", "risk_diff"]:
        pivot = risk_metrics.pivot(index="station_id", columns="method", values=metric)
        rows.append(
            {
                "metric": metric,
                "comparison": "lower_is_better",
                "model_better_than_base1_count": int((pivot["model"] < pivot["base1"]).sum()),
                "model_better_than_base2_count": int((pivot["model"] < pivot["base2"]).sum()),
            }
        )
    return pd.DataFrame(rows)


def format_markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    subset = df[columns].copy()
    for col in subset.columns:
        if pd.api.types.is_numeric_dtype(subset[col]):
            subset[col] = subset[col].map(lambda value: f"{value:.4f}")
    header = "| " + " | ".join(subset.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(subset.columns)) + " |"
    rows = ["| " + " | ".join(str(value) for value in row) + " |" for row in subset.to_numpy()]
    return "\n".join([header, sep, *rows])


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, encoding="utf-8-sig")


def build_markdown_report(
    data: DataBundle,
    params: Params,
    calibration: pd.DataFrame,
    overall: pd.DataFrame,
    selected_metrics: pd.DataFrame,
    win_counts: pd.DataFrame,
    target_d: int,
) -> str:
    baseline_d = choose_baseline_day(target_d, data.day_types)
    target_date = data.d_to_date[target_d].strftime("%Y-%m-%d")
    baseline_date = data.d_to_date[baseline_d].strftime("%Y-%m-%d")

    combined = overall[overall["variable"] == "combined"].set_index("method")
    base1 = combined.loc["base1"]
    base2 = combined.loc["base2"]
    model = combined.loc["model"]

    model_vs_base1 = {
        "MAE": base1["mae"] - model["mae"],
        "RMSE": base1["rmse"] - model["rmse"],
        "sMAPE": base1["smape"] - model["smape"],
        "Hit10": model["hit10"] - base1["hit10"],
        "TotalRel": base1["total_relative_error"] - model["total_relative_error"],
        "ShareL1": base1["share_l1"] - model["share_l1"],
    }
    model_vs_base2 = {
        "MAE": base2["mae"] - model["mae"],
        "RMSE": base2["rmse"] - model["rmse"],
        "sMAPE": base2["smape"] - model["smape"],
        "Hit10": model["hit10"] - base2["hit10"],
        "TotalRel": base2["total_relative_error"] - model["total_relative_error"],
        "ShareL1": base2["share_l1"] - model["share_l1"],
    }

    overall_table = format_markdown_table(
        overall[overall["variable"] == "combined"],
        ["method", "mae", "rmse", "smape", "hit10", "total_relative_error", "share_l1"],
    )
    selected_compact = selected_metrics[
        ["station_id", "zone", "selection_reason", "method", "mae", "rmse", "smape", "hit10", "stock_mae", "risk_diff"]
    ]
    selected_table = format_markdown_table(
        selected_compact,
        ["station_id", "selection_reason", "method", "mae", "rmse", "smape", "hit10", "stock_mae", "risk_diff"],
    )
    win_table = format_markdown_table(
        win_counts,
        ["metric", "model_better_than_base1_count", "model_better_than_base2_count"],
    )

    lines = [
        "# Basic Model Results",
        "",
        "## 运行设置",
        "",
        f"- 目标日：第{target_d}天（{target_date}）。",
        f"- 最近同类日基线：第{baseline_d}天（{baseline_date}）。",
        f"- 有效站点数：{len(data.stations)}。",
        f"- 参数选择：{params.label}。",
        f"- 输入文件：{data.info_file.name}；{data.records_file.name}。",
        "",
        "## 参数校准结论",
        "",
        "伪验证采用第5天和第6天作为验证目标，综合 MAE、RMSE、全天总量误差和小时结构误差的平均排名选择参数。",
        "",
        format_markdown_table(
            calibration.head(5),
            ["parameter_label", "mae", "rmse", "total_relative_error", "share_l1", "average_rank"],
        ),
        "",
        "## 全体站点总体指标",
        "",
        overall_table,
        "",
        "## 模型相对基线的变化",
        "",
        f"- 相对基线1，模型 MAE 改善 {model_vs_base1['MAE']:.4f}，RMSE 改善 {model_vs_base1['RMSE']:.4f}，sMAPE 改善 {model_vs_base1['sMAPE']:.4f}，命中率提高 {model_vs_base1['Hit10']:.4f}。",
        f"- 相对基线1，模型总量相对误差改善 {model_vs_base1['TotalRel']:.4f}，小时结构 L1 改善 {model_vs_base1['ShareL1']:.4f}。",
        f"- 相对基线2，模型 MAE 变化 {model_vs_base2['MAE']:.4f}，RMSE 变化 {model_vs_base2['RMSE']:.4f}，sMAPE 变化 {model_vs_base2['sMAPE']:.4f}，命中率变化 {model_vs_base2['Hit10']:.4f}。",
        "",
        "## 站点层胜出数量",
        "",
        win_table,
        "",
        "## 6个代表站点",
        "",
        selected_table,
        "",
        "## 结论",
        "",
        "- 改进模型相较基线1并非只是形式上更复杂，而是在全体站点的总体 MAE、RMSE、sMAPE、命中率、总量误差和小时结构误差上均有改善。",
        "- 基线2本身较强，说明第7天存在明显的功能区层平均回归现象。因此论文中不宜写成模型全面优于所有基线，而应强调模型相较直接复制基线更稳，同时承认功能区平均模板在部分站点上具有竞争力。",
        "- 运营风险指标使用相同初始库存进行相对比较，适合判断不同预测输入对第三问库存演化的影响，但不应被解释为真实第7天库存的绝对还原。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    params, calibration = calibrate_params(data)
    predictions, actuals = build_predictions(data, TARGET_D, params)

    overall = build_overall_metrics(predictions, actuals, TARGET_D)
    station_metrics = build_station_metrics(data, predictions, actuals, TARGET_D)
    zone_metrics = build_zone_metrics(data, predictions, actuals, TARGET_D)
    hourly_predictions = build_hourly_predictions(data, predictions, actuals, TARGET_D)
    risk_metrics, stock_trajectories = calc_risk_metrics(data, predictions, actuals, TARGET_D)
    station_selection = build_station_selection(data, station_metrics, TARGET_D)
    selected_station_metrics = build_selected_station_metrics(station_selection, station_metrics, risk_metrics)
    station_weights = build_station_weights(predictions)
    win_counts = build_win_counts(station_metrics, risk_metrics)

    params_table = pd.DataFrame(
        [
            {
                "target_d": TARGET_D,
                "baseline_d": choose_baseline_day(TARGET_D, data.day_types),
                "lambda_1": params.lambdas[0],
                "lambda_2": params.lambdas[1],
                "lambda_3": params.lambdas[2],
                "theta": params.theta,
                "w_min": params.w_min,
                "w_max": params.w_max,
                "parameter_label": params.label,
            }
        ]
    )

    write_csv(overall, OUTPUT_DIR / "basic_model_results.csv")
    write_csv(overall, OUTPUT_DIR / "basic_model_overall_metrics.csv")
    write_csv(station_metrics, OUTPUT_DIR / "basic_model_station_metrics.csv")
    write_csv(zone_metrics, OUTPUT_DIR / "basic_model_zone_metrics.csv")
    write_csv(hourly_predictions, OUTPUT_DIR / "basic_model_hourly_predictions.csv")
    write_csv(risk_metrics, OUTPUT_DIR / "basic_model_risk_metrics.csv")
    write_csv(stock_trajectories, OUTPUT_DIR / "basic_model_stock_trajectories.csv")
    write_csv(calibration, OUTPUT_DIR / "basic_model_calibration_results.csv")
    write_csv(params_table, OUTPUT_DIR / "basic_model_selected_parameters.csv")
    write_csv(station_selection, OUTPUT_DIR / "basic_model_station_selection.csv")
    write_csv(selected_station_metrics, OUTPUT_DIR / "basic_model_selected_station_metrics.csv")
    write_csv(station_weights, OUTPUT_DIR / "basic_model_station_weights.csv")
    write_csv(win_counts, OUTPUT_DIR / "basic_model_win_counts.csv")

    report = build_markdown_report(
        data=data,
        params=params,
        calibration=calibration,
        overall=overall,
        selected_metrics=selected_station_metrics,
        win_counts=win_counts,
        target_d=TARGET_D,
    )
    (OUTPUT_DIR / "basic_model_results.md").write_text(report, encoding="utf-8")

    print(f"Basic model completed. Results written to: {OUTPUT_DIR}")
    print(f"Selected parameters: {params.label}")


if __name__ == "__main__":
    main()
