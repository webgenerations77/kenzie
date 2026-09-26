"""Write beat_map.json, markers.csv, and a plain-text summary."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from .analysis import AnalysisResult
from .config import OutputConfig


def write_outputs(
    result: AnalysisResult,
    output_dir: str | Path,
    config: OutputConfig,
    input_path: str,
    stem_paths: Optional[dict[str, Path]] = None,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    beat_map_path = output_dir / config.beat_map_filename
    markers_path = output_dir / config.markers_filename
    summary_path = output_dir / config.summary_filename

    _write_beat_map(beat_map_path, result, input_path, stem_paths)
    _write_markers(markers_path, result)
    _write_summary(summary_path, result, input_path, stem_paths)

    return {
        "beat_map": beat_map_path,
        "markers": markers_path,
        "summary": summary_path,
    }


def _write_beat_map(
    path: Path,
    result: AnalysisResult,
    input_path: str,
    stem_paths: Optional[dict[str, Path]],
) -> None:
    data = {
        "input_path": input_path,
        "duration_seconds": result.duration_seconds,
        "tempo_bpm": result.tempo_bpm,
        "beats_per_bar": result.beats_per_bar,
        "beats": [
            {"time_seconds": t, "index": i}
            for i, t in enumerate(result.beat_times)
        ],
        "downbeats": [
            {"time_seconds": t, "bar_index": i}
            for i, t in enumerate(result.downbeat_times)
        ],
        "sections": result.sections,
    }
    if stem_paths is not None:
        data["stems"] = {name: str(p) for name, p in stem_paths.items()}

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _write_markers(path: Path, result: AnalysisResult) -> None:
    rows: list[tuple[float, str, str]] = []
    for i, t in enumerate(result.downbeat_times):
        rows.append((t, "downbeat", f"bar_{i + 1}"))
    for section in result.sections:
        rows.append(
            (section["start_seconds"], "section_start", section["label"])
        )
    rows.sort(key=lambda r: r[0])

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_seconds", "type", "label"])
        for time_seconds, marker_type, label in rows:
            writer.writerow([f"{time_seconds:.4f}", marker_type, label])


def _write_summary(
    path: Path,
    result: AnalysisResult,
    input_path: str,
    stem_paths: Optional[dict[str, Path]],
) -> None:
    lines = [
        f"Source: {input_path}",
        f"Duration: {result.duration_seconds:.2f}s",
        f"Tempo: {result.tempo_bpm} BPM",
        f"Beats detected: {len(result.beat_times)}",
        f"Downbeats detected: {len(result.downbeat_times)} "
        f"(assumed {result.beats_per_bar}/4 time)",
        f"Sections detected: {len(result.sections)}",
    ]
    for section in result.sections:
        lines.append(
            f"  - {section['label']}: "
            f"{section['start_seconds']:.2f}s - {section['end_seconds']:.2f}s"
        )
    if stem_paths is not None:
        lines.append("Stems:")
        for name, p in stem_paths.items():
            lines.append(f"  - {name}: {p}")

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
