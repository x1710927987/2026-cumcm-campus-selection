"""Sensitivity analysis 02: credibility weight clipping interval."""

from __future__ import annotations

from sensitivity_common import Scenario, bm, evaluate_scenarios, load_base_params, write_outputs


ANALYSIS_SLUG = "02_weight_clip"
TITLE = "可信度截断区间灵敏度"


def main() -> None:
    data = bm.load_data()
    base = load_base_params(data)
    lambdas = base.lambdas
    theta = base.theta

    scenarios = [
        Scenario("base_model", "Basic model selected by pseudo-validation.", base),
        Scenario("wide_clip_0_2_0_9", "Allow stronger station self-dependence and stronger shrinkage.", bm.Params(lambdas, theta, 0.2, 0.9)),
        Scenario("upper_0_9", "Keep lower bound but allow higher station credibility.", bm.Params(lambdas, theta, 0.3, 0.9)),
        Scenario("narrow_clip_0_3_0_7", "Stronger shrinkage by lowering the upper credibility bound.", bm.Params(lambdas, theta, 0.3, 0.7)),
        Scenario("conservative_0_4_0_8", "Avoid very low station credibility.", bm.Params(lambdas, theta, 0.4, 0.8)),
        Scenario("high_trust_0_5_0_9", "Force stronger reliance on station baseline-day samples.", bm.Params(lambdas, theta, 0.5, 0.9)),
    ]
    outputs = evaluate_scenarios(ANALYSIS_SLUG, scenarios)
    write_outputs(
        ANALYSIS_SLUG,
        TITLE,
        outputs,
        notes=[
            "本分析仅改变 w_s 的可信度截断区间，其他参数保持不变。",
            "较高的下界意味着模型更频繁地信任站点自身基线日曲线，较低的上界意味着模型更强地向功能区模板收缩。",
        ],
    )


if __name__ == "__main__":
    main()
