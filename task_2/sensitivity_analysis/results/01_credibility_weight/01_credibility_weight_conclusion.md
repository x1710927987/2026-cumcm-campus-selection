# 可信度权重参数灵敏度

## 情景汇总

| scenario_id | mae | rmse | smape | hit10 | total_relative_error | share_l1 | stock_mae | risk_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| volume_dominant | 1.7528 | 2.3647 | 0.4702 | 0.3347 | 0.0104 | 0.2377 | 6.1958 | 2.9000 |
| base_model | 1.7736 | 2.3761 | 0.4757 | 0.3236 | 0.0106 | 0.2404 | 6.2264 | 2.8000 |
| equal_weights | 1.8160 | 2.4277 | 0.4821 | 0.3167 | 0.0139 | 0.2470 | 6.3319 | 2.7667 |
| sparsity_dominant | 1.8306 | 2.4432 | 0.4845 | 0.3160 | 0.0151 | 0.2491 | 6.3208 | 2.9667 |
| stability_dominant | 1.8375 | 2.4509 | 0.4855 | 0.3146 | 0.0158 | 0.2502 | 6.2458 | 2.9000 |
| smoothness_dominant | 1.8389 | 2.4563 | 0.4861 | 0.3160 | 0.0164 | 0.2505 | 6.2167 | 2.9000 |

## 主要结论

- MAE 最优情景：`volume_dominant`，MAE=1.7528。
- RMSE 最优情景：`volume_dominant`，RMSE=2.3647。
- 小时结构 L1 最优情景：`volume_dominant`，ShareL1=0.2377。
- 库存轨迹误差最优情景：`volume_dominant`，StockMAE=6.1958。
- 基准模型在本组情景中的 MAE 排名为第 2 名，MAE=1.7736。

## 备注

- 本分析仅改变 lambda_1、lambda_2、lambda_3，theta 和可信度截断区间保持不变。
- MAE/RMSE 越低表示逐点预测越好，ShareL1 越低表示小时结构越接近真实值。

## 输出文件说明

- `01_credibility_weight_scenario_summary.csv`：情景级综合指标，最适合用于论文表格和可视化。
- `01_credibility_weight_overall_metrics.csv`：全体站点、借出/归还/综合三个层面的指标。
- `01_credibility_weight_station_metrics.csv`：站点层指标，可用于画站点改进图。
- `01_credibility_weight_zone_metrics.csv`：功能区层指标，可用于画功能区对比图。
- `01_credibility_weight_risk_metrics.csv`：库存轨迹和空桩/满桩风险指标。
- `01_credibility_weight_station_weights.csv`：站点可信度权重及其组成变量。
