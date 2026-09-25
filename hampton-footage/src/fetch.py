"""Step 3 (server only): download shortlisted clips with yt-dlp.

Reads output/shortlist.csv and saves each video to data/clips/<video_id>.<ext>
plus a <video_id>.info.json with its metadata. Already-downloaded videos are
recorded in data/clips/archive.txt and skipped on later runs.

Needs yt-dlp and ffmpeg (yt-dlp uses ffmpeg to merge video and audio):
    pip install -r requirements-server.txt
    sudo apt install ffmpeg

Usage:
    python src/fetch.py                  # everything on the shortlist
    python src/fetch.py --limit 5        # only the top 5 rows
    python src/fetch.py --ids abc123 def456
    python src/fetch.py --dry-run        # list what would be downloaded
"""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import time
from pathlib import Path

from common import CLIPS_DIR, SHORTLIST, video_url


def yt_dlp_command() -> list[str]:
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        sys.exit("yt-dlp not found. Install it with: pip install -r requirements-server.txt")
    return [sys.executable, "-m", "yt_dlp"]


def read_shortlist(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def download(base_cmd: list[str], video_id: str, max_height: int) -> bool:
    fmt = f"bv*[height<={max_height}]+ba/b[height<={max_height}]/bv*+ba/b"
    cmd = base_cmd + [
        "--format", fmt,
        "--merge-output-format", "mp4",
        "--output", str(CLIPS_DIR / "%(id)s.%(ext)s"),
        "--download-archive", str(CLIPS_DIR / "archive.txt"),
        "--write-info-json",
        "--no-playlist",
        "--no-overwrites",
        "--retries", "5",
        "--fragment-retries", "5",
        video_url(video_id),
    ]
    return subprocess.run(cmd).returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--shortlist", type=Path, default=SHORTLIST)
    parser.add_argument("--limit", type=int, help="only download the first N rows")
    parser.add_argument("--ids", nargs="+", help="only these video IDs")
    parser.add_argument("--max-height", type=int, default=720,
                        help="highest video resolution to fetch; default 720 (old camcorder footage rarely needs more)")
    parser.add_argument("--sleep", type=float, default=5,
                        help="seconds to wait between downloads; default 5")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.shortlist.exists():
        print(f"{args.shortlist} not found. Run src/filter.py first.", file=sys.stderr)
        return 1
    rows = read_shortlist(args.shortlist)
    if args.ids:
        wanted = set(args.ids)
        rows = [r for r in rows if r["video_id"] in wanted]
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        print("Nothing to download.")
        return 0

    if args.dry_run:
        for r in rows:
            print(f"{r['video_id']}  {r['duration']:>8}  {r['title']}")
        return 0

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    base_cmd = yt_dlp_command()
    failed = []
    for i, r in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {r['title']} ({r['duration']})")
        if not download(base_cmd, r["video_id"], args.max_height):
            failed.append(r["video_id"])
        if i < len(rows):
            time.sleep(args.sleep)

    print(f"Done: {len(rows) - len(failed)} ok, {len(failed)} failed. Clips are in {CLIPS_DIR}")
    if failed:
        print("Failed IDs (re-run with --ids to retry): " + " ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
