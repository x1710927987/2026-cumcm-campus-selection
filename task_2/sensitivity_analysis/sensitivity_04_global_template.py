"""Sensitivity analysis 04: whether to introduce the global template."""

from __future__ import annotations

from sensitivity_common import Scenario, bm, evaluate_scenarios, load_base_params, write_outputs


ANALYSIS_SLUG = "04_global_template"
TITLE = "是否引入全局模板的灵敏度"


def main() -> None:
    data = bm.load_data()
    base = load_base_params(data)
    lambdas = base.lambdas
    w_min = base.w_min
    w_max = base.w_max

    scenarios = [
        Scenario("base_model", "Use functional-zone template plus a small global template component.", base, use_global_template=True),
        Scenario("no_global_template", "Remove the global template; use only the functional-zone template in shrinkage.", base, use_global_template=False),
        Scenario("global_only_template", "Use only the global template in shrinkage.", bm.Params(lambdas, 0.0, w_min, w_max), use_global_template=True),
        Scenario("half_zone_half_global", "Use equal functional-zone and global template weights.", bm.Params(lambdas, 0.5, w_min, w_max), use_global_template=True),
        Scenario("zone_only_via_theta", "Use theta=1 with the normal formula; equivalent to no global template.", bm.Params(lambdas, 1.0, w_min, w_max), use_global_template=True),
    ]
    outputs = evaluate_scenarios(ANALYSIS_SLUG, scenarios)
    write_outputs(
        ANALYSIS_SLUG,
        TITLE,
        outputs,
        notes=[
            "本分析检验全局小时模板是否能稳定功能区模板。",
            "no_global_template 与 zone_only_via_theta 理论上应较接近，二者同时保留是为了做一致性检查。",
        ],
    )


if __name__ == "__main__":
    main()
