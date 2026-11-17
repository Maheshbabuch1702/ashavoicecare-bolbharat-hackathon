"""Probe which header enables interim (partial) transcripts on Gnani streaming STT."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.smoke_gnani import load_env  # noqa: E402

load_env(Path(__file__).resolve().parents[1] / ".env")

BASE = {
    "x-api-key-id": os.environ["GNANI_API_KEY"],
    "model": "prisma-v3.0",
    "language_code": "en-IN",
    "format": "transcribe",
    "x-sample-rate": "16000",
}

CANDIDATES = [
    {},
    {"x-partials-enabled": "true"},
    {"partials_enabled": "true"},
    {"x-enable-partials": "true"},
    {"x-partials": "true"},
    {"x-interim-results": "true"},
]


async def probe(extra: dict[str, str]) -> None:
    headers = {**BASE, **extra}
    label = json.dumps(extra) if extra else "default"
    try:
        async with websockets.connect(
            "wss://api.vachana.ai/stt/v3/stream", additional_headers=headers, proxy=None
        ) as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            frame = json.loads(raw)
            config = frame.get("config", {})
            print(f"{label:42} partials_enabled={config.get('partials_enabled')} config={config}")
    except Exception as error:  # noqa: BLE001
        print(f"{label:42} FAILED {error}")


async def main() -> None:
    for extra in CANDIDATES:
        await probe(extra)


if __name__ == "__main__":
    asyncio.run(main())
