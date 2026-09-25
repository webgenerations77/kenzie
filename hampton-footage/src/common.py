"""Shared paths and small helpers used by every step."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLIPS_DIR = DATA_DIR / "clips"
FRAMES_DIR = DATA_DIR / "frames"
OUTPUT_DIR = ROOT / "output"
CONTACT_SHEETS_DIR = OUTPUT_DIR / "contact_sheets"

RAW_RESULTS = DATA_DIR / "raw_results.json"
SHORTLIST = OUTPUT_DIR / "shortlist.csv"
AUDIO_ONLY = OUTPUT_DIR / "audio_only.csv"

_DURATION_RE = re.compile(
    r"^P(?:(?P<d>\d+)D)?(?:T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?)?$"
)


def load_env(path: Path = ROOT / ".env") -> None:
    """Load KEY=VALUE lines from .env into os.environ (existing vars win)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def read_lines(path: Path) -> list[str]:
    """Non-blank, non-comment lines of a text file."""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def parse_iso_duration(value: str | None) -> int:
    """YouTube's ISO 8601 duration (e.g. PT1H2M3S) to seconds; 0 if unknown."""
    match = _DURATION_RE.match(value or "")
    if not match:
        return 0
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    return parts["d"] * 86400 + parts["h"] * 3600 + parts["m"] * 60 + parts["s"]


def format_duration(seconds: int) -> str:
    """Seconds to H:MM:SS (or M:SS under an hour)."""
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "query"
