"""Throwaway probe: does Gnani keyterms/word-boosting fix medical-term ASR errors?"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.smoke_gnani import load_env, stt, tts  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
load_env(ROOT / ".env")

wav = (ROOT / "data" / "sample_visit.wav").read_bytes()
terms = ["ANC", "IFA", "TT", "ASHA", "beneficiary", "hemoglobin", "vaccination", "ANC checkup", "IFA tablets"]


def stt_with_terms(audio: bytes, language: str, keyterms: list[str]) -> dict:
    boundary = f"----asha{uuid.uuid4().hex}"
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
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
        ("model", "prisma-v3.0"),
        ("language_code", language),
        ("format", "transcribe"),
        ("keyterms", json.dumps(keyterms)),
    ):
        field(name, value)
    parts.append(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        "https://api.vachana.ai/stt/v3",
        data=b"".join(parts),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-API-Key-ID": os.environ["GNANI_API_KEY"],
            "User-Agent": "asha-voicecare/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


print("== baseline (no keyterms)")
print(stt(wav, "en-IN").get("transcript"))

print("\n== with keyterms")
try:
    print(stt_with_terms(wav, "en-IN", terms).get("transcript"))
except urllib.error.HTTPError as e:
    print("failed", e.code, e.read()[:300])

tamil = "லட்சுமி, பயனாளி ஐடி ASHA102. கர்ப்பகால பரிசோதனை முடிந்தது. எடை ஐம்பத்தைந்து கிலோ. ஐஎஃப்ஏ மாத்திரை கொடுத்தேன். அடுத்த வருகை நவம்பர் இருபது."
print("\n== tamil TTS round-trip")
try:
    audio = tts(tamil, "ta-IN")
    (ROOT / "data" / "sample_tamil.wav").write_bytes(audio)
    print("tts ok", len(audio), "bytes")
    for fmt in ("transcribe", "codemix"):
        try:
            print(f"[{fmt}]", stt(audio, "ta-IN").get("transcript"))
        except urllib.error.HTTPError as e:
            print(f"[{fmt}] failed", e.code, e.read()[:300])
        break
except urllib.error.HTTPError as e:
    print("failed", e.code, e.read()[:300])
