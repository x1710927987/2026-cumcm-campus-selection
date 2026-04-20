"""Run all sensitivity-analysis visualization scripts."""

from __future__ import annotations

from pathlib import Path
import runpy

import pandas as pd


MODULES = [
    "visualize_01_credibility_weight",
    "visualize_02_weight_clip",
    "visualize_03_zone_shrinkage",
    "visualize_04_global_template",
    "visualize_05_feasibility_correction",
    "visualize_06_zone_partition",
]

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = SCRIPT_DIR / "results"


def build_overview_index() -> None:
    frames = []
    for index_file in sorted(RESULTS_ROOT.glob("*/*_visualization_index.csv")):
        frames.append(pd.read_csv(index_file, encoding="utf-8-sig"))
    if not frames:
        return
    overview = pd.concat(frames, ignore_index=True)
    overview.to_csv(RESULTS_ROOT / "sensitivity_visualization_index.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# Sensitivity Visualization Index",
        "",
        "| analysis | figure_count |",
        "| --- | --- |",
    ]
    for analysis, group in overview.groupby("analysis", sort=True):
        lines.append(f"| {analysis} | {len(group)} |")
    lines.extend(
        [
            "",
            "Each analysis directory contains the same six figure types: scenario overview, delta from base model, station MAE heatmap, zone MAE comparison, operational risk comparison, and MAE-stock tradeoff.",
        ]
    )
    (RESULTS_ROOT / "sensitivity_visualization_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    for module_name in MODULES:
        print(f"Running {module_name}...")
        runpy.run_module(module_name, run_name="__main__")
    build_overview_index()
    print("All sensitivity visualizations completed.")


if __name__ == "__main__":
    main()
