# 极端值修正灵敏度

## 情景汇总

| scenario_id | mae | rmse | smape | hit10 | total_relative_error | share_l1 | stock_mae | risk_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| round_only | 1.7736 | 2.3761 | 0.4757 | 0.3236 | 0.0106 | 0.2404 | 6.2264 | 2.8000 |
| base_model | 1.7736 | 2.3761 | 0.4757 | 0.3236 | 0.0106 | 0.2404 | 6.2264 | 2.8000 |
| raw_continuous | 1.7797 | 2.3530 | 0.6369 | 0.2340 | 0.0090 | 0.2394 | 6.1256 | 2.6667 |
| nonnegative_continuous | 1.7797 | 2.3530 | 0.6369 | 0.2340 | 0.0090 | 0.2394 | 6.1256 | 2.6667 |

## 主要结论

- MAE 最优情景：`round_only`，MAE=1.7736。
- RMSE 最优情景：`nonnegative_continuous`，RMSE=2.3530。
- 小时结构 L1 最优情景：`nonnegative_continuous`，ShareL1=0.2394。
- 库存轨迹误差最优情景：`nonnegative_continuous`，StockMAE=6.1256。
- 基准模型在本组情景中的 MAE 排名为第 2 名，MAE=1.7736。

## 备注

- 本分析仅改变最终预测值的后处理规则。
- 连续型预测值有助于误差分析，但最终用于调度输入的需求矩阵应为非负整数。

## 输出文件说明

- `05_feasibility_correction_scenario_summary.csv`：情景级综合指标，最适合用于论文表格和可视化。
- `05_feasibility_correction_overall_metrics.csv`：全体站点、借出/归还/综合三个层面的指标。
- `05_feasibility_correction_station_metrics.csv`：站点层指标，可用于画站点改进图。
- `05_feasibility_correction_zone_metrics.csv`：功能区层指标，可用于画功能区对比图。
- `05_feasibility_correction_risk_metrics.csv`：库存轨迹和空桩/满桩风险指标。
- `05_feasibility_correction_station_weights.csv`：站点可信度权重及其组成变量。
