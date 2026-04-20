# 功能分区划分灵敏度

## 情景汇总

| scenario_id | mae | rmse | smape | hit10 | total_relative_error | share_l1 | stock_mae | risk_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_model | 1.7736 | 2.3761 | 0.4757 | 0.3236 | 0.0106 | 0.2404 | 6.2264 | 2.8000 |
| activity_tertile_zone | 1.7854 | 2.4082 | 0.4776 | 0.3264 | 0.0176 | 0.2433 | 6.1944 | 2.8667 |
| single_global_zone | 1.8194 | 2.4418 | 0.4786 | 0.3312 | 0.0009 | 0.2442 | 6.1375 | 2.7000 |
| capacity_tertile_zone | 1.8299 | 2.4669 | 0.4821 | 0.3326 | 0.0014 | 0.2458 | 6.2694 | 2.8333 |

## 主要结论

- MAE 最优情景：`base_model`，MAE=1.7736。
- RMSE 最优情景：`base_model`，RMSE=2.3761。
- 小时结构 L1 最优情景：`base_model`，ShareL1=0.2404。
- 库存轨迹误差最优情景：`single_global_zone`，StockMAE=6.1375。
- 基准模型在本组情景中的 MAE 排名为第 1 名，MAE=1.7736。

## 备注

- 本分析仅改变收缩模板中使用的站点到功能区映射关系。
- single_global_zone 用于检验功能区层是否确实有必要存在。
- activity_tertile_zone 和 capacity_tertile_zone 分别作为活动量驱动和桩位容量驱动的替代分区方案。

## 输出文件说明

- `06_zone_partition_scenario_summary.csv`：情景级综合指标，最适合用于论文表格和可视化。
- `06_zone_partition_overall_metrics.csv`：全体站点、借出/归还/综合三个层面的指标。
- `06_zone_partition_station_metrics.csv`：站点层指标，可用于画站点改进图。
- `06_zone_partition_zone_metrics.csv`：功能区层指标，可用于画功能区对比图。
- `06_zone_partition_risk_metrics.csv`：库存轨迹和空桩/满桩风险指标。
- `06_zone_partition_station_weights.csv`：站点可信度权重及其组成变量。
