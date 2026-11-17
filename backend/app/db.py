"""SQLite storage for the four core tables.

The schema mirrors the Supabase/Postgres design in `supabase_schema.sql`; only
the driver differs, so migrating for the hosted demo is a connection-string
change, not a rewrite.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import get_settings
from .danger import DangerHit
from .extract import VisitRecord
from .followups import FollowUpPlan

SCHEMA = """
CREATE TABLE IF NOT EXISTS beneficiaries (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    village       TEXT,
    household     TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
    id                 TEXT PRIMARY KEY,
    beneficiary_id     TEXT,
    patient_name       TEXT,
    visit_type         TEXT NOT NULL,
    weight_kg          REAL,
    bp                 TEXT,
    anc_completed      INTEGER,
    ifa_provided       INTEGER,
    vaccination_status TEXT,
    vaccines_due       TEXT,
    next_visit_date    TEXT,
    observations       TEXT,
    transcript         TEXT NOT NULL,
    extracted_json     TEXT NOT NULL,
    corrections_json   TEXT NOT NULL DEFAULT '[]',
    danger_json        TEXT NOT NULL DEFAULT '[]',
    status             TEXT NOT NULL DEFAULT 'draft',
    language           TEXT NOT NULL,
    extraction_method  TEXT,
    created_at         TEXT NOT NULL,
    confirmed_at       TEXT
);

