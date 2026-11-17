"""Per-visit conversation state machine.

    idle -> recording -> finalising -> review -> saved
                             ^            |
                             +-- corrections

One Gnani STT stream stays open for the whole visit, so the worker can
interrupt the read-back without waiting for a reconnect.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Any

from . import db
from .config import Settings, get_settings
from .danger import DangerHit, DangerResult, detect
from .dialog import build_readback, format_date, format_weight, looks_like_echo, parse_correction
from .extract import VisitRecord, extract, extract_rules
from .followups import build_followups
from .gnani import FRAME_BYTES, GnaniSTTStream
from .i18n import DANGER_WARNING, normalise_language, t

SendJSON = Any  # fastapi WebSocket.send_json

logger = logging.getLogger(__name__)


class VisitSession:
    def __init__(self, websocket, *, language: str = "en-IN", settings: Settings | None = None) -> None:
        self.ws = websocket
        self.settings = settings or get_settings()
        self.language = normalise_language(language)
        self.state = "idle"
        self.stt: GnaniSTTStream | None = None
        self.buffer = bytearray()
        self.transcript = ""
        self.segments: list[str] = []
        self.record: VisitRecord | None = None
        self.danger: list[DangerHit] = []
        self.first_alarm: str | None = None
        self.corrections: list[dict] = []
        self.last_spoken = ""
        self.speech_id = 0
        self._transcript_event = asyncio.Event()
        self._last_transcript_at = 0.0
        self._lock = asyncio.Lock()
        self.sample_rate = 16000

    # ------------------------------------------------------------------ io
    async def send(self, payload: dict) -> None:
        try:
            await self.ws.send_json(payload)
        except Exception:  # noqa: BLE001 - client went away
            pass

    async def speak(self, text: str) -> None:
        if not text:
            return
        self.last_spoken = text
        self.speech_id += 1
        await self.send(
            {"type": "speak", "id": self.speech_id, "text": text, "language": self.language}
        )

    async def error(self, message: str, *, fatal: bool = False) -> None:
        await self.send({"type": "error", "message": message, "fatal": fatal})

    # ------------------------------------------------------------- commands
    async def handle(self, message: dict) -> None:
        kind = message.get("type")

        if kind == "start":
            await self.start(language=message.get("language"), sample_rate=message.get("sample_rate"))
        elif kind == "stop":
            await self.finish_recording()
        elif kind == "confirm":
            await self.save()
        elif kind == "cancel":
            await self.reset()
        elif kind == "barge_in":
            # The client already stopped playback; flush the open utterance so
            # the correction transcript arrives sooner.
            if self.stt:
                await self.stt.commit()
        elif kind == "inject":
            await self._on_spoken_text(str(message.get("text") or ""))
        elif kind == "language":
            self.language = normalise_language(message.get("language"))
            await self.send({"type": "language_changed", "language": self.language})
        elif kind == "ping":
            await self.send({"type": "pong"})

    # ------------------------------------------------------------- lifecycle
    async def start(self, *, language: str | None = None, sample_rate: int | None = None) -> None:
        if self.stt:
            await self.stt.close()
        self.language = normalise_language(language) if language else self.language
        self.sample_rate = int(sample_rate or 16000)
        self.transcript = ""
        self.segments = []
        self.record = None
        self.danger = []
        self.first_alarm = None
        self.corrections = []
        self.buffer.clear()

        self.stt = GnaniSTTStream(
            language=self.language,
            on_event=self._on_frame,
            settings=self.settings,
            sample_rate=self.sample_rate,
        )
        try:
            await self.stt.connect()
        except Exception as error:  # noqa: BLE001
            self.stt = None
            logger.warning("Could not start speech recognition: %s", error)
            await self.error(t("stt_start_failed", self.language), fatal=True)
            return

        self.state = "recording"
        await self.send(
            {
                "type": "recording",
                "language": self.language,
                "sample_rate": self.sample_rate,
                "frame_bytes": FRAME_BYTES,
            }
        )

    async def feed_audio(self, chunk: bytes) -> None:
        """Re-chunk arbitrary browser payloads into exact 1024-byte PCM frames."""
        if not self.stt or self.state in {"idle", "saved"}:
            return
        self.buffer.extend(chunk)
        while len(self.buffer) >= FRAME_BYTES:
            frame = bytes(self.buffer[:FRAME_BYTES])
            del self.buffer[:FRAME_BYTES]
            try:
                await self.stt.send_audio(frame)
            except Exception:  # noqa: BLE001
                return

    async def reset(self) -> None:
        if self.stt:
            await self.stt.close()
            self.stt = None
        self.state = "idle"
        self.transcript = ""
        self.segments = []
        self.record = None
        self.danger = []
        self.corrections = []
        self.buffer.clear()

    # ------------------------------------------------------- STT event path
    async def _on_frame(self, frame: dict) -> None:
        kind = frame.get("type")
        if kind == "speech_start":
            await self.send({"type": "speech_start"})
            return
        if kind == "partial_transcript":
            await self._on_interim_text(frame.get("text") or "")
            return
        if kind == "error":
            logger.warning("Gnani STT error frame: %s", frame.get("message"))
            await self.error(t("stt_error", self.language))
            return
        if kind == "connected":
            await self.send({"type": "stt_connected", "config": frame.get("config", {})})
            return
        if kind != "transcript":
            return

        text = (frame.get("text") or "").strip()
        if not text:
            return
        self._last_transcript_at = time.monotonic()
        self._transcript_event.set()
        await self._on_spoken_text(text, frame)

    async def _on_spoken_text(self, text: str, frame: dict | None = None) -> None:
        text = (text or "").strip()
        if not text:
            return
        async with self._lock:
            if self.state == "recording":
                await self._append_transcript(text, frame)
            elif self.state in {"review", "awaiting_correction"}:
                await self._handle_review_utterance(text)
            elif self.state == "finalising":
                # Late segment still belongs to the dictation.
                await self._append_transcript(text, frame, notify=False)

    async def _on_interim_text(self, text: str) -> None:
        """Preview the in-flight utterance without committing it to the record.

        Interims are unstable, so danger detection and alarms stay on final
        transcripts only; the record preview is recomputed for the UI.
        """
        text = (text or "").strip()
        if not text or self.state != "recording":
            return
        if self.transcript and self.transcript.rstrip().lower().endswith(text.lower()):
            return
        preview = f"{self.transcript} {text}".strip()
        partial = extract_rules(preview, language=self.language)
        await self.send(
            {
                "type": "partial",
                "text": text,
                "transcript": self.transcript,
                "interim": True,
                "record": partial.as_dict(),
                "danger": [hit.as_dict() for hit in self.danger],
            }
        )

    async def _append_transcript(self, text: str, frame: dict | None, *, notify: bool = True) -> None:
        self.segments.append(text)
        self.transcript = " ".join(self.segments)

        partial = extract_rules(self.transcript, language=self.language)
        result = detect(
            self.transcript,
            language=self.language,
            visit_type=partial.visit_type,
            weight_kg=partial.weight_kg,
        )

        new_hits = [hit for hit in result.hits if hit.code not in {h.code for h in self.danger}]
        for hit in new_hits:
            self.danger.append(hit)

        if notify:
            await self.send(
                {
                    "type": "partial",
                    "text": text,
                    "transcript": self.transcript,
                    "segment_index": (frame or {}).get("segment_index"),
                    "record": partial.as_dict(),
                    "danger": [hit.as_dict() for hit in self.danger],
                }
            )

        if new_hits:
            await self._raise_alarm(new_hits)

    async def _raise_alarm(self, hits: list[DangerHit]) -> None:
        category = hits[0].category
        warning = DANGER_WARNING.get(category, DANGER_WARNING["pregnancy"]).get(
            self.language, DANGER_WARNING[category]["en-IN"]
        )
        await self.send(
            {
                "type": "alarm",
                "danger": [hit.as_dict() for hit in self.danger],
                "new": [hit.as_dict() for hit in hits],
                "message": warning,
                "language": self.language,
            }
        )
        if self.first_alarm is None:
            self.first_alarm = warning

    # ---------------------------------------------------------- end of note
    async def finish_recording(self) -> None:
        if self.state != "recording":
            return
        self.state = "finalising"
        if self.stt:
            await self.stt.commit()

        # Wait for the last utterance to be transcribed: quiet for 1.1 s, max 6 s.
        deadline = time.monotonic() + 6.0
        quiet_until = time.monotonic() + 1.1
        while time.monotonic() < deadline:
            await asyncio.sleep(0.15)
            if time.monotonic() >= quiet_until:
                break
            if self._transcript_event.is_set():
                self._transcript_event.clear()
                quiet_until = time.monotonic() + 1.1

        if not self.transcript.strip():
            self.state = "recording"
            await self.speak(t("not_understood", self.language))
            return

        await self._build_draft()

    async def _build_draft(self) -> None:
        record = extract(self.transcript, language=self.language, settings=self.settings)
        result = detect(
            self.transcript,
            language=self.language,
            visit_type=record.visit_type,
            weight_kg=record.weight_kg,
        )
        # Keep every danger sign ever detected in this visit (never silently drop).
        known = {hit.code for hit in self.danger}
        for hit in result.hits:
            if hit.code not in known:
                self.danger.append(hit)

        self.record = record
        plan = build_followups(record, self.danger)
        self.state = "review"

        missing = record.missing()
        unclear = record.low_confidence()
        readback = build_readback(record, self.language, missing=missing)

        await self.send(
            {
                "type": "draft",
                "record": record.as_dict(),
                "missing": missing,
                "unclear": unclear,
                "danger": [hit.as_dict() for hit in self.danger],
                "followups": plan.as_list(),
                "readback": readback,
                "language": self.language,
            }
        )
        await self.speak(readback)

    # ------------------------------------------------------------- review
    async def _handle_review_utterance(self, text: str) -> None:
        if looks_like_echo(text, self.last_spoken):
            return

        # Barge-in: stop whatever the assistant is saying.
        await self.send({"type": "stop_audio"})

        # A spoken danger sign must still raise an alarm during review.
        result = detect(
            text,
            language=self.language,
            visit_type=self.record.visit_type if self.record else "pregnancy_anc",
            weight_kg=self.record.weight_kg if self.record else None,
        )
        known = {hit.code for hit in self.danger}
        fresh = [hit for hit in result.hits if hit.code not in known]
        if fresh:
            self.danger.extend(fresh)
            await self._raise_alarm(fresh)
            await self.speak(
                DANGER_WARNING.get(fresh[0].category, DANGER_WARNING["pregnancy"]).get(
                    self.language, DANGER_WARNING["pregnancy"]["en-IN"]
                )
            )
            await self._publish_draft()
            return

        # "No, there is no bleeding" retracts an earlier false positive.
        retracted = self._retract_danger(text)
        if retracted:
            await self._publish_draft()
            await self.speak(self._readback())
            return

        correction = parse_correction(
            text, self.record, language=self.language, today=date.today()
        ) if self.record else None

        if correction and self.record:
            setattr(self.record, correction.field, correction.value)
            self.record.confidence[correction.field] = 1.0
            self.record.evidence[correction.field] = f"voice correction: {text}"
            self.corrections.append(
                {
                    "field": correction.field,
                    "value": correction.value,
                    "utterance": text,
                    "at": date.today().isoformat(),
                }
            )
            # Weight changes can add or clear the low-birth-weight rule.
            if correction.field == "weight_kg":
                self._refresh_weight_danger()

            await self._publish_draft()
            spoken = t(
                "corrected",
                self.language,
                field=self._field_label(correction.field),
                value=correction.spoken,
            )
            await self.speak(spoken)
            return

        if self.state == "awaiting_correction" or self._is_negative(text):
            self.state = "awaiting_correction"
            await self.speak(t("ask_correction", self.language))
            return

        if self._is_affirmative(text):
            await self.save()
            return

        await self.speak(t("not_understood", self.language))

    def _refresh_weight_danger(self) -> None:
        if not self.record:
            return
        weight = self.record.weight_kg
        newborn = self.record.visit_type == "newborn_hbnc"
        existing = next((hit for hit in self.danger if hit.code == "low_birth_weight"), None)
        should_flag = bool(newborn and weight is not None and weight < 2.5)
        if should_flag and existing is None:
            self.danger.append(
                DangerHit(
                    code="low_birth_weight",
                    category="newborn",
                    label="Low birth weight (<2.5 kg)",
                    label_local="Low birth weight (<2.5 kg)",
                    matched_text=f"{weight} kg",
                    urgency="urgent",
                    source="G2 §Newborn danger signs",
                )
            )
        elif not should_flag and existing is not None:
            self.danger = [hit for hit in self.danger if hit.code != "low_birth_weight"]

    def _retract_danger(self, text: str) -> bool:
        """Handle 'no bleeding' / 'bleeding illa' after an earlier alert."""
        from .normalize import fold, normalise

        lowered = fold(normalise(text))
        if not any(word in lowered for word in ("no", "not", "illa", "illai", "இல்லை", "नहीं")):
            return False
        removed = False
        keep: list[DangerHit] = []
        for hit in self.danger:
            keywords = {
                "vaginal_bleeding": ("bleed", "இரத்த", "खून"),
                "high_fever": ("fever", "காய்ச்ச", "बुखार"),
                "convulsions": ("convuls", "fit", "வலிப்ப", "दौर"),
                "severe_headache": ("headache", "தலைவலி", "सिरदर्द"),
                "newborn_jjaundice": ("jaundice", "மஞ்சள்", "पीलिया"),
                "newborn_jaundice": ("jaundice", "மஞ்சள்", "पीलिया"),
                "newborn_not_feeding": ("feed", "பால்", "दूध"),
            }.get(hit.code, ())
            if keywords and any(word in lowered for word in keywords):
                removed = True
                continue
            keep.append(hit)
        if removed:
            self.danger = keep
        return removed

    def _is_affirmative(self, text: str) -> bool:
        from .normalize import is_affirmative, is_negative

        return is_affirmative(text) and not is_negative(text)

    def _is_negative(self, text: str) -> bool:
        from .normalize import is_negative

        return is_negative(text)

    def _field_label(self, field: str) -> str:
        from .i18n import field_label

        return field_label(field, self.language)

    def _readback(self) -> str:
        if not self.record:
            return ""
        return build_readback(self.record, self.language, missing=self.record.missing())

    async def _publish_draft(self) -> None:
        if not self.record:
            return
        plan = build_followups(self.record, self.danger)
        await self.send(
            {
                "type": "draft",
                "record": self.record.as_dict(),
                "missing": self.record.missing(),
                "unclear": self.record.low_confidence(),
                "danger": [hit.as_dict() for hit in self.danger],
                "followups": plan.as_list(),
                "readback": self._readback(),
                "language": self.language,
                "corrected": True,
            }
        )
        self.state = "review"

    # --------------------------------------------------------------- saving
    async def save(self) -> None:
        if not self.record or self.state not in {"review", "awaiting_correction"}:
            return

        plan = build_followups(self.record, self.danger)
        saved = db.save_visit(
            self.record,
            self.danger,
            plan,
            corrections=self.corrections,
            status="confirmed",
        )
        self.state = "saved"
        if self.stt:
            await self.stt.close()
            self.stt = None

        await self.send(
            {
                "type": "saved",
                "visit_id": saved["visit_id"],
                "beneficiary_id": saved["beneficiary_id"],
                "followups": saved["followups"],
                "danger": saved["danger"],
                "record": self.record.as_dict(),
                "transcript": self.transcript,
                "saved_at": saved["saved_at"],
            }
        )
        await self.speak(t("saved", self.language))
