"""End-to-end WebSocket test for the visit flow.

Drives the same protocol the browser uses, but injects text instead of audio so
the test is deterministic and needs no microphone.

By default this starts a throwaway backend with a temporary database, so demo
data is never touched. Pass --url to reuse an already-running server instead.

Usage: python tools/e2e_ws.py [normal|danger|correction] [--url ws://host/ws/visit]
"""

from __future__ import annotations

import argparse
import asyncio
import json

import websockets

from _e2e_harness import isolated_backend

DEMO_1 = (
    "Lakshmi, beneficiary ID ASHA102. Pregnancy visit. Weight 55 kilo. "
    "ANC completed. IFA tablets given. Next visit November 20."
)
DEMO_2 = "Newborn has high fever. Weight 2.8 kilo."
DEMO_3 = "Weight is 2.5 kilo."


async def read_until(ws, predicate, timeout=25):
    """Collect messages until predicate matches; return the matching message and all seen."""
    seen = []
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        message = json.loads(raw)
        seen.append(message)
        print(f"  <- {message['type']}: {json.dumps(message)[:180]}")
        if predicate(message):
            return message, seen


async def run(ws_base: str, scenario: str) -> int:
    print(f"  server: {ws_base}")
    async with websockets.connect(f"{ws_base}?language=en-IN", max_size=None) as ws:
        await read_until(ws, lambda m: m["type"] == "ready")
        await ws.send(json.dumps({"type": "start", "language": "en-IN", "sample_rate": 16000}))
        await read_until(ws, lambda m: m["type"] in {"recording", "error"})

        if scenario == "normal":
            await ws.send(json.dumps({"type": "inject", "text": DEMO_1}))
        elif scenario == "danger":
            await ws.send(json.dumps({"type": "inject", "text": DEMO_2}))
        elif scenario == "correction":
            await ws.send(json.dumps({"type": "inject", "text": DEMO_3}))
        else:
            raise SystemExit(f"unknown scenario {scenario}")

        await asyncio.sleep(0.4)
        await ws.send(json.dumps({"type": "stop"}))

        draft, seen = await read_until(ws, lambda m: m["type"] in {"draft", "error"})
        alarms = [m for m in seen if m["type"] == "alarm"]
        if draft["type"] == "error":
            print("FAILED:", draft["message"])
            return 1

        missing = draft.get("missing") or []
        print(f"  missing: {missing}")
        print(f"  danger: {[hit['code'] for hit in draft.get('danger', [])]}")
        print(f"  followups: {[task['title'] for task in draft.get('followups', [])]}")

        # Wait for the read-back 'speak' frame.
        try:
            await read_until(ws, lambda m: m["type"] == "speak", timeout=6)
        except asyncio.TimeoutError:
            print("  (no speak frame)")

        if scenario == "danger":
            assert alarms, "no alarm frame received"
            assert any(t["priority"] == "urgent" for t in draft["followups"]), "no urgent referral task"
            assert draft["danger"], "no danger in draft"

        if scenario == "correction":
            await ws.send(json.dumps({"type": "inject", "text": "No, weight is 2.8 kilo"}))
            corrected, _ = await read_until(ws, lambda m: m["type"] in {"draft", "error"})
            assert corrected["record"]["weight_kg"] == 2.8, corrected
            print("  corrected weight:", corrected["record"]["weight_kg"])

        await ws.send(json.dumps({"type": "confirm"}))
        saved, _ = await read_until(ws, lambda m: m["type"] in {"saved", "error"})
        if saved["type"] == "error":
            print("FAILED on save:", saved["message"])
            return 1
        print(f"  SAVED {saved['visit_id']} · followups={len(saved['followups'])} · danger={len(saved['danger'])}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scenario",
        nargs="?",
        default="normal",
        choices=["normal", "danger", "correction"],
    )
    parser.add_argument(
        "--url",
        default="",
        help="reuse a running server, e.g. ws://127.0.0.1:8000/ws/visit",
    )
    args = parser.parse_args()
    if args.url:
        return asyncio.run(run(args.url.rstrip("/"), args.scenario))
    with isolated_backend() as ws_base:
        return asyncio.run(run(ws_base, args.scenario))


if __name__ == "__main__":
    raise SystemExit(main())
