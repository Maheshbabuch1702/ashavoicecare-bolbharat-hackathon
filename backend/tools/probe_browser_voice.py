"""Reproduce the browser voice-start path and capture console/JS errors.

Launches headless Chrome with a fake microphone, clicks "Tap to speak" and
prints every console message, exception and the resulting UI state.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = "http://127.0.0.1:8000/"
PORT = 9222


async def cdp(ws, method: str, params: dict | None = None, counter: list[int] | None = None) -> dict:
    counter[0] += 1
    await ws.send(json.dumps({"id": counter[0], "method": method, "params": params or {}}))
    while True:
        raw = json.loads(await ws.recv())
        if raw.get("id") == counter[0]:
            return raw
        await print_event(raw)


async def print_event(raw: dict) -> None:
    method = raw.get("method")
    params = raw.get("params", {})
    if method == "Runtime.consoleAPICalled":
        args = [str(a.get("value", a.get("description", ""))) for a in params.get("args", [])]
        print(f"CONSOLE {params.get('type')}: {' '.join(args)}")
    elif method == "Runtime.exceptionThrown":
        detail = params.get("exceptionDetails", {})
        print(f"EXCEPTION: {detail.get('text')} {detail.get('exception', {}).get('description', '')}")
    elif method == "Log.entryAdded":
        entry = params.get("entry", {})
        print(f"LOG {entry.get('level')}: {entry.get('text')}")
    elif method == "Runtime.consoleAPICalled":
        pass


async def main() -> int:
    profile = tempfile.mkdtemp(prefix="asha-chrome-")
    chrome = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--autoplay-policy=no-user-gesture-required",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 15
        target = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=2) as response:
                    pages = json.loads(response.read())
                target = next((p for p in pages if p.get("type") == "page"), None)
                if target:
                    break
            except Exception:
                time.sleep(0.3)
        if not target:
            print("No Chrome page target")
            return 1

        async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
            counter = [0]
            await cdp(ws, "Runtime.enable", counter=counter)
            await cdp(ws, "Log.enable", counter=counter)
            await cdp(ws, "Page.enable", counter=counter)
            await cdp(ws, "Page.navigate", {"url": APP}, counter=counter)
            await asyncio.sleep(4)

            # Drain whatever arrived while loading.
            try:
                while True:
                    raw = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.4))
                    await print_event(raw)
            except asyncio.TimeoutError:
                pass

            click = await cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": (
                        "(() => { const b = document.querySelector('button[aria-label=\"Tap to speak\"]');"
                        " if (!b) return 'no-button'; b.click(); return 'clicked'; })()"
                    ),
                    "returnByValue": True,
                },
                counter=counter,
            )
            print("click:", click.get("result", {}).get("result", {}).get("value"))

            end = time.time() + 8
            while time.time() < end:
                try:
                    raw = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
                    await print_event(raw)
                except asyncio.TimeoutError:
                    pass

            state = await cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": (
                        "JSON.stringify({text: document.body.innerText.slice(0,900),"
                        " secure: window.isSecureContext,"
                        " media: !!navigator.mediaDevices,"
                        " worklet: !!window.AudioContext && 'audioWorklet' in AudioContext.prototype})"
                    ),
                    "returnByValue": True,
                },
                counter=counter,
            )
            print("state:", state.get("result", {}).get("result", {}).get("value"))
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome.kill()
        shutil.rmtree(profile, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
