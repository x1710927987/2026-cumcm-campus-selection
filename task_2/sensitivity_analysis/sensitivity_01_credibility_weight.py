"""Sensitivity analysis 01: credibility weight parameters."""

from __future__ import annotations

from sensitivity_common import Scenario, bm, evaluate_scenarios, load_base_params, write_outputs


ANALYSIS_SLUG = "01_credibility_weight"
TITLE = "可信度权重参数灵敏度"


def main() -> None:
    data = bm.load_data()
    base = load_base_params(data)
    theta = base.theta
    w_min = base.w_min
    w_max = base.w_max

    scenarios = [
        Scenario("base_model", "Basic model selected by pseudo-validation.", base),
        Scenario("equal_weights", "Equal weights for total activity, zero-hour ratio and peak concentration.", bm.Params((1 / 3, 1 / 3, 1 / 3), theta, w_min, w_max)),
        Scenario("volume_dominant", "Emphasize baseline-day total activity.", bm.Params((0.8, 0.1, 0.1), theta, w_min, w_max)),
        Scenario("sparsity_dominant", "Emphasize low zero-hour ratio.", bm.Params((0.2, 0.6, 0.2), theta, w_min, w_max)),
        Scenario("smoothness_dominant", "Emphasize low peak concentration.", bm.Params((0.2, 0.2, 0.6), theta, w_min, w_max)),
        Scenario("stability_dominant", "Emphasize both low zero-hour ratio and low peak concentration.", bm.Params((0.2, 0.4, 0.4), theta, w_min, w_max)),
    ]
    outputs = evaluate_scenarios(ANALYSIS_SLUG, scenarios)
    write_outputs(
        ANALYSIS_SLUG,
        TITLE,
        outputs,
        notes=[
            "本分析仅改变 lambda_1、lambda_2、lambda_3，theta 和可信度截断区间保持不变。",
            "MAE/RMSE 越低表示逐点预测越好，ShareL1 越低表示小时结构越接近真实值。",
        ],
    )


if __name__ == "__main__":
    main()
