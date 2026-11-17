"""End-to-end UI smoke test against the production build.

Drives headless Chrome over CDP (no Playwright dependency), using the fake
microphone so the real streaming path can be started. Every assertion is
printed as PASS/FAIL; the process exits non-zero if any fail.

Usage (from backend/, with the server running on 127.0.0.1:8000):
    python tools/smoke_ui.py
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from datetime import date, timedelta

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = "http://127.0.0.1:8000/"
PORT = 9223

HELPERS = r"""
window.__t = {
  text: () => document.body.innerText,
  button: (needle, scope) => {
    const root = scope ? document.querySelector(scope) : document;
    if (!root) return null;
    return [...root.querySelectorAll('button')].find((b) => {
      const label = (b.innerText || '') + ' ' + (b.getAttribute('aria-label') || '');
      return label.includes(needle);
    }) || null;
  },
  click: (needle, scope) => {
    const el = window.__t.button(needle, scope);
    if (!el) return 'missing:' + needle;
    el.click();
    return 'ok';
  },
  setInput: (selector, value, index) => {
    const el = document.querySelectorAll(selector)[index || 0];
    if (!el) return 'missing:' + selector;
    const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype
      : el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
    el.dispatchEvent(new Event(el.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
    return 'ok';
  },
  setField: (labelText, value) => {
    const label = [...document.querySelectorAll('label')].find((item) =>
      (item.innerText || '').toUpperCase().includes(labelText.toUpperCase()));
    if (!label) return 'missing-label:' + labelText;
    const el = label.querySelector('input, select, textarea');
    if (!el) return 'missing-input:' + labelText;
    const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype
      : el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
    el.dispatchEvent(new Event(el.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
    return 'ok';
  },
  visible: (selector) => {
    const el = document.querySelector(selector);
    return !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  },
  resultCount: () => {
    const line = [...document.querySelectorAll('p')].find((p) => /^\d+ visits?$/.test((p.innerText || '').trim()));
    return line ? line.innerText.trim() : '';
  },
};
'ready'
"""


class UI:
    def __init__(self, ws, counter):
        self.ws = ws
        self.counter = counter
        self.exceptions: list[str] = []
        self.checks: list[tuple[str, bool, str]] = []

    async def call(self, method: str, params: dict | None = None) -> dict:
        self.counter[0] += 1
        await self.ws.send(json.dumps({"id": self.counter[0], "method": method, "params": params or {}}))
        while True:
            raw = json.loads(await self.ws.recv())
            if raw.get("id") == self.counter[0]:
                if "error" in raw:
                    raise RuntimeError(f"{method}: {raw['error']}")
                return raw.get("result", {})
            self._event(raw)

    def _event(self, raw: dict) -> None:
        if raw.get("method") == "Runtime.exceptionThrown":
            detail = raw.get("params", {}).get("exceptionDetails", {})
            text = detail.get("exception", {}).get("description") or detail.get("text") or "exception"
            self.exceptions.append(str(text))

    async def eval(self, expression: str):
        result = await self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        if result.get("exceptionDetails"):
            detail = result["exceptionDetails"]
            raise RuntimeError(detail.get("exception", {}).get("description") or detail.get("text"))
        return result.get("result", {}).get("value")

    async def load(self, url: str | None = None, wait: float = 3.0) -> None:
        if url:
            await self.call("Page.navigate", {"url": url})
        else:
            await self.call("Page.reload")
        await asyncio.sleep(wait)
        await self.eval(HELPERS)

    def check(self, name: str, ok: bool, detail: object = "") -> None:
        self.checks.append((name, bool(ok), str(detail)[:300]))
        print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}" if detail and not ok else ""))

    async def click(self, needle: str, scope: str = "") -> bool:
        result = await self.eval(f"__t.click({json.dumps(needle)}, {json.dumps(scope)})")
        return result == "ok"

    async def set_field(self, label: str, value: str) -> bool:
        result = await self.eval(f"__t.setField({json.dumps(label)}, {json.dumps(value)})")
        return result == "ok"

    async def set_input(self, selector: str, value: str, index: int = 0) -> bool:
        result = await self.eval(f"__t.setInput({json.dumps(selector)}, {json.dumps(value)}, {index})")
        return result == "ok"

    def report(self) -> int:
        failed = [item for item in self.checks if not item[1]]
        print(f"\n{len(self.checks) - len(failed)}/{len(self.checks)} checks passed")
        if self.exceptions:
            print(f"{len(self.exceptions)} uncaught JS exception(s):")
            for item in self.exceptions[:5]:
                print("  -", item.splitlines()[0][:200])
        return 0 if not failed and not self.exceptions else 1


async def main() -> int:
    profile = tempfile.mkdtemp(prefix="asha-smoke-")
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
                target = next((page for page in pages if page.get("type") == "page"), None)
                if target:
                    break
            except Exception:
                await asyncio.sleep(0.3)
        if not target:
            print("No Chrome page target")
            return 1

        async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
            ui = UI(ws, [0])
            await ui.call("Runtime.enable")
            await ui.call("Log.enable")
            await ui.call("Page.enable")
            await ui.call(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
            )
            await ui.load(APP)

            text = await ui.eval("__t.text()")
            ui.check("desktop greeting shows worker name", "Sunita" in text, text[:160])
            ui.check("desktop header shows village", "Rampur" in text)
            ui.check(
                "desktop header shows date",
                date.today().strftime("%B") in text and str(date.today().year) in text,
            )
            main_width = await ui.eval("Math.round(document.querySelector('main').getBoundingClientRect().width)")
            ui.check("desktop uses available width", isinstance(main_width, (int, float)) and main_width >= 1100, main_width)
            ui.check("desktop sidebar visible", await ui.eval("__t.visible('aside')"))
            ui.check("desktop bottom nav hidden", not await ui.eval("__t.visible('nav.fixed')"))
            ui.check("recent visits rendered with real name", "Baby of Meena" in text)
            ui.check("no anonymous beneficiary label", "Beneficiary · name not recorded" not in text)

            # ---------------------------------------------------------- new visit
            ui.check("header + opens the new-visit dialog", await ui.click("New visit"))
            await asyncio.sleep(0.6)
            dialog = await ui.eval("document.querySelector('[role=dialog]')?.innerText || ''")
            ui.check("dialog offers voice and manual", "Start voice visit" in dialog and "Enter manually" in dialog, dialog[:120])
            ui.check("dialog manual button works", await ui.click("Enter manually", "[role=dialog]"))
            await asyncio.sleep(0.7)
            text = await ui.eval("__t.text()")
            ui.check("manual form opened", "Enter a visit manually" in text)

            future = (date.today() + timedelta(days=15)).isoformat()
            for label, value in (
                ("Patient / newborn name", "Test Beneficiary"),
                ("Beneficiary ID", "ASHA999"),
                ("Visit type", "general"),
                ("Weight (kg)", "60.5"),
                ("Next visit date", future),
                ("Observations", "No danger signs. Routine follow-up. Smoke test record."),
            ):
                ok = await ui.set_field(label, value)
                ui.check(f"manual field set: {label}", ok)
            await asyncio.sleep(0.3)
            ui.check("manual save clicked", await ui.click("Save visit record"))
            await asyncio.sleep(3.0)
            text = await ui.eval("__t.text()")
            ui.check("manual save reaches saved screen", "Record saved" in text, text[:200])
            ui.check("manual save shows confirmation toast", "Visit saved and follow-ups created." in text)

            # ---------------------------------------------------------- saved view
            ui.check("saved screen links to detail", await ui.click("Visit details"))
            await asyncio.sleep(1.4)
            text = await ui.eval("__t.text()")
            ui.check("visit detail opens", "Test Beneficiary" in text and "Edit record" in text, text[:200])
            ui.check("edit mode opens", await ui.click("Edit record"))
            await asyncio.sleep(0.6)
            ui.check("edit weight field set", await ui.set_field("Weight (kg)", "61.2"))
            ui.check("save changes clicked", await ui.click("Save changes"))
            await asyncio.sleep(2.5)
            text = await ui.eval("__t.text()")
            ui.check("edit persists weight", "61.2 kg" in text, text[:220])
            ui.check("edit confirmation toast", "Visit record updated." in text)
            ui.check("back returns to the saved record", await ui.click("Back"))
            await asyncio.sleep(0.8)
            ui.check("saved record is restored", "Record saved" in await ui.eval("__t.text()"))
            ui.check("start another visit from saved screen", await ui.click("New visit", "main"))
            await asyncio.sleep(0.8)
            ui.check("sidebar History opens", await ui.click("History"))
            await asyncio.sleep(0.8)

            # ------------------------------------------------------------- history
            awaited = await ui.set_input('input[placeholder^="Search by name"]', "Test")
            ui.check("history search accepts input", awaited)
            await asyncio.sleep(0.6)
            count = await ui.eval("__t.resultCount()")
            ui.check("history search narrows to one visit", count == "1 visit", count)
            ui.check("search result is clickable", await ui.click("Test Beneficiary"))
            await asyncio.sleep(1.3)
            ui.check("search result opens its detail", "Edit record" in await ui.eval("__t.text()"))
            ui.check("back from searched detail", await ui.click("Back"))
            await asyncio.sleep(0.8)

            # filters (returning from detail resets the search field)
            ui.check("beneficiary lookup select set", await ui.set_input("select", "ASHA102", 0))
            await asyncio.sleep(0.6)
            count = await ui.eval("__t.resultCount()")
            ui.check("beneficiary lookup narrows to Lakshmi", count == "1 visit", count)
            ui.check("clear lookup", await ui.click("Clear filters"))
            await asyncio.sleep(0.5)
            ui.check("visit-type filter set", await ui.set_input("select", "newborn_hbnc", 1))
            await asyncio.sleep(0.6)
            count = await ui.eval("__t.resultCount()")
            ui.check("visit-type filter narrows to newborn", count == "1 visit", count)
            ui.check("clear type filter", await ui.click("Clear filters"))
            await asyncio.sleep(0.5)
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            ui.check("date-from filter set", await ui.set_input("input[type=date]", tomorrow, 0))
            await asyncio.sleep(0.6)
            count = await ui.eval("__t.resultCount()")
            ui.check("date range excludes today's visits", count == "0 visits", count)
            ui.check("empty filter state explains itself", "No visits match these filters." in await ui.eval("__t.text()"))
            ui.check("clear date filter", await ui.click("Clear filters"))
            await asyncio.sleep(0.5)

            # ------------------------------------------------------------ language
            ui.check("home tab before language switch", await ui.click("Home"))
            await asyncio.sleep(0.6)
            ui.check("switch to Tamil", await ui.click("தமிழ்"))
            await asyncio.sleep(1.0)
            text = await ui.eval("__t.text()")
            ui.check("Tamil greeting rendered", "வணக்கம்" in text)
            ui.check("Tamil dashboard labels rendered", "இன்றைய வருகைகள்" in text and "சமீபத்திய வருகைகள்" in text)
            ui.check("English dashboard label removed", "RECENT VISITS" not in text)
            ui.check("Tamil follow-up label rendered", "தொடர் பணிகள்" in text)
            await ui.load(wait=3.5)
            text = await ui.eval("__t.text()")
            ui.check("language persists across reload", "இன்றைய வருகைகள்" in text and "வணக்கம்" in text)

            # danger banner in Tamil
            ui.check("open newborn visit while Tamil", await ui.click("Baby of Meena"))
            await asyncio.sleep(1.4)
            text = await ui.eval("__t.text()")
            ui.check(
                "danger banner is localised",
                "ஆபத்து அறிகுறி" in text and "குறைந்த பிறப்பு எடை" in text,
                text[:220],
            )
            ui.check("detail back after Tamil", await ui.click("பின்செல்"))
            await asyncio.sleep(0.7)
            tamil_text = (await ui.eval("__t.text()")).lower()
            english_ui = (
                "view all", "recent visits", "new visit", "follow-ups", "mark done",
                "enter manually", "search by name", "clear filters", "all patients",
                "all visit types", "date from", "date to",
            )
            leaks = [phrase for phrase in english_ui if phrase in tamil_text]
            ui.check("no English UI phrases in Tamil view", not leaks, leaks)
            ui.check(
                "follow-up titles translated in Tamil",
                "urgent: refer to phc today" not in tamil_text and "next anc checkup" not in tamil_text,
            )

            # Hindi pass over the same screens
            ui.check("switch to Hindi", await ui.click("हिन्दी"))
            await asyncio.sleep(1.0)
            hindi_text = await ui.eval("__t.text()")
            ui.check(
                "Hindi dashboard labels rendered",
                "आज की विज़िट" in hindi_text and "हाल की विज़िट" in hindi_text,
                hindi_text[:160],
            )
            hindi_lower = hindi_text.lower()
            leaks = [phrase for phrase in english_ui if phrase in hindi_lower]
            ui.check("no English UI phrases in Hindi view", not leaks, leaks)
            ui.check(
                "follow-up titles translated in Hindi",
                "urgent: refer to phc today" not in hindi_lower and "next anc checkup" not in hindi_lower,
            )

            ui.check("switch back to English", await ui.click("English"))
            await asyncio.sleep(0.8)
            ui.check("English restored", "RECENT VISITS" in await ui.eval("__t.text()"))

            # danger detail in English
            ui.check("open newborn visit from recent list", await ui.click("Baby of Meena"))
            await asyncio.sleep(1.4)
            text = await ui.eval("__t.text()")
            ui.check("danger banner shown in detail", "Danger sign detected" in text and "Low birth weight" in text, text[:220])
            ui.check("detail back works", await ui.click("Back"))
            await asyncio.sleep(0.7)

            # ---------------------------------------------------------- mark done
            ui.check("open follow-ups", await ui.click("Follow-ups"))
            await asyncio.sleep(0.7)
            follow_text = await ui.eval("__t.text()")
            ui.check("follow-up groups visible", "Urgent" in follow_text)
            positions = [
                follow_text.find(label)
                for label in ("Urgent", "Overdue", "Today", "Next 7 days", "Later")
                if follow_text.find(label) != -1
            ]
            ui.check("follow-up groups in priority order", positions == sorted(positions), positions)
            urgent_at = follow_text.find("URGENT: Refer to PHC today")
            next_at = follow_text.find("Next ANC checkup")
            ui.check("urgent referral before routine tasks", 0 <= urgent_at < next_at, (urgent_at, next_at))
            ui.check("no stale 2027 tasks in demo", "2027" not in follow_text)
            ui.check("mark done starts confirmation", await ui.click("Mark done"))
            await asyncio.sleep(0.5)
            dialog = await ui.eval("document.querySelector('[role=dialog]')?.innerText || ''")
            ui.check("mark-done asks for confirmation", "Mark this task done?" in dialog and "Yes, mark done" in dialog, dialog[:150])
            ui.check("confirm mark done", await ui.click("Yes, mark done", "[role=dialog]"))
            await asyncio.sleep(1.4)
            text = await ui.eval("__t.text()")
            ui.check("done toast offers undo", "Task marked done." in text and "Undo" in text, text[-300:])
            ui.check("undo restores task", await ui.click("Undo"))
            await asyncio.sleep(1.6)
            ui.check("restore toast shown", "Task restored." in await ui.eval("__t.text()"))

            # --------------------------------------------------------------- voice
            ui.check("home tab opens", await ui.click("Home"))
            await asyncio.sleep(0.7)
            ui.check("microphone recording starts", await ui.click("Tap to speak"))
            await asyncio.sleep(4.0)
            text = await ui.eval("__t.text()")
            ui.check(
                "recording screen is listening",
                "Listening…" in text or "Tap to stop" in text,
                text[:220],
            )

            # Feed the same pipeline deterministically, so stop always has text
            # even when the fake microphone produces silence.
            await ui.eval("document.querySelector('details')?.setAttribute('open', '')")
            await asyncio.sleep(0.3)
            ui.check(
                "typed fallback input available",
                await ui.set_input('input[placeholder^="Lakshmi"]', "Lakshmi, beneficiary ID ASHA102. Pregnancy visit. Weight 55 kilo. ANC completed. Next visit in three days."),
            )
            ui.check("typed fallback sends text", await ui.click("Send"))
            await asyncio.sleep(1.5)
            ui.check("recording can be stopped", await ui.click("Tap to stop"))
            await asyncio.sleep(2.5)
            text = await ui.eval("__t.text()")
            ui.check(
                "stop leaves the recording state",
                "Building the record…" in text or "Confirm & save" in text or "Record saved" in text,
                text[:220],
            )
            if "Cancel" in text:
                await ui.click("Cancel")
                await asyncio.sleep(1.0)
            else:
                await ui.load(wait=3.0)

            # -------------------------------------------------------------- mobile
            await ui.call(
                "Emulation.setDeviceMetricsOverride",
                {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
            )
            await ui.load(wait=3.5)
            text = await ui.eval("__t.text()")
            ui.check("mobile sidebar hidden", not await ui.eval("__t.visible('aside')"))
            ui.check("mobile bottom nav visible", await ui.eval("__t.visible('nav.fixed')"))
            ui.check("mobile header keeps worker identity", "Sunita" in text and "Rampur" in text)
            overflow = await ui.eval("document.documentElement.scrollWidth - window.innerWidth")
            ui.check("mobile has no horizontal overflow", overflow <= 1, overflow)

            return ui.report()
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
