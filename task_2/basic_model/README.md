# Basic Model 结果说明与论文写作指南

本目录用于存放问题二基础预测模型的代码、运行结果和结果解释。核心脚本为 `basic_model.py`，运行后会读取 `data_attachment_for_question_A` 中的附件数据，并在 `results` 目录下生成模型预测、基线比较、参数校准、站点层指标、功能区层指标和运营风险指标等结构化结果。

运行命令如下：

```powershell
python "D:\Repository\mathematical_modeling_competition\2026-cumcm-campus-selection\task_2\basic_model\basic_model.py"
```

当前模型评估对象为第7天，即 2025-04-13；最近同类日基线为第6天，即 2025-04-12。模型分别对借出量和归还量独立预测，再合并评价。

## 1. 方法名称约定

结果文件中统一使用以下 `method` 字段：

| method | 含义 | 论文表述建议 |
| --- | --- | --- |
| `base1` | 最近同类日直接复制，即直接使用第6天逐小时借还量预测第7天 | “直接复制基线”或“最近同类日复制基线” |
| `base2` | 功能区平均模板，即使用同功能区第6天平均总量和平均小时结构预测第7天 | “功能区平均模板基线” |
| `model` | 本文提出的“最近同类日基线 + 功能区层修正 + 站点可信度收缩”模型 | “本文模型”或“收缩修正模型” |

结果文件中统一使用以下 `variable` 字段：

| variable | 含义 |
| --- | --- |
| `borrow` | 借出量 |
| `return` | 归还量 |
| `combined` | 借出量与归还量合并后的总体指标 |

## 2. 指标字段说明

多个结果文件中会重复出现以下评价指标：

| 字段 | 含义 | 越大越好还是越小越好 | 论文用途 |
| --- | --- | --- | --- |
| `mae` | 平均绝对误差 | 越小越好 | 衡量逐小时预测平均偏差 |
| `rmse` | 均方根误差 | 越小越好 | 对大误差更敏感，适合说明峰值误差 |
| `smape` | 对称平均绝对百分比误差 | 越小越好 | 衡量相对误差，但在小流量站点上较敏感 |
| `hit10` | 预测值落入真实值 ±10% 范围的比例 | 越大越好 | 衡量逐点命中能力 |
| `total_relative_error` | 全天总量相对误差 | 越小越好 | 衡量站点或总体全天总量是否准确 |
| `share_l1` | 小时结构 L1 误差 | 越小越好 | 衡量24小时分布形状是否接近 |
| `stock_mae` | 预测借还量驱动库存轨迹与真实借还量驱动库存轨迹的平均差异 | 越小越好 | 服务第三问，评价预测输入对库存演化的影响 |
| `risk_diff` | 空桩小时差异与满桩小时差异之和 | 越小越好 | 服务第三问，评价运营风险判断是否接近 |

注意：`stock_mae` 和 `risk_diff` 是相对比较指标。它们使用相同初始库存进行模拟，适合比较不同预测方法对第三问库存演化的影响，但不应被解释为真实第7天库存的绝对还原。

## 3. results 目录文件说明

### 3.1 `basic_model_results.csv`

这是最重要的总体结果入口文件，记录三种方法在全体站点层面的预测指标。

文件规模：9 行，对应 3 种方法 × 3 类变量。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `target_d` | 目标预测日编号，当前为 7 |
| `method` | 预测方法，取 `base1`、`base2`、`model` |
| `variable` | 评价对象，取 `borrow`、`return`、`combined` |
| `station_id` | 当前文件为全体站点汇总，因此为 `ALL` |
| `zone` | 当前文件为全体功能区汇总，因此为 `ALL` |
| `mae`、`rmse`、`smape`、`hit10`、`total_relative_error`、`share_l1` | 常规预测评价指标 |

论文写作建议：

可以将 `variable=combined` 的三行整理为问题二的核心对比表。当前结果表明，本文模型相较 `base1` 在 MAE、RMSE、sMAPE、Hit10、总量误差和小时结构误差上均有改善；但 `base2` 在 MAE、RMSE 和小时结构 L1 上较强，因此不能写成“本文模型全面优于所有基线”。

