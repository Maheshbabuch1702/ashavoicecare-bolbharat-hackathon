"""Automatic follow-up task generation.

Tasks are derived deterministically from the confirmed record and any danger
hits. Each task carries: action, beneficiary, due date, priority, status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .danger import DangerHit
from .extract import VisitRecord


# Human titles for the scheduled next visit. Building them by lowercasing the
# display label mangled acronyms ("Next pregnancy visit (anc)").
NEXT_VISIT_TITLES: dict[str, str] = {
    "pregnancy_anc": "Next ANC checkup",
    "newborn_hbnc": "Next newborn home visit",
    "postnatal": "Next postnatal checkup",
    "immunization": "Next immunization visit",
    "family_planning": "Next family planning visit",
    "general": "Next general visit",
}


@dataclass
class FollowUp:
    title: str
    detail: str
    due_date: str
    priority: str          # urgent | high | normal
    reason: str
    kind: str
    title_key: str = ""

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "title_key": self.title_key,
            "detail": self.detail,
            "due_date": self.due_date,
            "priority": self.priority,
            "reason": self.reason,
            "kind": self.kind,
            "status": "pending",
        }


@dataclass
class FollowUpPlan:
    tasks: list[FollowUp] = field(default_factory=list)

    def as_list(self) -> list[dict]:
        return [task.as_dict() for task in self.tasks]


def _iso(day: date) -> str:
    return day.isoformat()


def _clamp_future(day: date, today: date) -> date:
    return day if day >= today else today


def build_followups(
    record: VisitRecord,
    danger_hits: list[DangerHit],
    *,
    today: date | None = None,
) -> FollowUpPlan:
    today = today or date.today()
    plan = FollowUpPlan()
    visit_title = NEXT_VISIT_TITLES.get(record.visit_type, "Next visit")
    visit_title_key = f"next_visit_{record.visit_type}" if record.visit_type in NEXT_VISIT_TITLES else "next_visit"
    who = record.patient_name or "Beneficiary"

    # 1. Emergency referral always comes first and is due immediately.
    if danger_hits:
        signs = "; ".join(hit.label for hit in danger_hits)
        plan.tasks.append(
            FollowUp(
                title="URGENT: Refer to PHC today",
                detail=f"{who} — danger sign(s): {signs}. Refer to the nearest Primary Health Centre now.",
                due_date=_iso(today),
                priority="urgent",
                reason="Danger sign detected by rule engine",
                kind="referral",
                title_key="referral",
            )
        )

    # 2. Scheduled next visit.
    next_visit = None
    if record.next_visit_date:
        try:
            next_visit = date.fromisoformat(record.next_visit_date)
        except ValueError:
            next_visit = None
    if next_visit:
        plan.tasks.append(
            FollowUp(
                title=visit_title,
                detail=f"{who} · scheduled follow-up visit",
                due_date=_iso(_clamp_future(next_visit, today)),
                priority="normal",
                reason="Next visit date recorded",
                kind="visit",
                title_key=visit_title_key,
            )
        )
    else:
        plan.tasks.append(
            FollowUp(
                title="Schedule next visit",
                detail=f"{who} · no next visit date was recorded",
                due_date=_iso(today + timedelta(days=7)),
                priority="high",
                reason="Next visit date missing",
                kind="visit",
                title_key="schedule_visit",
            )
        )

    # 3. IFA compliance.
    if record.ifa_provided:
        due = _clamp_future(next_visit, today) if next_visit else today + timedelta(days=30)
        plan.tasks.append(
            FollowUp(
                title="IFA follow-up",
                detail=f"{who} · check IFA tablet compliance at next contact",
                due_date=_iso(due),
                priority="normal",
                reason="IFA tablets provided",
                kind="supplement",
                title_key="ifa",
            )
        )

    # 4. Vaccination gap.
    if record.vaccination_status in (None, "not_specified", "due"):
        detail = (
            f"{who} · vaccination details were not recorded"
            if record.vaccination_status in (None, "not_specified")
            else f"{who} · vaccines pending"
        )
        plan.tasks.append(
            FollowUp(
                title="Verify vaccination status",
                detail=detail,
                due_date=_iso(today + timedelta(days=7)),
                priority="high",
                reason="Vaccination status missing or pending",
                kind="immunization",
                title_key="vaccination",
            )
        )

    # 5. ANC gap.
    if record.visit_type == "pregnancy_anc" and record.anc_completed is not True:
        plan.tasks.append(
            FollowUp(
                title="ANC checkup pending",
                detail=f"{who} · ANC checkup was not confirmed as completed",
                due_date=_iso(today + timedelta(days=7)),
                priority="high",
                reason="ANC status not completed",
                kind="anc",
                title_key="anc",
            )
        )

    # 6. Newborn schedule.
    if record.visit_type == "newborn_hbnc":
        plan.tasks.append(
            FollowUp(
                title="Newborn danger-sign check (HBNC)",
                detail=f"{who} · next HBNC home visit and danger-sign screening",
                due_date=_iso(today + timedelta(days=3)),
                priority="high" if not danger_hits else "urgent",
                reason="Newborn home-visit schedule",
                kind="hbnc",
                title_key="hbnc",
            )
        )

    return plan
