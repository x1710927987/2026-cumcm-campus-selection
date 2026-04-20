"""Sensitivity analysis 03: functional-zone shrinkage strength."""

from __future__ import annotations

from sensitivity_common import Scenario, bm, evaluate_scenarios, load_base_params, write_outputs


ANALYSIS_SLUG = "03_zone_shrinkage"
TITLE = "功能分区收缩强度灵敏度"


def main() -> None:
    data = bm.load_data()
    base = load_base_params(data)
    lambdas = base.lambdas
    w_min = base.w_min
    w_max = base.w_max

    scenarios = [
        Scenario("theta_0_0_global_only", "Use only the global template inside the shrinkage part.", bm.Params(lambdas, 0.0, w_min, w_max)),
        Scenario("theta_0_5_balanced", "Use equal functional-zone and global template weights.", bm.Params(lambdas, 0.5, w_min, w_max)),
        Scenario("theta_0_6", "Moderate functional-zone dominance.", bm.Params(lambdas, 0.6, w_min, w_max)),
        Scenario("base_model", "Basic model selected by pseudo-validation.", base),
        Scenario("theta_0_8", "Stronger functional-zone dominance.", bm.Params(lambdas, 0.8, w_min, w_max)),
        Scenario("theta_1_0_zone_only", "Use only the functional-zone template inside the shrinkage part.", bm.Params(lambdas, 1.0, w_min, w_max)),
    ]
    outputs = evaluate_scenarios(ANALYSIS_SLUG, scenarios)
    write_outputs(
        ANALYSIS_SLUG,
        TITLE,
        outputs,
        notes=[
            "本分析仅改变功能区模板与全局模板混合时的 theta_s。",
            "theta=1 表示站点信息被收缩时完全依赖功能区模板，theta=0 表示完全依赖全局模板。",
        ],
    )


if __name__ == "__main__":
    main()