### 3.2 `basic_model_overall_metrics.csv`

该文件与 `basic_model_results.csv` 当前内容一致，保留它是为了让文件名语义更清楚，便于后续脚本按“总体指标”读取。

论文写作时优先引用 `basic_model_results.csv` 或 `basic_model_overall_metrics.csv` 均可，但建议统一使用其中一个，避免表格来源混乱。

### 3.3 `basic_model_results.md`

这是非结构化结论文件，适合直接作为论文写作或答辩说明的参考。

主要内容包括：

| 部分 | 作用 |
| --- | --- |
| 运行设置 | 说明目标日、基线日、有效站点数和最终参数 |
| 参数校准结论 | 展示伪验证中排名靠前的参数组合 |
| 全体站点总体指标 | 展示三种方法的总体对比 |
| 模型相对基线的变化 | 直接给出模型相对 `base1` 和 `base2` 的改善或退化 |
| 站点层胜出数量 | 统计本文模型在多少个站点上优于两个基线 |
| 6个代表站点 | 展示客观选出的代表站点对比结果 |
| 结论 | 给出适合论文使用的谨慎结论 |

论文写作建议：

该文件中的“结论”部分可以直接转化为问题二结果分析的文字基础。尤其需要保留“本文模型相较直接复制基线更稳，但功能区平均模板在部分站点上有竞争力”这一表述。

### 3.4 `basic_model_calibration_results.csv`

该文件记录参数伪验证结果，用于说明模型参数不是完全主观设定。

文件规模：27 行，对应 3 组可信度权重 × 3 个功能区收缩强度 × 3 个可信度截断区间。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `parameter_label` | 参数组合的字符串标签 |
| `lambda_1`、`lambda_2`、`lambda_3` | 站点可信度中总量、零值占比、峰值集中度三项权重 |
| `theta` | 功能区模板在结构修正中的权重 |
| `w_min`、`w_max` | 站点可信度权重的截断上下界 |
| `mae`、`rmse`、`smape`、`hit10`、`total_relative_error`、`share_l1` | 伪验证阶段的平均指标 |
| `rank_mae`、`rank_rmse`、`rank_total_relative_error`、`rank_share_l1` | 各指标下的候选参数排名 |
| `average_rank` | 综合排名，用于选择最终参数 |

论文写作建议：

可以在“参数确定”或“模型求解”小节中说明：本文在有限候选参数组中进行伪验证，并综合 MAE、RMSE、总量误差和小时结构误差的平均排名选择最终参数。当前选出的参数为：

```text
lambda=(0.60,0.20,0.20); theta=0.70; w=[0.30,0.80]
```

这可以缓解“参数拍脑袋”的问题。

### 3.5 `basic_model_selected_parameters.csv`

该文件只记录最终选中的参数组合。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `target_d` | 目标预测日 |
| `baseline_d` | 最近同类日基线 |
| `lambda_1`、`lambda_2`、`lambda_3` | 可信度权重参数 |
| `theta` | 功能区结构模板权重 |
| `w_min`、`w_max` | 可信度截断区间 |
| `parameter_label` | 参数组合标签 |

论文写作建议：

适合用于复现说明或附录。正文中只需要给出最终参数和简要解释即可。

### 3.6 `basic_model_hourly_predictions.csv`

这是最适合做可视化和误差诊断的明细文件，记录每个站点、每个小时、借出/归还两类变量的真实值与三种方法预测值。

文件规模：1440 行，对应 30 个站点 × 24 小时 × 2 类变量。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `target_d` | 目标预测日 |
| `date` | 目标日期 |
| `station_id` | 站点编号 |
| `zone` | 站点所属功能区 |
| `hour` | 小时，0 到 23 |
| `variable` | `borrow` 或 `return` |
| `actual` | 第7天真实记录值 |
| `base1_raw_pred`、`base1_pred` | 基线1连续预测值和最终预测值 |
| `base2_raw_pred`、`base2_pred` | 基线2连续预测值和最终预测值 |
| `model_raw_pred`、`model_pred` | 本文模型连续预测值和最终预测值 |

