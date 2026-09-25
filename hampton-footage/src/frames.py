"""Step 4 (server only): grab a frame every 3 seconds and build contact sheets.

For every clip in data/clips/ this:
  1. runs ffmpeg to save one small frame every 3 seconds to data/frames/<video_id>/
  2. tiles those frames into one image per clip, output/contact_sheets/<video_id>.jpg,
     with the clip's timestamp printed under each frame so you can jump straight
     to the midnight countdown or Tripping Billies.

Needs ffmpeg and Pillow:
    pip install -r requirements-server.txt
    sudo apt install ffmpeg

Usage:
    python src/frames.py                 # all downloaded clips
    python src/frames.py --ids abc123    # just one
    python src/frames.py --force         # redo frames that already exist
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from common import CLIPS_DIR, CONTACT_SHEETS_DIR, FRAMES_DIR, format_duration

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".flv"}
JPEG_MAX_SIDE = 65_000  # JPEG cannot exceed 65,535 px on a side


def find_clips(ids: list[str] | None) -> list[Path]:
    clips = sorted(p for p in CLIPS_DIR.glob("*") if p.suffix.lower() in VIDEO_EXTS)
    if ids:
        clips = [p for p in clips if p.stem in set(ids)]
    return clips


def clip_title(clip: Path) -> str:
    info = clip.with_suffix(".info.json")
    if info.exists():
        try:
            return json.loads(info.read_text(encoding="utf-8")).get("title") or clip.stem
        except ValueError:
            pass
    return clip.stem


def extract_frames(clip: Path, out_dir: Path, interval: float, width: int, force: bool) -> list[Path]:
    existing = sorted(out_dir.glob("frame_*.jpg"))
    if existing and not force:
        print(f"  frames already extracted ({len(existing)}), skipping ffmpeg")
        return existing
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-i", str(clip),
        "-vf", f"fps=1/{interval},scale={width}:-2",
        "-q:v", "4",
        str(out_dir / "frame_%05d.jpg"),
    ]
    subprocess.run(cmd, check=True)
    return sorted(out_dir.glob("frame_*.jpg"))


def build_contact_sheet(frames: list[Path], title: str, interval: float, columns: int, dest: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.load_default()
    with Image.open(frames[0]) as first:
        thumb_w, thumb_h = first.size
    label_h, pad, header_h = 14, 4, 28
    cols = min(columns, len(frames))
    rows = -(-len(frames) // cols)
    cell_w, cell_h = thumb_w + pad, thumb_h + label_h + pad

    # Very long clips: shrink thumbnails so the sheet stays a valid JPEG.
    scale = min(1.0, (JPEG_MAX_SIDE - header_h - pad) / (rows * cell_h))
    if scale < 1.0:
        thumb_w, thumb_h = max(16, int(thumb_w * scale)), max(9, int(thumb_h * scale))
        cell_w, cell_h = thumb_w + pad, thumb_h + label_h + pad

    sheet = Image.new("RGB", (cols * cell_w + pad, header_h + rows * cell_h + pad), "black")
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 8), f"{title}  -  one frame every {interval:g}s, {len(frames)} frames", fill="white", font=font)

    for i, frame in enumerate(frames):
        x = pad + (i % cols) * cell_w
        y = header_h + (i // cols) * cell_h
        with Image.open(frame) as im:
            if im.size != (thumb_w, thumb_h):
                im = im.resize((thumb_w, thumb_h))
            sheet.paste(im.convert("RGB"), (x, y))
        # ffmpeg's fps filter emits frame N (from 0) at about N * interval seconds.
        draw.text((x + 2, y + thumb_h + 1), format_duration(int(i * interval)), fill="yellow", font=font)

    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, "JPEG", quality=85)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ids", nargs="+", help="only these video IDs")
    parser.add_argument("--interval", type=float, default=3, help="seconds between frames; default 3")
    parser.add_argument("--width", type=int, default=240, help="frame width in pixels; default 240")
    parser.add_argument("--columns", type=int, default=10, help="frames per row on the sheet; default 10")
    parser.add_argument("--force", action="store_true", help="re-extract frames even if present")
    args = parser.parse_args(argv)

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install it with: sudo apt install ffmpeg")
    clips = find_clips(args.ids)
    if not clips:
        print(f"No clips in {CLIPS_DIR}. Run src/fetch.py first.")
        return 0

    failed = []
    for i, clip in enumerate(clips, 1):
        print(f"[{i}/{len(clips)}] {clip.name}")
        try:
            frames = extract_frames(clip, FRAMES_DIR / clip.stem, args.interval, args.width, args.force)
            if not frames:
                raise RuntimeError("ffmpeg produced no frames")
            dest = CONTACT_SHEETS_DIR / f"{clip.stem}.jpg"
            build_contact_sheet(frames, clip_title(clip), args.interval, args.columns, dest)
            print(f"  {len(frames)} frames -> {dest}")
        except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
            print(f"  failed: {exc}", file=sys.stderr)
            failed.append(clip.stem)

    if failed:
        print("Failed: " + " ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
