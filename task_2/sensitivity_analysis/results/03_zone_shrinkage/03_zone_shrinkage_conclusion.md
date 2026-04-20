# 功能分区收缩强度灵敏度

## 情景汇总

| scenario_id | mae | rmse | smape | hit10 | total_relative_error | share_l1 | stock_mae | risk_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| theta_0_0_global_only | 1.7681 | 2.3667 | 0.4757 | 0.3250 | 0.0134 | 0.2402 | 6.3097 | 2.6333 |
| base_model | 1.7736 | 2.3761 | 0.4757 | 0.3236 | 0.0106 | 0.2404 | 6.2264 | 2.8000 |
| theta_0_8 | 1.7736 | 2.3793 | 0.4745 | 0.3257 | 0.0106 | 0.2405 | 6.2403 | 2.8667 |
| theta_0_5_balanced | 1.7757 | 2.3733 | 0.4760 | 0.3229 | 0.0118 | 0.2409 | 6.2083 | 2.7000 |
| theta_0_6 | 1.7771 | 2.3757 | 0.4759 | 0.3222 | 0.0113 | 0.2410 | 6.1833 | 2.7667 |
| theta_1_0_zone_only | 1.7799 | 2.3914 | 0.4733 | 0.3271 | 0.0109 | 0.2413 | 6.2625 | 2.9333 |

## 主要结论

- MAE 最优情景：`theta_0_0_global_only`，MAE=1.7681。
- RMSE 最优情景：`theta_0_0_global_only`，RMSE=2.3667。
- 小时结构 L1 最优情景：`theta_0_0_global_only`，ShareL1=0.2402。
- 库存轨迹误差最优情景：`theta_0_6`，StockMAE=6.1833。
- 基准模型在本组情景中的 MAE 排名为第 2 名，MAE=1.7736。

## 备注

- 本分析仅改变功能区模板与全局模板混合时的 theta_s。
- theta=1 表示站点信息被收缩时完全依赖功能区模板，theta=0 表示完全依赖全局模板。

## 输出文件说明

- `03_zone_shrinkage_scenario_summary.csv`：情景级综合指标，最适合用于论文表格和可视化。
- `03_zone_shrinkage_overall_metrics.csv`：全体站点、借出/归还/综合三个层面的指标。
- `03_zone_shrinkage_station_metrics.csv`：站点层指标，可用于画站点改进图。
- `03_zone_shrinkage_zone_metrics.csv`：功能区层指标，可用于画功能区对比图。
- `03_zone_shrinkage_risk_metrics.csv`：库存轨迹和空桩/满桩风险指标。
- `03_zone_shrinkage_station_weights.csv`：站点可信度权重及其组成变量。
