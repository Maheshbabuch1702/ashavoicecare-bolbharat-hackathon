"""Stream the saved demo WAV through the backend WebSocket.

This is the test that text injection cannot cover: real Gnani streaming STT ->
partial frames -> final transcript -> structured draft -> save.

By default this starts a throwaway backend with a temporary database, so demo
data is never touched. Pass --url to reuse an already-running server instead.

Usage: python tools/e2e_audio.py [path-to-wav] [--url ws://host/ws/visit]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import wave
from pathlib import Path

import websockets

from _e2e_harness import isolated_backend

ROOT = Path(__file__).resolve().parents[1]
FRAME_BYTES = 1024  # 512 samples * 2 bytes


async def read_until(ws, predicate, timeout=40):
    seen = []
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        message = json.loads(raw)
        seen.append(message)
        if message["type"] in {"partial", "alarm", "draft", "saved", "error", "speak"}:
            print(f"  <- {message['type']}: {json.dumps(message)[:160]}")
        if predicate(message):
            return message, seen


async def run(ws_base: str, path: str | None) -> int:
    wav_path = Path(path) if path else ROOT / "data" / "sample_visit.wav"
    with wave.open(str(wav_path), "rb") as wav:
        assert wav.getframerate() == 16000, "demo WAV must be 16 kHz"
        assert wav.getnchannels() == 1, "demo WAV must be mono"
        pcm = wav.readframes(wav.getnframes())

    print(f"  server: {ws_base}")
    async with websockets.connect(f"{ws_base}?language=en-IN", max_size=None) as ws:
        await read_until(ws, lambda m: m["type"] == "ready", timeout=10)
        await ws.send(json.dumps({"type": "start", "language": "en-IN", "sample_rate": 16000}))
        connected, _ = await read_until(ws, lambda m: m["type"] in {"recording", "error"}, timeout=15)
        if connected["type"] == "error":
            print("FAILED:", connected["message"])
            return 1

        for offset in range(0, len(pcm), FRAME_BYTES):
            await ws.send(pcm[offset : offset + FRAME_BYTES])
            await asyncio.sleep(0.032)
        await asyncio.sleep(0.4)
        await ws.send(json.dumps({"type": "stop"}))

        draft, seen = await read_until(ws, lambda m: m["type"] in {"draft", "error"}, timeout=45)
        if draft["type"] == "error":
            print("FAILED:", draft["message"])
            return 1

        interims = [m for m in seen if m["type"] == "partial" and m.get("interim")]
        print(f"  interim frames: {len(interims)}")
        print(f"  transcript: {draft['record']['transcript']}")
        print(f"  record: name={draft['record']['patient_name']} id={draft['record']['beneficiary_id']} "
              f"type={draft['record']['visit_type']} weight={draft['record']['weight_kg']} "
              f"anc={draft['record']['anc_completed']} ifa={draft['record']['ifa_provided']} "
              f"next={draft['record']['next_visit_date']}")

        assert interims, "no interim partial frames arrived (x-partials not active?)"
        assert draft["record"]["beneficiary_id"] == "ASHA102", draft["record"]
        assert draft["record"]["weight_kg"] == 55.0, draft["record"]

        try:
            await read_until(ws, lambda m: m["type"] == "speak", timeout=6)
        except asyncio.TimeoutError:
            print("  (no speak frame)")

        await ws.send(json.dumps({"type": "confirm"}))
        saved, _ = await read_until(ws, lambda m: m["type"] in {"saved", "error"}, timeout=20)
        if saved["type"] == "error":
            print("FAILED on save:", saved["message"])
            return 1
        print(f"  SAVED {saved['visit_id']} · followups={len(saved['followups'])}")

    print("OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", nargs="?", help="16 kHz mono WAV to stream")
    parser.add_argument(
        "--url",
        default="",
        help="reuse a running server, e.g. ws://127.0.0.1:8000/ws/visit",
    )
    args = parser.parse_args()
    if args.url:
        return asyncio.run(run(args.url.rstrip("/"), args.wav))
    with isolated_backend() as ws_base:
        return asyncio.run(run(ws_base, args.wav))


if __name__ == "__main__":
    raise SystemExit(main())