论文写作建议：

该文件主要用于画图，不建议直接放入论文表格。可用于生成：

1. 代表性站点逐小时拟合图；
2. 真实值与预测值热力图；
3. 逐小时误差热力图；
4. 功能区平均小时曲线对比图。

### 3.7 `basic_model_station_metrics.csv`

该文件记录站点层评价指标。

文件规模：270 行，对应 30 个站点 × 3 种方法 × 3 类变量。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `station_id` | 站点编号 |
| `zone` | 站点功能区 |
| `method` | 预测方法 |
| `variable` | 借出、归还或合并 |
| 各误差指标 | 该站点24小时序列上的评价结果 |

论文写作建议：

该文件适合用于：

1. 统计本文模型在多少个站点上优于基线；
2. 绘制站点级改善幅度图；
3. 找出模型改善最大和退化最大的站点；
4. 支持“模型不是对所有站点都同等有效”的讨论。

### 3.8 `basic_model_zone_metrics.csv`

该文件记录功能区层评价指标。

文件规模：27 行，对应 3 个功能区 × 3 种方法 × 3 类变量。

主要字段与 `basic_model_station_metrics.csv` 类似，但 `station_id` 为 `ALL`，表示该功能区内所有站点整体评价。

论文写作建议：

该文件非常适合支撑“功能区差异确实影响预测表现”的论述。可以在论文中展示功能区层面的 MAE 或 RMSE 对比图，说明模型在哪些功能区更有效，在哪些功能区功能区平均模板更有优势。

### 3.9 `basic_model_win_counts.csv`

该文件统计本文模型在站点层面优于两个基线的站点数量。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `metric` | 比较指标 |
| `comparison` | 指标方向，当前均为越小越好 |
| `model_better_than_base1_count` | 本文模型优于基线1的站点数 |
| `model_better_than_base2_count` | 本文模型优于基线2的站点数 |

论文写作建议：

该文件适合写入结果分析。例如当前结果中，本文模型在站点层 MAE 上优于 `base1` 的站点数为 28 个，在 RMSE 上优于 `base1` 的站点数为 30 个。这比单独给总体指标更有说服力。

### 3.10 `basic_model_station_selection.csv`

该文件记录 6 个代表站点的客观选择规则。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `station_id` | 被选中的站点编号 |
| `zone` | 站点功能区 |
| `selection_reason` | 选择原因 |
| `baseline_day_activity` | 基线日总活动量，等于第6天借出量与归还量之和 |
| `model_minus_base1_mae` | 本文模型 MAE 减去基线1 MAE，小于0表示本文模型优于基线1 |

当前选择规则包括：

| selection_reason | 含义 |
| --- | --- |
| `highest_activity_baseline_day` | 基线日活动量最高站点 |
| `median_activity_baseline_day` | 基线日活动量接近中位数站点 |
| `lowest_nonzero_activity_baseline_day` | 基线日非零活动量最低站点 |
| `largest_model_improvement_vs_base1` | 本文模型相对基线1改善最大站点 |
| `largest_model_deterioration_vs_base1` | 本文模型相对基线1退化最大站点 |
| `closest_to_base1` | 本文模型与基线1表现最接近站点 |

论文写作建议：

使用该文件可以避免“代表站点是主观挑选”的问题。论文中可以说明代表站点按上述规则客观确定。

### 3.11 `basic_model_selected_station_metrics.csv`

该文件记录 6 个代表站点在三种方法下的详细评价指标。

文件规模：18 行，对应 6 个代表站点 × 3 种方法。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `station_id`、`zone` | 代表站点及其功能区 |
| `method` | 预测方法 |
| `variable` | 当前为 `combined` |
| 常规预测指标 | 代表站点层面的预测误差 |
| `selection_reason` | 该站点被选中的原因 |
| `baseline_day_activity` | 基线日总活动量 |
| `model_minus_base1_mae` | 本文模型相对基线1的 MAE 差值 |
| `stock_mae`、`risk_diff` | 代表站点层面的运营风险指标 |

