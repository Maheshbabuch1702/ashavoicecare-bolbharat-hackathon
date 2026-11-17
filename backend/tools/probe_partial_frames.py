"""Stream the saved sample WAV with x-partials enabled and print every frame."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import wave
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.smoke_gnani import load_env  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
load_env(ROOT / ".env")

HEADERS = {
    "x-api-key-id": os.environ["GNANI_API_KEY"],
    "model": "prisma-v3.0",
    "language_code": "en-IN",
    "format": "transcribe",
    "x-sample-rate": "16000",
    "x-partials": "true",
    "keyterms": json.dumps(["ANC", "IFA", "ASHA", "beneficiary", "weight"], ensure_ascii=True),
}


async def main() -> None:
    with wave.open(str(ROOT / "data" / "sample_visit.wav"), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        frames = wav.readframes(wav.getnframes())
    print(f"wav: rate={rate} channels={channels} width={width} bytes={len(frames)}")

    async with websockets.connect(
        "wss://api.vachana.ai/stt/v3/stream",
        additional_headers=HEADERS,
        max_size=None,
        proxy=None,
    ) as ws:
        first = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        print("config:", first)

        chunk = 512 * channels * width

        async def sender() -> None:
            for offset in range(0, len(frames), chunk):
                await ws.send(frames[offset : offset + chunk])
                await asyncio.sleep(0.032)
            await asyncio.sleep(1.0)
            await ws.send(json.dumps({"type": "commit"}))

        task = asyncio.create_task(sender())
        deadline = asyncio.get_running_loop().time() + 25
        while asyncio.get_running_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=3)
            except asyncio.TimeoutError:
                break
            if isinstance(raw, bytes):
                continue
            print("frame:", raw[:400])
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
