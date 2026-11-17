"""FastAPI application: voice WebSocket, TTS proxy and record APIs."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db
from .config import PROJECT_DIR, get_settings
from .danger import detect
from .dialog import build_readback
from .extract import VisitRecord
from .followups import build_followups
from .gnani import synthesize
from .i18n import SUPPORTED_LANGUAGES, normalise_language, t
from .session import VisitSession

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="ASHA VoiceCare", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    language: str = "en-IN"


class ManualVisitCreate(BaseModel):
    beneficiary_id: str | None = None
    patient_name: str | None = None
    visit_type: str = "general"
    weight_kg: float | None = Field(default=None, ge=0.1, le=300)
    bp: str | None = None
    anc_completed: bool | None = None
    ifa_provided: bool | None = None
    vaccination_status: str | None = None
    vaccines_due: list[str] = Field(default_factory=list)
    next_visit_date: str | None = None
    observations: str | None = None
    language: str = "en-IN"


class ManualVisitPatch(BaseModel):
    beneficiary_id: str | None = None
    patient_name: str | None = None
    visit_type: str | None = None
    weight_kg: float | None = Field(default=None, ge=0.1, le=300)
    bp: str | None = None
    anc_completed: bool | None = None
    ifa_provided: bool | None = None
    vaccination_status: str | None = None
    vaccines_due: list[str] | None = None
    next_visit_date: str | None = None
    observations: str | None = None


VALID_VISIT_TYPES = {
    "pregnancy_anc", "newborn_hbnc", "postnatal", "immunization",
    "family_planning", "general",
}


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _validated_date(raw: str | None) -> str | None:
    raw = _clean_optional(raw)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Next visit date must be YYYY-MM-DD") from error


def _validated_visit_type(raw: str | None, fallback: str = "general") -> str:
    if raw not in VALID_VISIT_TYPES:
        return fallback
    return raw


def _manual_record(payload: ManualVisitCreate) -> VisitRecord:
    language = normalise_language(payload.language)
    patient_name = _clean_optional(payload.patient_name)
    beneficiary_id = _clean_optional(payload.beneficiary_id)
    if not patient_name and not beneficiary_id:
        raise HTTPException(
            status_code=422,
            detail="Enter a patient name or beneficiary ID before saving.",
        )

    visit_type = _validated_visit_type(payload.visit_type)
    vaccination = _clean_optional(payload.vaccination_status)
    if vaccination not in {None, "given", "due", "not_specified"}:
        vaccination = None

    observations = _clean_optional(payload.observations)
    record = VisitRecord(
        beneficiary_id=beneficiary_id.upper() if beneficiary_id else None,
        patient_name=patient_name,
        visit_type=visit_type,
        weight_kg=payload.weight_kg,
        bp=_clean_optional(payload.bp),
        anc_completed=payload.anc_completed,
        ifa_provided=payload.ifa_provided,
        vaccination_status=vaccination,
        vaccines_due=[item.strip() for item in payload.vaccines_due if item.strip()],
        next_visit_date=_validated_date(payload.next_visit_date),
        observations=observations,
        language=language,
        transcript=observations or "Manual entry by ASHA worker.",
        extraction_method="manual",
    )
    for field in (
        "beneficiary_id", "patient_name", "visit_type", "weight_kg", "bp",
        "anc_completed", "ifa_provided", "vaccination_status", "next_visit_date",
        "observations",
    ):
        if getattr(record, field) not in (None, "", []):
            record.confidence[field] = 1.0
            record.evidence[field] = "typed by ASHA worker"
    return record



@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "gnani_configured": settings.gnani_ready,
        "llm_configured": settings.llm_ready,
        "stt_model": settings.gnani_stt_model,
        "tts_model": settings.gnani_tts_model,
        "database": str(settings.database_path),
    }


@app.get("/api/config")
async def config() -> dict[str, Any]:
    return {
        "languages": [{"code": code, "label": label} for code, label in SUPPORTED_LANGUAGES.items()],
        "default_language": "en-IN",
        "gnani_configured": settings.gnani_ready,
        "llm_configured": settings.llm_ready,
    }


@app.post("/api/tts")
async def tts(request: TTSRequest) -> Response:
    if not settings.gnani_ready:
        raise HTTPException(status_code=503, detail="Gnani API key is not configured")
    language = normalise_language(request.language)
    try:
        audio = await synthesize(request.text, language, settings)
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Text-to-speech failed: {error}") from error
    return Response(content=audio, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@app.get("/api/visits")
async def visits(
    limit: int = 100,
    search: str = "",
    date_from: str = "",
    date_to: str = "",
    visit_type: str = "",
    beneficiary_id: str = "",
) -> dict[str, Any]:
    return {
        "visits": db.list_visits(
            limit=max(1, min(limit, 500)),
            search=search,
            date_from=date_from,
            date_to=date_to,
            visit_type=visit_type,
            beneficiary_id=beneficiary_id,
        )
    }


@app.post("/api/visits/manual")
async def create_manual_visit(payload: ManualVisitCreate) -> dict[str, Any]:
    record = _manual_record(payload)
    result = detect(
        record.observations or "",
        language=record.language,
        visit_type=record.visit_type,
        weight_kg=record.weight_kg,
    )
    plan = build_followups(record, result.hits)
    saved = db.save_visit(record, result.hits, plan, status="confirmed")
    return {
        **saved,
        "record": record.as_dict(),
        "transcript": record.transcript,
        "missing": record.missing(),
        "readback": build_readback(record, record.language, missing=record.missing()),
        "source": "manual",
    }


@app.patch("/api/visits/{visit_id}")
async def edit_visit(visit_id: str, payload: ManualVisitPatch) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    if "visit_type" in updates:
        updates["visit_type"] = _validated_visit_type(updates["visit_type"])
    if "next_visit_date" in updates:
        updates["next_visit_date"] = _validated_date(updates["next_visit_date"])
    if "vaccination_status" in updates:
        status = _clean_optional(updates["vaccination_status"])
        updates["vaccination_status"] = status if status in {None, "given", "due", "not_specified"} else None
    if "beneficiary_id" in updates:
        beneficiary_id = _clean_optional(updates["beneficiary_id"])
        updates["beneficiary_id"] = beneficiary_id.upper() if beneficiary_id else None
    if "patient_name" in updates:
        updates["patient_name"] = _clean_optional(updates["patient_name"])

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    corrections = [
        {"field": field, "value": value, "utterance": "manual edit", "at": now}
        for field, value in updates.items()
    ]
    updated = db.update_visit(visit_id, updates, corrections=corrections)
    if not updated:
        raise HTTPException(status_code=404, detail="Visit not found")
    return {"ok": True, "visit": updated}


@app.get("/api/visits/{visit_id}")
async def visit(visit_id: str) -> dict[str, Any]:
    record = db.get_visit(visit_id)
    if not record:
        raise HTTPException(status_code=404, detail="Visit not found")
    return record


@app.get("/api/beneficiaries")
async def beneficiaries(search: str = "", limit: int = 30) -> dict[str, Any]:
    return {"beneficiaries": db.list_beneficiaries(search=search, limit=max(1, min(limit, 100)))}


@app.get("/api/followups")
async def followups(status: str | None = "pending") -> dict[str, Any]:
    return {"followups": db.list_followups(status=status)}


@app.post("/api/followups/{followup_id}/complete")
async def complete(followup_id: str) -> dict[str, Any]:
    if not db.complete_followup(followup_id):
        raise HTTPException(status_code=404, detail="Follow-up not found or already done")
    return {"ok": True, "id": followup_id}


@app.post("/api/followups/{followup_id}/reopen")
async def reopen(followup_id: str) -> dict[str, Any]:
    if not db.reopen_followup(followup_id):
        raise HTTPException(status_code=404, detail="Follow-up not found or not completed")
    return {"ok": True, "id": followup_id}


@app.get("/api/stats")
async def stats() -> dict[str, Any]:
    return db.stats()


@app.websocket("/ws/visit")
async def visit_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    language = websocket.query_params.get("language", "en-IN")
    session = VisitSession(websocket, language=language, settings=settings)
    await session.send(
        {
            "type": "ready",
            "language": session.language,
            "gnani_configured": settings.gnani_ready,
            "frame_bytes": 1024,
        }
    )
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            payload = message.get("bytes")
            if payload:
                await session.feed_audio(payload)
                continue
            text = message.get("text")
            if not text:
                continue
            try:
                command = json.loads(text)
            except json.JSONDecodeError:
                continue
            await session.handle(command)
    except WebSocketDisconnect:
        pass
    except Exception as error:  # noqa: BLE001
        logger.warning("Voice session failed: %s", error)
        await session.error(t("session_error", session.language))
    finally:
        await session.reset()


# Serve the built React app when it exists, so `uvicorn app.main:app` alone is
# enough for the demo.
_dist = PROJECT_DIR / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