CREATE TABLE IF NOT EXISTS danger_alerts (
    id             TEXT PRIMARY KEY,
    visit_id       TEXT NOT NULL,
    beneficiary_id TEXT,
    code           TEXT NOT NULL,
    label          TEXT NOT NULL,
    category       TEXT NOT NULL,
    urgency        TEXT NOT NULL,
    matched_text   TEXT,
    source         TEXT,
    referral_status TEXT NOT NULL DEFAULT 'pending',
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS followups (
    id             TEXT PRIMARY KEY,
    visit_id       TEXT NOT NULL,
    beneficiary_id TEXT,
    patient_name   TEXT,
    title          TEXT NOT NULL,
    title_key      TEXT,
    detail         TEXT,
    due_date       TEXT,
    priority       TEXT NOT NULL,
    reason         TEXT,
    kind           TEXT,
    status         TEXT NOT NULL DEFAULT 'pending',
    created_at     TEXT NOT NULL,
    completed_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_visits_created ON visits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_followups_status ON followups(status, due_date);
CREATE INDEX IF NOT EXISTS idx_alerts_visit ON danger_alerts(visit_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _db_path() -> Path:
    return get_settings().database_path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(_db_path())
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    """Small additive migration for existing SQLite demo databases."""
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)
        _ensure_column(connection, "followups", "title_key", "TEXT")
        _ensure_column(connection, "followups", "patient_name", "TEXT")

        # Backfill fields for databases created by older builds.
        connection.execute(
            """
            UPDATE followups
            SET patient_name = (
                SELECT v.patient_name FROM visits v WHERE v.id = followups.visit_id
            )
            WHERE (patient_name IS NULL OR patient_name = '')
              AND EXISTS (
                SELECT 1 FROM visits v
                WHERE v.id = followups.visit_id AND v.patient_name IS NOT NULL
              )
            """
        )
        connection.execute(
            """
            UPDATE followups
            SET title_key = CASE
                WHEN title LIKE 'Next ANC%' THEN 'next_visit_pregnancy_anc'
                WHEN title LIKE 'Next newborn%' THEN 'next_visit_newborn_hbnc'
                WHEN title LIKE 'Next postnatal%' THEN 'next_visit_postnatal'
                WHEN title LIKE 'Next immunization%' THEN 'next_visit_immunization'
                WHEN title LIKE 'Next family%' THEN 'next_visit_family_planning'
                WHEN title LIKE 'Next general%' THEN 'next_visit_general'
                ELSE title_key
            END
            WHERE title_key = 'next_visit'
            """
        )
        connection.execute(
            """
            UPDATE followups
            SET title_key = CASE
                WHEN kind = 'referral' THEN 'referral'
                WHEN kind = 'supplement' THEN 'ifa'
                WHEN kind = 'immunization' THEN 'vaccination'
                WHEN kind = 'hbnc' THEN 'hbnc'
                WHEN kind = 'anc' THEN 'anc'
                WHEN kind = 'visit' AND title LIKE 'Next ANC%' THEN 'next_visit_pregnancy_anc'
                WHEN kind = 'visit' AND title LIKE 'Next newborn%' THEN 'next_visit_newborn_hbnc'
                WHEN kind = 'visit' AND title LIKE 'Next postnatal%' THEN 'next_visit_postnatal'
                WHEN kind = 'visit' AND title LIKE 'Next immunization%' THEN 'next_visit_immunization'
                WHEN kind = 'visit' AND title LIKE 'Next family%' THEN 'next_visit_family_planning'
                WHEN kind = 'visit' AND title LIKE 'Next general%' THEN 'next_visit_general'
                WHEN kind = 'visit' AND title LIKE 'Schedule next%' THEN 'schedule_visit'
                WHEN kind = 'visit' THEN 'next_visit'
                ELSE title_key
            END
            WHERE title_key IS NULL OR title_key = ''
            """
        )


def _upsert_beneficiary(connection: sqlite3.Connection, record: VisitRecord) -> None:
    if not record.beneficiary_id:
        return
    now = _now()
    connection.execute(
        """
        INSERT INTO beneficiaries (id, name, village, household, created_at, updated_at)
        VALUES (?, ?, NULL, NULL, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = COALESCE(excluded.name, beneficiaries.name),
            updated_at = excluded.updated_at
        """,
        (record.beneficiary_id, record.patient_name or "", now, now),
    )


def save_visit(
    record: VisitRecord,
    danger_hits: list[DangerHit],
    followups: FollowUpPlan,
    *,
    corrections: list[dict] | None = None,
    status: str = "confirmed",
) -> dict[str, Any]:
    visit_id = f"VIS-{uuid.uuid4().hex[:10].upper()}"
    now = _now()
    corrections = corrections or []

    with connect() as connection:
        _upsert_beneficiary(connection, record)
        connection.execute(
            """
            INSERT INTO visits (
                id, beneficiary_id, patient_name, visit_type, weight_kg, bp,
                anc_completed, ifa_provided, vaccination_status, vaccines_due,
                next_visit_date, observations, transcript, extracted_json,
                corrections_json, danger_json, status, language, extraction_method,
                created_at, confirmed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                visit_id,
                record.beneficiary_id,
                record.patient_name,
                record.visit_type,
                record.weight_kg,
                record.bp,
                None if record.anc_completed is None else int(record.anc_completed),
                None if record.ifa_provided is None else int(record.ifa_provided),
                record.vaccination_status,
                json.dumps(record.vaccines_due, ensure_ascii=False),
                record.next_visit_date,
                record.observations,
                record.transcript,
                json.dumps(record.as_dict(), ensure_ascii=False),
                json.dumps(corrections, ensure_ascii=False),
                json.dumps([hit.as_dict() for hit in danger_hits], ensure_ascii=False),
                status,
                record.language,
                record.extraction_method,
                now,
                now if status == "confirmed" else None,
            ),
        )

        for hit in danger_hits:
            connection.execute(
                """
                INSERT INTO danger_alerts (
                    id, visit_id, beneficiary_id, code, label, category, urgency,
                    matched_text, source, referral_status, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    f"ALT-{uuid.uuid4().hex[:10].upper()}",
                    visit_id,
                    record.beneficiary_id,
                    hit.code,
                    hit.label,
                    hit.category,
                    hit.urgency,
                    hit.matched_text,
                    hit.source,
                    "pending",
                    now,
                ),
            )

        task_rows = followups.as_list()
        for task in task_rows:
            task["id"] = f"FUP-{uuid.uuid4().hex[:10].upper()}"
            connection.execute(
                """
                INSERT INTO followups (
                    id, visit_id, beneficiary_id, patient_name, title, title_key,
                    detail, due_date, priority, reason, kind, status, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    task["id"],
                    visit_id,
                    record.beneficiary_id,
                    record.patient_name,
                    task["title"],
                    task.get("title_key", ""),
                    task["detail"],
                    task["due_date"],
                    task["priority"],
                    task["reason"],
                    task["kind"],
                    "pending",
                    now,
                ),
            )

    return {
        "visit_id": visit_id,
        "beneficiary_id": record.beneficiary_id,
        "followups": task_rows,
        "danger": [hit.as_dict() for hit in danger_hits],
        "saved_at": now,
    }


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("vaccines_due", "danger_json", "corrections_json"):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                data[key] = []
    for key in ("extracted_json",):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                data[key] = {}
    return data


def list_visits(
    limit: int = 50,
    *,
    search: str = "",
    date_from: str = "",
    date_to: str = "",
    visit_type: str = "",
    beneficiary_id: str = "",
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if search.strip():
        needle = f"%{search.strip()}%"
        clauses.append(
            "(COALESCE(patient_name, '') LIKE ? OR COALESCE(beneficiary_id, '') LIKE ?"
            " OR COALESCE(transcript, '') LIKE ? OR COALESCE(observations, '') LIKE ?)"
        )
        params.extend([needle, needle, needle, needle])
    if date_from:
        clauses.append("substr(created_at, 1, 10) >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("substr(created_at, 1, 10) <= ?")
        params.append(date_to)
    if visit_type:
        clauses.append("visit_type = ?")
        params.append(visit_type)
    if beneficiary_id:
        clauses.append("beneficiary_id = ?")
        params.append(beneficiary_id)

    query = "SELECT * FROM visits"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(max(1, limit))

    with connect() as connection:
        rows = connection.execute(query, params).fetchall()

    visits: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        visit = _row_to_dict(row)
        # Test runs and retries can create near-identical records seconds apart.
        # Collapse repeat visits for the same person and visit type on the same
        # day in the history view; the underlying rows stay intact for audit.
        signature = (
            visit.get("beneficiary_id") or (visit.get("patient_name") or "").strip().lower() or None,
            visit.get("visit_type"),
            (visit.get("created_at") or "")[:10],
        )
        if signature in seen:
            continue
        seen.add(signature)
        visits.append(visit)
    return visits


def get_visit(visit_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        if not row:
            return None
        visit = _row_to_dict(row)
        visit["followups"] = [
            dict(item)
            for item in connection.execute(
                """
                SELECT * FROM followups WHERE visit_id = ?
                ORDER BY CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 ELSE 2 END,
                         due_date
                """,
                (visit_id,),
            ).fetchall()
        ]
        visit["alerts"] = [
            dict(item)
            for item in connection.execute(
                "SELECT * FROM danger_alerts WHERE visit_id = ?", (visit_id,)
            ).fetchall()
        ]
    return visit


def _legacy_title_key(row: dict[str, Any]) -> str:
    key = row.get("title_key")
    if key:
        return str(key)
    title = str(row.get("title") or "")
    kind = str(row.get("kind") or "")
    if kind == "referral":
        return "referral"
    if kind == "supplement":
        return "ifa"
    if kind == "immunization":
        return "vaccination"
    if kind == "hbnc":
        return "hbnc"
    if kind == "anc":
        return "anc"
    if kind == "visit":
        if title.startswith("Next ANC"):
            return "next_visit_pregnancy_anc"
        if title.startswith("Next newborn"):
            return "next_visit_newborn_hbnc"
        if title.startswith("Next postnatal"):
            return "next_visit_postnatal"
        if title.startswith("Next immunization"):
            return "next_visit_immunization"
        if title.startswith("Next family"):
            return "next_visit_family_planning"
        if title.startswith("Next general"):
            return "next_visit_general"
        if title.startswith("Schedule"):
            return "schedule_visit"
        return "next_visit"
    return ""


def list_followups(status: str | None = "pending", limit: int = 100) -> list[dict[str, Any]]:
    query = "SELECT * FROM followups"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at"
    with connect() as connection:
        rows = [dict(row) for row in connection.execute(query, params).fetchall()]

    # Collapse duplicate tasks generated by repeated test saves of the same
    # visit. A legitimate task with a different due date or beneficiary is kept.
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        row["title_key"] = _legacy_title_key(row)
        identity = row.get("beneficiary_id") or row.get("patient_name") or row.get("detail") or ""
        # "next_visit" and "next_visit_pregnancy_anc" describe the same task.
        task_group = "next_visit" if str(row.get("title_key", "")).startswith("next_visit") else row.get("title_key")
        key = (
            task_group,
            row.get("kind"),
            row.get("due_date"),
            identity,
            row.get("status"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    priority_order = {"urgent": 0, "high": 1, "normal": 2}
    deduped.sort(
        key=lambda task: (
            priority_order.get(str(task.get("priority")), 3),
            str(task.get("due_date") or "9999-12-31"),
            str(task.get("created_at") or ""),
        )
    )
    return deduped[: max(1, limit)]


def complete_followup(followup_id: str) -> bool:
    with connect() as connection:
        row = connection.execute(
            "SELECT visit_id, kind FROM followups WHERE id = ?", (followup_id,)
        ).fetchone()
        if not row:
            return False
        cursor = connection.execute(
            "UPDATE followups SET status = 'done', completed_at = ? WHERE id = ? AND status != 'done'",
            (_now(), followup_id),
        )
        if cursor.rowcount > 0 and row["kind"] == "referral":
            # Closing the urgent referral task also closes the alert, so the
            # dashboard stops counting it as pending.
            connection.execute(
                """
                UPDATE danger_alerts
                SET referral_status = 'referred'
                WHERE visit_id = ? AND referral_status = 'pending'
                """,
                (row["visit_id"],),
            )
    return cursor.rowcount > 0


def reopen_followup(followup_id: str) -> bool:
    with connect() as connection:
        row = connection.execute(
            "SELECT visit_id, kind FROM followups WHERE id = ?", (followup_id,)
        ).fetchone()
        if not row:
            return False
        cursor = connection.execute(
            "UPDATE followups SET status = 'pending', completed_at = NULL WHERE id = ? AND status = 'done'",
            (followup_id,),
        )
        if cursor.rowcount > 0 and row["kind"] == "referral":
            connection.execute(
                """
                UPDATE danger_alerts
                SET referral_status = 'pending'
                WHERE visit_id = ? AND referral_status = 'referred'
                """,
                (row["visit_id"],),
            )
    return cursor.rowcount > 0


def list_beneficiaries(search: str = "", limit: int = 30) -> list[dict[str, Any]]:
    query = """
        SELECT COALESCE(beneficiary_id, 'NAME:' || lower(patient_name)) AS id,
               MAX(patient_name) AS name,
               COUNT(*) AS visits,
               MAX(created_at) AS last_seen
        FROM visits
        WHERE (patient_name IS NOT NULL OR beneficiary_id IS NOT NULL)
    """
    params: list[Any] = []
    if search.strip():
        needle = f"%{search.strip()}%"
        query += " AND (COALESCE(patient_name, '') LIKE ? OR COALESCE(beneficiary_id, '') LIKE ?)"
        params.extend([needle, needle])
    query += " GROUP BY COALESCE(beneficiary_id, 'NAME:' || lower(patient_name))"
    query += " ORDER BY last_seen DESC LIMIT ?"
    params.append(max(1, limit))
    with connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def update_visit(
    visit_id: str,
    updates: dict[str, Any],
    *,
    corrections: list[dict] | None = None,
) -> dict[str, Any] | None:
    """Apply a manual correction to an already-saved visit.

    Danger alerts and follow-ups are intentionally left as they were recorded at
    visit time: silently deleting an emergency flag because a field was edited is
    less safe than keeping the original alert for review.
    """
    allowed = {
        "beneficiary_id", "patient_name", "visit_type", "weight_kg", "bp",
        "anc_completed", "ifa_provided", "vaccination_status", "vaccines_due",
        "next_visit_date", "observations",
    }
    cleaned: dict[str, Any] = {}
    for key, value in updates.items():
        if key not in allowed:
            continue
        if key in {"anc_completed", "ifa_provided"}:
            value = None if value is None else bool(value)
        elif key == "weight_kg":
            value = None if value in (None, "") else float(value)
        elif key == "vaccines_due":
            value = [str(item) for item in (value or [])]
        elif isinstance(value, str):
            value = value.strip() or None
        cleaned[key] = value

    if not cleaned:
        return get_visit(visit_id)

    with connect() as connection:
        row = connection.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        if not row:
            return None

        stored: dict[str, Any] = {}
        try:
            stored = json.loads(row["extracted_json"] or "{}")
        except json.JSONDecodeError:
            stored = {}
        stored.update(cleaned)

        fields = VisitRecord.__dataclass_fields__
        record = VisitRecord(
            **{key: stored.get(key) for key in fields if key in stored}
        )
        record.transcript = row["transcript"]
        record.language = row["language"]
        record.extraction_method = row["extraction_method"] or "manual"

        previous: list[dict] = []
        try:
            previous = json.loads(row["corrections_json"] or "[]")
        except json.JSONDecodeError:
            previous = []
        previous.extend(corrections or [])

        connection.execute(
            """
            UPDATE visits SET
                beneficiary_id = ?, patient_name = ?, visit_type = ?, weight_kg = ?,
                bp = ?, anc_completed = ?, ifa_provided = ?, vaccination_status = ?,
                vaccines_due = ?, next_visit_date = ?, observations = ?,
                extracted_json = ?, corrections_json = ?
            WHERE id = ?
            """,
            (
                record.beneficiary_id,
                record.patient_name,
                record.visit_type,
                record.weight_kg,
                record.bp,
                None if record.anc_completed is None else int(record.anc_completed),
                None if record.ifa_provided is None else int(record.ifa_provided),
                record.vaccination_status,
                json.dumps(record.vaccines_due, ensure_ascii=False),
                record.next_visit_date,
                record.observations,
                json.dumps(record.as_dict(), ensure_ascii=False),
                json.dumps(previous, ensure_ascii=False),
                visit_id,
            ),
        )
        _upsert_beneficiary(connection, record)

    return get_visit(visit_id)


def stats() -> dict[str, Any]:
    today = date.today().isoformat()
    with connect() as connection:
        todays = connection.execute(
            "SELECT COUNT(*) AS n FROM visits WHERE substr(created_at, 1, 10) = ?", (today,)
        ).fetchone()["n"]
        urgent = connection.execute(
            "SELECT COUNT(DISTINCT visit_id) AS n FROM danger_alerts WHERE referral_status = 'pending'"
        ).fetchone()["n"]
        total = connection.execute("SELECT COUNT(*) AS n FROM visits").fetchone()["n"]
    pending = len(list_followups(status="pending", limit=10_000))
    return {
        "today_visits": todays,
        "pending_followups": pending,
        "urgent_alerts": urgent,
        "total_visits": total,
    }
