"""Run an isolated backend instance for end-to-end scripts.

The e2e scripts save real visits, so pointing them at the demo server would
pollute the curated dataset. This helper starts a throwaway uvicorn process on
a free port with DATABASE_PATH inside a temporary directory, waits for
/api/health, and tears everything down afterwards.

Set ``E2E_URL`` (or pass ``--url`` where supported) to reuse an already-running
server instead; in that case nothing is started or deleted.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_healthy(base_url: str, process: subprocess.Popen, timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    last_error = "no attempt"
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"backend exited early with code {process.returncode}")
        try:
            with urllib.request.urlopen(f"{base_url}/api/health", timeout=1.5) as response:
                if response.status == 200:
                    return
        except Exception as error:  # connection refused while uvicorn boots
            last_error = str(error)
        time.sleep(0.25)
    raise RuntimeError(f"backend did not become healthy: {last_error}")


@contextlib.contextmanager
def isolated_backend() -> Iterator[str]:
    """Yield a websocket base URL backed by a temporary database."""
    override = os.environ.get("E2E_URL", "").strip()
    if override:
        yield override.rstrip("/")
        return

    temp_dir = Path(tempfile.mkdtemp(prefix="asha-e2e-"))
    port = _free_port()
    environment = os.environ.copy()
    environment["DATABASE_PATH"] = str(temp_dir / "asha-e2e.db")
    log_path = temp_dir / "server.log"
    log = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        try:
            _wait_healthy(base_url, process)
        except Exception:
            log.flush()
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
            print("--- isolated backend log ---")
            print(tail)
            print("----------------------------")
            raise
        yield f"ws://127.0.0.1:{port}/ws/visit"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        log.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
