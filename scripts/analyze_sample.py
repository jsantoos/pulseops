from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from oie_core import EquipmentSnapshot, analyze_capacity


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "sample" / "equipment_capacity.csv"


def load_snapshots() -> list[EquipmentSnapshot]:
    with DATASET.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        return [
            EquipmentSnapshot(
                equipment_id=row["equipment_id"],
                equipment_name=row["equipment_name"],
                equipment_type=row["equipment_type"],
                available_minutes=int(row["available_minutes"]),
                booked_minutes=int(row["booked_minutes"]),
                realized_minutes=int(row["realized_minutes"]),
                gross_revenue=float(row["gross_revenue"]),
            )
            for row in rows
        ]


def main() -> None:
    opportunities = analyze_capacity(load_snapshots())
    print(json.dumps([asdict(item) for item in opportunities], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
