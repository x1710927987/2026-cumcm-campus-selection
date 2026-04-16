from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


def find_attachment(base_dir: Path, prefix: str) -> Path:
    matches = sorted(base_dir.glob(f"{prefix}*.csv"))
    if not matches:
        raise FileNotFoundError(f"未找到前缀为 {prefix!r} 的 CSV 文件")
    return matches[0]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def print_station_count(station_rows: list[dict[str, str]]) -> None:
    station_ids = sorted({row["站点编号"] for row in station_rows})
    print("1. 站点数")
    print(f"总站点数: {len(station_ids)}")
    print(f"站点编号列表: {', '.join(station_ids)}")
    print()


def print_station_daily_counts(record_rows: list[dict[str, str]]) -> None:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in record_rows:
        counts[(row["站点编号"], row["日期"])] += 1

    print("2. 每个站点每天记录数")
    print("站点编号\t日期\t记录数")
    for station_id, date in sorted(counts):
        print(f"{station_id}\t{date}\t{counts[(station_id, date)]}")
    print()


def validate_non_negative_integers(record_rows: list[dict[str, str]]) -> None:
    invalid_rows: list[tuple[int, str, str, str]] = []
    for row_index, row in enumerate(record_rows, start=2):
        for field in ("借出量", "归还量"):
            raw_value = row[field]
            try:
                value = int(raw_value)
            except ValueError:
                invalid_rows.append((row_index, row["站点编号"], field, raw_value))
                continue

            if value < 0:
                invalid_rows.append((row_index, row["站点编号"], field, raw_value))

    print("3. 借出量和归还量是否均为非负整数")
    if not invalid_rows:
        print("是，借出量和归还量全部为非负整数。")
    else:
        print("否，发现以下异常值：")
        print("行号\t站点编号\t字段\t值")
        for row_index, station_id, field, raw_value in invalid_rows:
            print(f"{row_index}\t{station_id}\t{field}\t{raw_value}")
    print()


def print_top10(record_rows: list[dict[str, str]], field: str) -> None:
    sorted_rows = sorted(
        record_rows,
        key=lambda row: (
            int(row[field]),
            row["日期"],
            int(row["小时(0-23)"]),
            row["站点编号"],
        ),
        reverse=True,
    )

    print(f"{field} top10")
    print("排名\t值\t日期\t小时\t站点编号")
    for rank, row in enumerate(sorted_rows[:10], start=1):
        print(
            f"{rank}\t{int(row[field])}\t{row['日期']}\t"
            f"{int(row['小时(0-23)'])}\t{row['站点编号']}"
        )
    print()


def print_overall_top10(record_rows: list[dict[str, str]]) -> None:
    print("4. 全体数据（某站点某小时）中借出量和归还量分别的top10")
    print_top10(record_rows, "借出量")
    print_top10(record_rows, "归还量")


def main() -> None:
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]
    attachment_dir = project_root / "data_attachment_for_question_A"

    station_file = find_attachment(attachment_dir, "附件1_")
    record_file = find_attachment(attachment_dir, "附件2_")

    station_rows = read_csv(station_file)
    record_rows = read_csv(record_file)

    print_station_count(station_rows)
    print_station_daily_counts(record_rows)
    validate_non_negative_integers(record_rows)
    print_overall_top10(record_rows)


if __name__ == "__main__":
    main()
