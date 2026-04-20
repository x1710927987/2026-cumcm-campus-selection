# 是否引入全局模板的灵敏度

## 情景汇总

| scenario_id | mae | rmse | smape | hit10 | total_relative_error | share_l1 | stock_mae | risk_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_only_template | 1.7681 | 2.3667 | 0.4757 | 0.3250 | 0.0134 | 0.2402 | 6.3097 | 2.6333 |
| base_model | 1.7736 | 2.3761 | 0.4757 | 0.3236 | 0.0106 | 0.2404 | 6.2264 | 2.8000 |
| half_zone_half_global | 1.7757 | 2.3733 | 0.4760 | 0.3229 | 0.0118 | 0.2409 | 6.2083 | 2.7000 |
| no_global_template | 1.7799 | 2.3914 | 0.4733 | 0.3271 | 0.0109 | 0.2413 | 6.2625 | 2.9333 |
| zone_only_via_theta | 1.7799 | 2.3914 | 0.4733 | 0.3271 | 0.0109 | 0.2413 | 6.2625 | 2.9333 |

## 主要结论

- MAE 最优情景：`global_only_template`，MAE=1.7681。
- RMSE 最优情景：`global_only_template`，RMSE=2.3667。
- 小时结构 L1 最优情景：`global_only_template`，ShareL1=0.2402。
- 库存轨迹误差最优情景：`half_zone_half_global`，StockMAE=6.2083。
- 基准模型在本组情景中的 MAE 排名为第 2 名，MAE=1.7736。

## 备注

- 本分析检验全局小时模板是否能稳定功能区模板。
- no_global_template 与 zone_only_via_theta 理论上应较接近，二者同时保留是为了做一致性检查。

## 输出文件说明

- `04_global_template_scenario_summary.csv`：情景级综合指标，最适合用于论文表格和可视化。
- `04_global_template_overall_metrics.csv`：全体站点、借出/归还/综合三个层面的指标。
- `04_global_template_station_metrics.csv`：站点层指标，可用于画站点改进图。
- `04_global_template_zone_metrics.csv`：功能区层指标，可用于画功能区对比图。
- `04_global_template_risk_metrics.csv`：库存轨迹和空桩/满桩风险指标。
- `04_global_template_station_weights.csv`：站点可信度权重及其组成变量。
