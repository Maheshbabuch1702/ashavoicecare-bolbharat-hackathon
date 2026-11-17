"""Smoke-test the Gnani credentials end to end.

1. Synthesises a demo visit note with Gnani TTS (Timbre v3.0).
2. Feeds that WAV straight back into Gnani STT (Prisma v3.0) and prints the transcript.

If this passes, both the STT and TTS halves of the hackathon demo are wired correctly.

Usage:  python tools/smoke_gnani.py
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)

# Cloudflare in front of api.vachana.ai blocks Python's default urllib UA (error 1010).
UA = "asha-voicecare/0.1 (+hackathon prototype)"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def tts(text: str, language: str) -> bytes:
    payload = {
        "text": text,
        "voice": os.environ.get("GNANI_TTS_VOICE", "Shivani"),
        "model": os.environ.get("GNANI_TTS_MODEL", "timbre-v3.0"),
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
    request = urllib.request.Request(
        "https://api.vachana.ai/api/v1/tts/inference",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-API-Key-ID": os.environ["GNANI_API_KEY"],
            "User-Agent": UA,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def stt(audio: bytes, language: str) -> dict:
    boundary = f"----asha{uuid.uuid4().hex}"
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()
        )

    mime = mimetypes.guess_type("audio.wav")[0] or "audio/wav"
    parts.append(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="audio_file"; filename="audio.wav"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
    )
    parts.append(audio)
    parts.append(b"\r\n")
    for name, value in (
        ("model", os.environ.get("GNANI_STT_MODEL", "prisma-v3.0")),
        ("language_code", language),
        ("format", "transcribe"),
    ):
        field(name, value)
    parts.append(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        "https://api.vachana.ai/stt/v3",
        data=b"".join(parts),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-API-Key-ID": os.environ["GNANI_API_KEY"],
            "User-Agent": UA,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    load_env(ROOT / ".env")
    if not os.environ.get("GNANI_API_KEY"):
        print("GNANI_API_KEY missing in backend/.env", file=sys.stderr)
        return 2

    note = "Lakshmi, beneficiary ID ASHA102. Pregnancy visit. Weight fifty five kilo. ANC completed. IFA tablets given. Next visit November 20."
    print("TTS  ->", note)
    try:
        audio = tts(note, "en-IN")
    except urllib.error.HTTPError as error:
        print(f"TTS failed: {error.code} {error.read()[:400]!r}", file=sys.stderr)
        return 1

    wav_path = OUT / "sample_visit.wav"
    wav_path.write_bytes(audio)
    print(f"     saved {wav_path} ({len(audio)} bytes)")

    try:
        result = stt(audio, "en-IN")
    except urllib.error.HTTPError as error:
        print(f"STT failed: {error.code} {error.read()[:400]!r}", file=sys.stderr)
        return 1

    print("STT  <-", result.get("transcript"))
    (OUT / "sample_visit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
