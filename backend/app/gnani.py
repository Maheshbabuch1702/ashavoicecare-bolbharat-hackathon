"""Gnani Speech API client.

STT is streamed over a WebSocket from the backend, never from the browser:
browsers cannot set the `x-api-key-id` upgrade header, and this keeps the key
server-side. See docs: https://docs.gnani.ai/api/STT/stt-websocket.md

Audio contract: raw PCM, signed 16-bit little-endian, mono, 1024-byte frames
(512 samples) sent at real-time cadence.
"""

from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

import httpx
import websockets

from .config import Settings, get_settings

STT_URL = "wss://api.vachana.ai/stt/v3/stream"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

FRAME_BYTES = 1024

# Medical vocabulary the recogniser should favour. Verified on real audio:
# without this, "ANC" came back as "Hence he" and "IFA" as "Tifa".
KEYTERMS = (
    "ANC", "IFA", "TT", "HBNC", "PHC", "ASHA", "beneficiary", "vaccination",
    "immunization", "hemoglobin", "hemoglobin", "weight", "kilo", "checkup",
    "pregnancy", "newborn", "tablets", "injection", "next visit", "danger sign",
    "bleeding", "fever", "convulsion", "breastfeeding", "postnatal",
)

LANGUAGE_HINTS = {
    "en-IN": "en-IN",
    # Prisma v3.0 accepts a comma-separated hint list, so code-mixed speech
    # ("weight 55 kilo" inside Tamil) is handled in one session.
    "ta-IN": "ta-IN,en-IN",
    "hi-IN": "hi-IN,en-IN",
    "te-IN": "te-IN,en-IN",
    "kn-IN": "kn-IN,en-IN",
    "ml-IN": "ml-IN,en-IN",
    "mr-IN": "mr-IN,en-IN",
    "bn-IN": "bn-IN,en-IN",
    "gu-IN": "gu-IN,en-IN",
    "pa-IN": "pa-IN,en-IN",
}

TranscriptHandler = Callable[[dict], Awaitable[None]]


class GnaniSTTStream:
    """One streaming session. Mirrors the kiosk-style VAD flow from the docs."""

    def __init__(
        self,
        *,
        language: str,
        on_event: TranscriptHandler,
        settings: Settings | None = None,
        sample_rate: int = 16000,
    ) -> None:
        self.settings = settings or get_settings()
        self.language = language
        self.sample_rate = sample_rate
        self.on_event = on_event
        self._ws: websockets.ClientConnection | None = None
        self._reader_task: asyncio.Task | None = None
        self._closed = False

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key-id": self.settings.gnani_api_key,
            "model": self.settings.gnani_stt_model,
            "language_code": LANGUAGE_HINTS.get(self.language, self.language),
            "format": "transcribe",
            "x-sample-rate": str(self.sample_rate),
            "x-idle-timeout-sec": "180",
            # Tuned for a noisy outdoor home visit rather than a quiet headset.
            "x-vad-threshold": "0.65",
            "x-min-speech-ms": "200",
            "x-min-segment-ms": "150",
            "x-min-silence-ms": "600",
            "x-max-speech-s": "30",
            # Undocumented header verified against the live service: without it
            # the server advertises partials_enabled=false and only sends finals.
            "x-partials": "true",
            "keyterms": json.dumps(KEYTERMS, ensure_ascii=True),
            "topic": "ASHA home visit, maternal and newborn health record",
        }

    async def connect(self) -> None:
        if not self.settings.gnani_ready:
            raise RuntimeError("GNANI_API_KEY is not configured")
        try:
            self._ws = await websockets.connect(
                STT_URL,
                additional_headers=self._headers(),
                ping_interval=20,
                ping_timeout=20,
                max_size=None,
                proxy=None,
            )
        except TypeError:
            # Older websockets releases use `extra_headers` / no `proxy`.
            self._ws = await websockets.connect(
                STT_URL,
                extra_headers=self._headers(),
                ping_interval=20,
                max_size=None,
            )
        self._reader_task = asyncio.create_task(self._reader())

    async def _reader(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    continue
                try:
                    frame = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                kind = frame.get("type")
                if kind == "final_transcript":
                    # Gnani v3 names the final frame "final_transcript"; the
                    # rest of the app speaks in "transcript" events.
                    await self.on_event(
                        {
                            "type": "transcript",
                            "text": frame.get("text") or "",
                            "segment_index": frame.get("segment_index"),
                            "utterance_id": frame.get("utterance_id"),
                        }
                    )
                elif kind == "partial_transcript":
                    await self.on_event(
                        {
                            "type": "partial_transcript",
                            "text": frame.get("text") or "",
                            "stable_text": frame.get("stable_text") or "",
                            "utterance_id": frame.get("utterance_id"),
                        }
                    )
                elif kind in {"speech_start", "processing", "error", "connected"}:
                    await self.on_event(frame)
        except websockets.ConnectionClosed:
            if not self._closed:
                await self.on_event({"type": "error", "message": "Speech connection closed"})
        except Exception as error:  # noqa: BLE001
            if not self._closed:
                await self.on_event({"type": "error", "message": f"Speech stream failed: {error}"})

    async def send_audio(self, chunk: bytes) -> None:
        if self._ws is None or self._closed:
            return
        await self._ws.send(chunk)

    async def commit(self) -> None:
        """Force-close the open utterance (used on barge-in and on stop)."""
        if self._ws and not self._closed:
            await self._ws.send(json.dumps({"type": "commit"}))

    async def close(self) -> None:
        self._closed = True
        if self._reader_task:
            self._reader_task.cancel()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:  # noqa: BLE001
                pass


async def synthesize(text: str, language: str, settings: Settings | None = None) -> bytes:
    """Render speech with Gnani Timbre. Returns WAV bytes."""
    settings = settings or get_settings()
    payload = {
        "text": text,
        "voice": settings.gnani_tts_voice,
        "model": settings.gnani_tts_model,
        "language": language,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 16000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            TTS_URL,
            headers={
                "X-API-Key-ID": settings.gnani_api_key,
                "Content-Type": "application/json",
                "User-Agent": "asha-voicecare/0.1",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.content