论文写作建议：

适合放入附录或作为代表站点折线图的补充表格。正文中可选取其中 2 到 3 个站点进行解释，例如一个改善明显站点、一个退化站点、一个中等活动量站点。

### 3.12 `basic_model_station_weights.csv`

该文件记录本文模型中每个站点的可信度权重及其组成变量。

文件规模：60 行，对应 30 个站点 × 2 类变量。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `station_id` | 站点编号 |
| `variable` | `borrow` 或 `return` |
| `baseline_total` | 基线日该站点全天总量 |
| `zero_hour_ratio` | 基线日零值小时占比 |
| `peak_concentration` | 基线日峰值集中度 |
| `credibility_weight` | 最终站点可信度权重 |

论文写作建议：

该文件适合解释模型的“站点可信度收缩”机制。可以选取若干站点说明：活动量高、零值少、峰值不过度集中的站点更依赖自身曲线；反之则更多向功能区模板收缩。

### 3.13 `basic_model_risk_metrics.csv`

该文件记录运营风险指标，用于连接第二问和第三问。

文件规模：90 行，对应 30 个站点 × 3 种方法。

主要字段：

| 字段 | 含义 |
| --- | --- |
| `station_id`、`zone` | 站点及其功能区 |
| `method` | 预测方法 |
| `stock_mae` | 预测借还量驱动库存轨迹与真实借还量驱动库存轨迹之间的平均差异 |
| `empty_hours_pred` | 预测数据驱动下出现空桩的小时数 |
| `empty_hours_actual` | 真实数据驱动下出现空桩的小时数 |
| `full_hours_pred` | 预测数据驱动下出现满桩的小时数 |
| `full_hours_actual` | 真实数据驱动下出现满桩的小时数 |
| `empty_hour_diff` | 空桩小时数差异 |
| `full_hour_diff` | 满桩小时数差异 |
| `risk_diff` | 空桩小时差异与满桩小时差异之和 |

论文写作建议：

该文件适合在“预测结果对调度模型的适用性”中使用。需要强调的是，运营风险指标不是为了证明预测值逐点最优，而是为了说明预测结果是否能更稳定地服务第三问库存演化与调度优化。

### 3.14 `basic_model_stock_trajectories.csv`

该文件记录库存轨迹明细。

文件规模：2880 行，对应 30 个站点 × 24 小时 × 4 类轨迹。

其中 `method` 包括：

| method | 含义 |
| --- | --- |
| `actual` | 真实借还量驱动库存轨迹 |
| `base1` | 基线1预测借还量驱动库存轨迹 |
| `base2` | 基线2预测借还量驱动库存轨迹 |
| `model` | 本文模型预测借还量驱动库存轨迹 |

论文写作建议：

该文件主要用于绘制库存轨迹对比图。正文中可以选取少数代表站点展示，说明不同预测输入对第三问库存状态判断的影响。

## 4. 推荐论文写作结构

### 4.1 参数确定

可以写：

> 为避免模型参数完全依赖主观指定，本文在有限候选参数组中进行伪验证。验证目标包括第5天与第6天，综合 MAE、RMSE、全天总量相对误差和小时结构 L1 误差的平均排名，最终选取 $\lambda_1=0.60,\lambda_2=0.20,\lambda_3=0.20,\theta=0.70,w_s\in[0.30,0.80]$。

对应文件：

1. `basic_model_calibration_results.csv`
2. `basic_model_selected_parameters.csv`

### 4.2 总体预测效果

可以写：

> 从全体站点合并指标看，本文模型相较最近同类日直接复制基线，在 MAE、RMSE、sMAPE、$\pm10\%$命中率、总量相对误差和小时结构误差上均有所改善，说明功能区层修正与站点可信度收缩具有实际作用。

同时必须补充：

