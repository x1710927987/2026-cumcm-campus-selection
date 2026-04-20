"""Sensitivity analysis 06: functional-zone partition scheme."""

from __future__ import annotations

from sensitivity_common import (
    Scenario,
    activity_tertile_zones,
    bm,
    capacity_tertile_zones,
    clone_data_with_zone,
    evaluate_scenarios,
    global_single_zone,
    load_base_params,
    write_outputs,
)


ANALYSIS_SLUG = "06_zone_partition"
TITLE = "功能分区划分灵敏度"


def main() -> None:
    data = bm.load_data()
    base = load_base_params(data)

    global_data = clone_data_with_zone(data, global_single_zone(data))
    activity_data = clone_data_with_zone(data, activity_tertile_zones(data, bm.TARGET_D))
    capacity_data = clone_data_with_zone(data, capacity_tertile_zones(data))

    scenarios = [
        Scenario("base_model", "Original manually annotated functional zones.", base, data=data),
        Scenario("single_global_zone", "Merge all stations into one zone.", base, data=global_data),
        Scenario("activity_tertile_zone", "Data-driven zones by baseline-day total activity tertiles.", base, data=activity_data),
        Scenario("capacity_tertile_zone", "Infrastructure-driven zones by dock-capacity tertiles.", base, data=capacity_data),
    ]
    outputs = evaluate_scenarios(ANALYSIS_SLUG, scenarios)
    write_outputs(
        ANALYSIS_SLUG,
        TITLE,
        outputs,
        notes=[
            "本分析仅改变收缩模板中使用的站点到功能区映射关系。",
            "single_global_zone 用于检验功能区层是否确实有必要存在。",
            "activity_tertile_zone 和 capacity_tertile_zone 分别作为活动量驱动和桩位容量驱动的替代分区方案。",
        ],
    )


if __name__ == "__main__":
    main()
