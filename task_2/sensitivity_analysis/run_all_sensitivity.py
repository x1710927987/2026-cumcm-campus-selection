"""Run all task 2 sensitivity analyses."""

from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd


MODULES = [
    "sensitivity_01_credibility_weight",
    "sensitivity_02_weight_clip",
    "sensitivity_03_zone_shrinkage",
    "sensitivity_04_global_template",
    "sensitivity_05_feasibility_correction",
    "sensitivity_06_zone_partition",
]

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = SCRIPT_DIR / "results"


def build_overview() -> None:
    frames = []
    for analysis_dir in sorted(path for path in RESULTS_ROOT.iterdir() if path.is_dir()):
        summary_files = list(analysis_dir.glob("*_scenario_summary.csv"))
        if not summary_files:
            continue
        frames.append(pd.read_csv(summary_files[0], encoding="utf-8-sig"))
    if not frames:
        return

    overview = pd.concat(frames, ignore_index=True)
    overview.to_csv(RESULTS_ROOT / "sensitivity_analysis_overview.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# Sensitivity Analysis Overview",
        "",
        "## 各类灵敏度分析的 MAE 最优情景",
        "",
        "| analysis | best_scenario | mae | rmse | share_l1 | stock_mae |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for analysis, group in overview.groupby("analysis", sort=True):
        best = group.sort_values(["mae", "rmse"]).iloc[0]
        lines.append(
            f"| {analysis} | {best['scenario_id']} | {best['mae']:.4f} | {best['rmse']:.4f} | {best['share_l1']:.4f} | {best['stock_mae']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## 使用说明",
            "",
            "- `sensitivity_analysis_overview.csv` 汇总所有情景级结果，适合做总表或综合可视化。",
            "- 各子目录中的 `*_scenario_summary.csv`、`*_station_metrics.csv`、`*_zone_metrics.csv` 和 `*_risk_metrics.csv` 适合做单项灵敏度图表。",
            "- 若论文篇幅有限，建议优先报告情景级综合表，并补充 1-2 张站点或功能区层面的可视化。",
        ]
    )
    (RESULTS_ROOT / "sensitivity_analysis_overview.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    for module_name in MODULES:
        print(f"Running {module_name}...")
        module = importlib.import_module(module_name)
        module.main()
    build_overview()
    print("All sensitivity analyses completed.")


if __name__ == "__main__":
    main()
