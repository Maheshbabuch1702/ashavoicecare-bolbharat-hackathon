"""Clean duplicate demo/test records out of the SQLite database.

The hackathon build uses synthetic data only. Repeated end-to-end runs can leave
byte-identical visits and follow-up tasks behind; those are collapsed here so the
demo dashboard reflects distinct visits.

Usage (from backend/):
    python tools/clean_demo_data.py
"""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "asha.db"


def _delete_visit(connection: sqlite3.Connection, visit_id: str) -> None:
    connection.execute("DELETE FROM danger_alerts WHERE visit_id = ?", (visit_id,))
    connection.execute("DELETE FROM followups WHERE visit_id = ?", (visit_id,))
    connection.execute("DELETE FROM visits WHERE id = ?", (visit_id,))


def main() -> int:
    if not DB_PATH.exists():
        print(f"No database at {DB_PATH}")
        return 1

    backup = DB_PATH.with_name(
        f"{DB_PATH.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    removed_visits = 0
    removed_tasks = 0
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(followups)")}
        if "title_key" not in columns:
            connection.execute("ALTER TABLE followups ADD COLUMN title_key TEXT")
        if "patient_name" not in columns:
            connection.execute("ALTER TABLE followups ADD COLUMN patient_name TEXT")

        rows = connection.execute("SELECT * FROM visits ORDER BY created_at").fetchall()
        seen: dict[tuple, str] = {}
        for row in rows:
            signature = (
                row["beneficiary_id"]
                or (row["patient_name"] or "").strip().lower()
                or None,
                row["visit_type"],
                (row["created_at"] or "")[:10],
            )
            incomplete_general = (
                row["visit_type"] == "general"
                and not row["patient_name"]
                and not row["beneficiary_id"]
            )
            if incomplete_general or signature in seen:
                _delete_visit(connection, row["id"])
                removed_visits += 1
            else:
                seen[signature] = row["id"]

        tasks = connection.execute(
            "SELECT * FROM followups WHERE status = 'pending' ORDER BY created_at"
        ).fetchall()
        seen_tasks: set[tuple] = set()
        for task in tasks:
            identity = (
                task["beneficiary_id"]
                or task["patient_name"]
                or task["detail"]
                or ""
            )
            key = (task["title_key"], task["kind"], task["due_date"], identity)
            if key in seen_tasks:
                connection.execute("DELETE FROM followups WHERE id = ?", (task["id"],))
                removed_tasks += 1
            else:
                seen_tasks.add(key)

        connection.execute(
            "DELETE FROM followups WHERE visit_id NOT IN (SELECT id FROM visits)"
        )
        connection.execute(
            "DELETE FROM danger_alerts WHERE visit_id NOT IN (SELECT id FROM visits)"
        )
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()

    print(f"Removed {removed_visits} duplicate/incomplete visits and {removed_tasks} duplicate tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
