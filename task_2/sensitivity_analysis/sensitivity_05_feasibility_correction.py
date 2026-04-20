"""Sensitivity analysis 05: feasibility correction of final predictions."""

from __future__ import annotations

from sensitivity_common import Scenario, bm, evaluate_scenarios, load_base_params, write_outputs


ANALYSIS_SLUG = "05_feasibility_correction"
TITLE = "极端值修正灵敏度"


def main() -> None:
    data = bm.load_data()
    base = load_base_params(data)

    scenarios = [
        Scenario("raw_continuous", "Use raw continuous predictions without nonnegative, integer or cap correction.", base, finalization_mode="raw_continuous"),
        Scenario("nonnegative_continuous", "Only force nonnegativity; keep continuous values.", base, finalization_mode="nonnegative_continuous"),
        Scenario("round_only", "Force nonnegative integer predictions, but do not apply historical upper bounds.", base, finalization_mode="round_only"),
        Scenario("base_model", "Basic model: nonnegative integer predictions plus historical mild upper cap.", base, finalization_mode="cap"),
    ]
    outputs = evaluate_scenarios(ANALYSIS_SLUG, scenarios)
    write_outputs(
        ANALYSIS_SLUG,
        TITLE,
        outputs,
        notes=[
            "本分析仅改变最终预测值的后处理规则。",
            "连续型预测值有助于误差分析，但最终用于调度输入的需求矩阵应为非负整数。",
        ],
    )


if __name__ == "__main__":
    main()