> 功能区平均模板基线在 MAE、RMSE 和小时结构误差上具有较强竞争力，说明第7天存在明显的功能区平均回归现象。因此本文模型并非在所有指标上绝对最优，其优势主要体现在相较直接复制基线更加稳定，并且保留了站点自身信息与功能区修正之间的平衡。

对应文件：

1. `basic_model_results.csv`
2. `basic_model_results.md`
3. `basic_model_win_counts.csv`

### 4.3 站点层差异

可以写：

> 站点层结果表明，本文模型在多数站点上优于直接复制基线，但不同站点改善幅度存在差异。对于活动量较低或周末曲线偶然性较强的站点，向功能区模板收缩通常更有帮助；对于个别自身周六曲线已经较稳定的站点，直接复制基线可能仍具有优势。

对应文件：

1. `basic_model_station_metrics.csv`
2. `basic_model_station_selection.csv`
3. `basic_model_selected_station_metrics.csv`

### 4.4 功能区层分析

可以写：

> 功能区层结果用于检验第一问中“功能区差异显著”的结论是否能在第二问预测中发挥作用。若某功能区内 `base2` 表现较强，说明该功能区站点具有较明显的共同日内结构；若本文模型表现更优，则说明站点个体信息仍不可忽略。

对应文件：

1. `basic_model_zone_metrics.csv`

### 4.5 面向第三问的评价

可以写：

> 由于问题二的预测结果将作为第三问调度优化的输入，本文进一步使用预测借还量驱动库存演化，并比较预测库存轨迹与真实借还量驱动库存轨迹之间的偏差。该指标更关注预测结果对空桩、满桩等运营风险判断的影响，而不仅仅关注逐小时点预测误差。

对应文件：

1. `basic_model_risk_metrics.csv`
2. `basic_model_stock_trajectories.csv`

## 5. 写作时需要避免的说法

不要写：

> 本文模型全面优于所有基线模型。

原因是 `base2` 在部分指标上优于本文模型。

更建议写：

> 本文模型相较直接复制最近同类日的基线在总体误差、结构误差和多数站点表现上均有改善；同时，功能区平均模板在部分指标上具有较强竞争力，说明目标日借还量具有功能区层面的平均回归特征。本文模型的价值在于在保留站点自身信息的同时引入功能区层收缩，从而获得更稳定、更可解释的预测输入。

不要写：

> 库存风险指标反映了第7天真实库存。

更建议写：

> 库存风险指标是在统一初始库存假设下，对不同预测输入所导致库存演化差异的相对比较，用于评价预测结果对第三问调度优化的适用性。

## 6. 与可视化文件的对应关系

`basic_model` 的可视化结果位于：

```text
task_2/visualizatioon/basic_model/results
```

常用对应关系如下：

| 数据文件 | 常用图 |
| --- | --- |
| `basic_model_results.csv` | 总体指标对比柱状图 |
| `basic_model_hourly_predictions.csv` | 逐小时拟合图、热力图、功能区平均曲线 |
| `basic_model_station_metrics.csv` | 站点 MAE 改善图、站点 MAE 热力图 |
| `basic_model_zone_metrics.csv` | 功能区指标对比图 |
| `basic_model_risk_metrics.csv` | 运营风险指标图 |
| `basic_model_stock_trajectories.csv` | 库存轨迹对比图 |
| `basic_model_selected_station_metrics.csv` | 代表站点指标图 |

## 7. 最推荐放入论文的表和图

若篇幅有限，建议优先使用：

1. `basic_model_results.csv` 中 `variable=combined` 的三行，作为问题二总体预测效果表；
2. `basic_model_win_counts.csv`，作为站点层稳定性补充；
3. `basic_model_zone_metrics.csv`，作为功能区层解释；
4. `basic_model_hourly_predictions.csv` 生成的代表站点逐小时拟合图；
5. `basic_model_risk_metrics.csv` 或 `basic_model_stock_trajectories.csv`，作为第二问连接第三问的证据。

最终结论建议保持克制：本文模型优于直接复制基线，但不应宣称全面优于功能区平均模板；其主要贡献是给出一个兼顾站点个体信息、功能区共性结构和第三问调度需求的稳定预测框架。
