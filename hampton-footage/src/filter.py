"""Step 2: filter data/raw_results.json using config/rules.yaml.

Writes:
  output/shortlist.csv   likely video of the 12/31/96 show, best matches first
  output/audio_only.csv  results that match but look like audio-only uploads
  data/filtered_out.csv  everything dropped, with the reason (for checking the rules)

No API calls are made, so this can be re-run freely after editing rules.yaml.

Usage:
    python src/filter.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

import yaml

from common import AUDIO_ONLY, CONFIG_DIR, DATA_DIR, RAW_RESULTS, SHORTLIST, format_duration, video_url

COLUMNS = ["title", "link", "duration", "upload_date", "why_matched",
           "focus_score", "channel", "video_id", "reuploads"]
AUDIO_COLUMNS = COLUMNS + ["audio_reason"]
FILTERED_OUT = DATA_DIR / "filtered_out.csv"


def phrase_regex(phrase: str) -> re.Pattern:
    """Whole-word, case-insensitive match for a literal phrase."""
    return re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.IGNORECASE)


@dataclass
class Matcher:
    label: str
    pattern: re.Pattern


def build_matchers(words: list[str] | None, patterns: list[str] | None = None) -> list[Matcher]:
    matchers = [Matcher(w, phrase_regex(w)) for w in words or []]
    matchers += [Matcher(p, re.compile(p, re.IGNORECASE)) for p in patterns or []]
    return matchers


@dataclass
class Rules:
    fields: list[str]
    keep: list[Matcher]
    exclude: list[Matcher]
    audio_strong: list[Matcher]
    audio_weak: list[Matcher]
    video_hints: list[Matcher]
    focus: list[Matcher]
    dup_tolerance: int = 2
    dup_similarity: float = 0.6
    dup_long_clip: int = 600

    @classmethod
    def load(cls, path: Path) -> "Rules":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        audio = raw.get("audio_only") or {}
        dedupe = raw.get("dedupe") or {}
        return cls(
            fields=raw.get("fields") or ["title", "description", "tags"],
            keep=build_matchers(raw.get("keep"), raw.get("keep_patterns")),
            exclude=build_matchers(raw.get("exclude"), raw.get("exclude_patterns")),
            audio_strong=build_matchers(audio.get("strong")),
            audio_weak=build_matchers(audio.get("weak")),
            video_hints=build_matchers(audio.get("video_hints")),
            focus=build_matchers(raw.get("focus")),
            dup_tolerance=int(dedupe.get("duration_tolerance_seconds", 2)),
            dup_similarity=float(dedupe.get("title_similarity", 0.6)),
            dup_long_clip=int(dedupe.get("long_clip_seconds", 600)),
        )


def field_texts(record: dict, fields: list[str]) -> dict[str, str]:
    texts = {}
    for name in fields:
        value = record.get(name, "")
        texts[name] = " ".join(value) if isinstance(value, list) else str(value or "")
    return texts


def find_hits(matchers: list[Matcher], texts: dict[str, str]) -> list[str]:
    """Descriptions like "'1996' in title" for every matcher that hits."""
    hits = []
    for m in matchers:
        where = [name for name, text in texts.items() if m.pattern.search(text)]
        if where:
            hits.append(f"'{m.label}' in {'/'.join(where)}")
    return hits


def audio_reason(record: dict, rules: Rules) -> str:
    """Why a record looks audio-only, or '' if it looks like video."""
    if record.get("channel", "").endswith(" - Topic"):
        return "auto-generated '- Topic' music channel"
    texts = field_texts(record, ["title", "description"])
    strong = find_hits(rules.audio_strong, texts)
    if strong:
        return "; ".join(strong)
    weak = find_hits(rules.audio_weak, texts)
    if weak and not find_hits(rules.video_hints, texts):
        return "; ".join(weak) + " (no video words)"
    return ""


def normalise_title(title: str) -> str:
    title = re.sub(r"\b(re-?upload(ed)?|hd|hq|1080p|720p|480p|full|official)\b", " ", title.lower())
    return re.sub(r"[^a-z0-9]+", " ", title).strip()


def is_reupload(a: dict, b: dict, rules: Rules) -> bool:
    da, db = a.get("duration_seconds", 0), b.get("duration_seconds", 0)
    if not da or not db or abs(da - db) > rules.dup_tolerance:
        return False
    if min(da, db) >= rules.dup_long_clip:
        return True
    similarity = SequenceMatcher(None, normalise_title(a["title"]), normalise_title(b["title"])).ratio()
    return similarity >= rules.dup_similarity


def dedupe(records: list[dict], rules: Rules) -> list[dict]:
    """Collapse reuploads, keeping the earliest upload and listing the rest."""
    unique: dict[str, dict] = {}
    for rec in records:  # drop exact repeats of the same video ID first
        unique.setdefault(rec["video_id"], rec)
    ordered = sorted(unique.values(), key=lambda r: r.get("published_at") or "9999")
    kept: list[dict] = []
    for rec in ordered:
        original = next((k for k in kept if is_reupload(k, rec, rules)), None)
        if original is None:
            kept.append({**rec, "reuploads": []})
        else:
            original["reuploads"].append(video_url(rec["video_id"]))
    return kept


def classify(records: list[dict], rules: Rules):
    """Split records into (video, audio_only, rejected); each gets 'why'."""
    video, audio, rejected = [], [], []
    for rec in records:
        texts = field_texts(rec, rules.fields)
        excluded = find_hits(rules.exclude, texts)
        kept = find_hits(rules.keep, texts)
        if excluded:
            rejected.append({**rec, "why": "excluded: " + "; ".join(excluded)})
            continue
        if not kept:
            rejected.append({**rec, "why": "no keep word"})
            continue
        focus = find_hits(rules.focus, field_texts(rec, ["title", "description"]))
        why = "keep: " + "; ".join(kept)
        if focus:
            why += " | focus: " + "; ".join(focus)
        rec = {**rec, "why": why, "focus_score": len(focus)}
        reason = audio_reason(rec, rules)
        if reason:
            audio.append({**rec, "audio_reason": reason})
        else:
            video.append(rec)
    return video, audio, rejected


def to_row(rec: dict) -> dict:
    return {
        "title": rec["title"],
        "link": video_url(rec["video_id"]),
        "duration": format_duration(rec.get("duration_seconds", 0)),
        "upload_date": (rec.get("published_at") or "")[:10],
        "why_matched": rec.get("why", ""),
        "focus_score": rec.get("focus_score", 0),
        "channel": rec.get("channel", ""),
        "video_id": rec["video_id"],
        "reuploads": " ".join(rec.get("reuploads", [])),
        "audio_reason": rec.get("audio_reason", ""),
    }


def write_csv(path: Path, records: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = sorted(records, key=lambda r: (-r.get("focus_score", 0), r.get("published_at") or ""))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(to_row(rec))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=RAW_RESULTS)
    parser.add_argument("--rules", type=Path, default=CONFIG_DIR / "rules.yaml")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"{args.input} not found. Run src/search.py first.", file=sys.stderr)
        return 1
    records = json.loads(args.input.read_text(encoding="utf-8"))
    rules = Rules.load(args.rules)

    video, audio, rejected = classify(records, rules)
    video, audio = dedupe(video, rules), dedupe(audio, rules)

    write_csv(SHORTLIST, video, COLUMNS)
    write_csv(AUDIO_ONLY, audio, AUDIO_COLUMNS)
    write_csv(FILTERED_OUT, rejected, ["title", "link", "why_matched", "channel", "video_id"])
    print(f"{len(records)} results -> {len(video)} on the shortlist, "
          f"{len(audio)} audio-only, {len(rejected)} filtered out.")
    print(f"  {SHORTLIST}\n  {AUDIO_ONLY}\n  {FILTERED_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
