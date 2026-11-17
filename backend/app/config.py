"""Runtime configuration, loaded from backend/.env (no external dependency)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader. Existing environment variables win."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    gnani_api_key: str
    gnani_stt_model: str
    gnani_tts_model: str
    gnani_tts_voice: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    database_path: Path
    frontend_origin: str

    @property
    def gnani_ready(self) -> bool:
        return bool(self.gnani_api_key)

    @property
    def llm_ready(self) -> bool:
        return bool(self.llm_api_key and self.llm_model and self.llm_base_url)


def _resolve_database_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = (BACKEND_DIR / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_dotenv(BACKEND_DIR / ".env")
    return Settings(
        gnani_api_key=os.environ.get("GNANI_API_KEY", ""),
        gnani_stt_model=os.environ.get("GNANI_STT_MODEL", "prisma-v3.0"),
        gnani_tts_model=os.environ.get("GNANI_TTS_MODEL", "timbre-v3.0"),
        gnani_tts_voice=os.environ.get("GNANI_TTS_VOICE", "Shivani"),
        llm_base_url=os.environ.get("LLM_BASE_URL", "").rstrip("/"),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_model=os.environ.get("LLM_MODEL", ""),
        database_path=_resolve_database_path(os.environ.get("DATABASE_PATH", "./data/asha.db")),
        frontend_origin=os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173"),
    )
