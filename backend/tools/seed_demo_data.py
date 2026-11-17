"""Reset the demo database to a small curated synthetic dataset.

Every person below is fictional. The script backs up the SQLite file, clears the
four tables, then saves each visit through the same deterministic danger engine
and follow-up planner used by the live app — so alerts and tasks are real
outputs, not hand-written rows.

Usage (from backend/):
    python tools/seed_demo_data.py --force
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.danger import detect  # noqa: E402
from app.extract import VisitRecord  # noqa: E402
from app.followups import build_followups  # noqa: E402


def _record(**fields) -> VisitRecord:
    record = VisitRecord(**fields)
    for name in (
        "beneficiary_id", "patient_name", "visit_type", "weight_kg", "bp",
        "anc_completed", "ifa_provided", "vaccination_status", "next_visit_date",
        "observations",
    ):
        if getattr(record, name) not in (None, "", []):
            record.confidence[name] = 1.0
            record.evidence[name] = "seeded synthetic demo record"
    return record


def demo_records(today: date) -> list[VisitRecord]:
    def day(offset: int) -> str:
        return (today + timedelta(days=offset)).isoformat()

    return [
        _record(
            beneficiary_id="ASHA102",
            patient_name="Lakshmi",
            visit_type="pregnancy_anc",
            weight_kg=55.0,
            bp="118/76",
            anc_completed=True,
            ifa_provided=True,
            next_visit_date=day(4),
            observations="No danger signs. Mild tiredness; appetite normal.",
            language="en-IN",
            transcript=(
                "Lakshmi, beneficiary ID ASHA102. Pregnancy visit. Weight 55 kilo. "
                "BP 118 by 76. ANC completed. IFA tablets given. Next visit in four days."
            ),
        ),
        _record(
            beneficiary_id="ASHA118",
            patient_name="Baby of Meena",
            visit_type="newborn_hbnc",
            weight_kg=2.4,
            next_visit_date=day(2),
            observations=(
                "Newborn has high fever. The baby is not feeding well. "
                "Weight 2.4 kg."
            ),
            language="en-IN",
            transcript=(
                "Baby of Meena, beneficiary ID ASHA118. Newborn home visit. "
                "Weight 2.4 kilo. High fever. The baby is not feeding well."
            ),
        ),
        _record(
            beneficiary_id="ASHA120",
            patient_name="Arjun",
            visit_type="immunization",
            weight_kg=9.2,
            vaccination_status="due",
            vaccines_due=["MR", "Vitamin A"],
            next_visit_date=day(10),
            observations=(
                "No danger signs. Growth normal. Measles-Rubella and "
                "Vitamin A are due."
            ),
            language="en-IN",
            transcript=(
                "Arjun, beneficiary ID ASHA120. Immunization visit. Weight 9.2 kilo. "
                "MR and Vitamin A vaccine due. No danger signs."
            ),
        ),
        _record(
            beneficiary_id="ASHA124",
            patient_name="Sunita",
            visit_type="postnatal",
            weight_kg=52.0,
            ifa_provided=True,
            vaccination_status="given",
            next_visit_date=day(6),
            observations=(
                "Mother recovering well. No danger signs. "
                "Breastfeeding established."
            ),
            language="en-IN",
            transcript=(
                "Sunita, beneficiary ID ASHA124. Postnatal visit. Weight 52 kilo. "
                "Mother recovering well, breastfeeding established. No danger signs. "
                "IFA tablets given."
            ),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="skip confirmation")
    args = parser.parse_args()

    path = get_settings().database_path
    if not path.exists():
        print(f"No database at {path}")
        return 1

    if not args.force:
        answer = input(
            f"This deletes all visits, tasks and alerts in {path}.\n"
            "A backup is written first. Continue? [y/N] "
        )
        if answer.strip().lower() not in {"y", "yes"}:
            print("Cancelled.")
            return 1

    backup = path.with_name(
        f"{path.name}.bak-{date.today().strftime('%Y%m%d')}-{path.stat().st_mtime_ns}"
    )
    shutil.copy2(path, backup)
    print(f"Backup: {backup}")

    db.init_db()
    with sqlite3.connect(path) as connection:
        for table in ("danger_alerts", "followups", "visits", "beneficiaries"):
            connection.execute(f"DELETE FROM {table}")

    tasks = 0
    alerts = 0
    for record in demo_records(date.today()):
        result = detect(
            record.transcript,
            language=record.language,
            visit_type=record.visit_type,
            weight_kg=record.weight_kg,
        )
        plan = build_followups(record, result.hits)
        saved = db.save_visit(record, result.hits, plan)
        tasks += len(plan.tasks)
        alerts += len(result.hits)
        print(
            f"{saved['visit_id']}  {record.patient_name:<16} "
            f"{record.visit_type:<14} tasks={len(plan.tasks)} danger={len(result.hits)}"
        )

    print(f"Seeded {len(demo_records(date.today()))} visits, {tasks} tasks, {alerts} danger alerts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
