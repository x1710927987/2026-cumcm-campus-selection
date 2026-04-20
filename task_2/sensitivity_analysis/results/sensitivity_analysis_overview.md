# Sensitivity Analysis Overview

## 各类灵敏度分析的 MAE 最优情景

| analysis | best_scenario | mae | rmse | share_l1 | stock_mae |
| --- | --- | --- | --- | --- | --- |
| 01_credibility_weight | volume_dominant | 1.7528 | 2.3647 | 0.2377 | 6.1958 |
| 02_weight_clip | narrow_clip_0_3_0_7 | 1.7403 | 2.3310 | 0.2367 | 6.1417 |
| 03_zone_shrinkage | theta_0_0_global_only | 1.7681 | 2.3667 | 0.2402 | 6.3097 |
| 04_global_template | global_only_template | 1.7681 | 2.3667 | 0.2402 | 6.3097 |
| 05_feasibility_correction | round_only | 1.7736 | 2.3761 | 0.2404 | 6.2264 |
| 06_zone_partition | base_model | 1.7736 | 2.3761 | 0.2404 | 6.2264 |

## 使用说明

- `sensitivity_analysis_overview.csv` 汇总所有情景级结果，适合做总表或综合可视化。
- 各子目录中的 `*_scenario_summary.csv`、`*_station_metrics.csv`、`*_zone_metrics.csv` 和 `*_risk_metrics.csv` 适合做单项灵敏度图表。
- 若论文篇幅有限，建议优先报告情景级综合表，并补充 1-2 张站点或功能区层面的可视化。
