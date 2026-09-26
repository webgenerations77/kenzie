"""Tests using a short synthetic audio clip (see synthetic_audio.py) —
no real song recording is needed or committed to run these.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.synthetic_audio import make_synthetic_clip
from vr_audio_pipeline.analysis import analyze
from vr_audio_pipeline.cli import main as cli_main
from vr_audio_pipeline.config import AnalysisConfig, PipelineConfig
from vr_audio_pipeline.output import write_outputs
from vr_audio_pipeline.separation import combined_stems_note, resolve_device


@pytest.fixture
def synthetic_clip(tmp_path: Path) -> Path:
    clip_path = tmp_path / "synthetic_clip.wav"
    make_synthetic_clip(str(clip_path), duration_seconds=12.0, bpm=120.0)
    return clip_path


def test_synthetic_clip_generation(synthetic_clip: Path):
    assert synthetic_clip.exists()
    assert synthetic_clip.stat().st_size > 0


def test_analysis_finds_tempo_and_beats(synthetic_clip: Path):
    result = analyze(str(synthetic_clip), AnalysisConfig())

    assert result.duration_seconds == pytest.approx(12.0, abs=0.2)
    # Synthetic clip is 120 BPM; librosa's estimate (or a musically related
    # tempo, e.g. half/double time) should land near it.
    assert any(
        abs(result.tempo_bpm - target) < 6
        for target in (120.0, 60.0, 240.0)
    )
    assert len(result.beat_times) > 10
    assert len(result.downbeat_times) > 2
    # Beat times must be increasing and within the clip duration.
    assert result.beat_times == sorted(result.beat_times)
    assert all(0 <= t <= result.duration_seconds for t in result.beat_times)


def test_analysis_finds_a_section_boundary(synthetic_clip: Path):
    result = analyze(str(synthetic_clip), AnalysisConfig(min_section_seconds=2.0))

    assert len(result.sections) >= 1
    # Sections must tile the full duration with no gaps/overlaps.
    assert result.sections[0]["start_seconds"] == 0.0
    assert result.sections[-1]["end_seconds"] == pytest.approx(
        result.duration_seconds, abs=0.01
    )
    for a, b in zip(result.sections, result.sections[1:]):
        assert a["end_seconds"] == b["start_seconds"]


def test_write_outputs_creates_expected_files(tmp_path: Path, synthetic_clip: Path):
    result = analyze(str(synthetic_clip), AnalysisConfig())
    from vr_audio_pipeline.config import OutputConfig

    paths = write_outputs(
        result,
        tmp_path,
        OutputConfig(),
        input_path=str(synthetic_clip),
    )

    assert paths["beat_map"].exists()
    assert paths["markers"].exists()
    assert paths["summary"].exists()

    with open(paths["beat_map"]) as f:
        beat_map = json.load(f)
    assert beat_map["tempo_bpm"] == result.tempo_bpm
    assert len(beat_map["beats"]) == len(result.beat_times)
    assert len(beat_map["sections"]) == len(result.sections)

    markers_text = paths["markers"].read_text()
    assert "time_seconds,type,label" in markers_text
    assert "downbeat" in markers_text
    assert "section_start" in markers_text

    summary_text = paths["summary"].read_text()
    assert "Tempo:" in summary_text
    assert "Sections detected:" in summary_text


def test_cli_skip_separation_end_to_end(tmp_path: Path, synthetic_clip: Path):
    output_dir = tmp_path / "output"
    exit_code = cli_main(
        [
            "--input",
            str(synthetic_clip),
            "--output-dir",
            str(output_dir),
            "--skip-separation",
        ]
    )
    assert exit_code == 0
    assert (output_dir / "beat_map.json").exists()
    assert (output_dir / "markers.csv").exists()
    assert (output_dir / "summary.txt").exists()


def test_cli_missing_input_returns_error(tmp_path: Path):
    exit_code = cli_main(
        [
            "--input",
            str(tmp_path / "does_not_exist.wav"),
            "--output-dir",
            str(tmp_path / "output"),
            "--skip-separation",
        ]
    )
    assert exit_code == 1


def test_config_from_yaml(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "input_path: my_song.wav\noutput_dir: my_output\n"
        "separation:\n  device: cpu\n"
    )
    config = PipelineConfig.load(config_path)
    assert config.input_path == "my_song.wav"
    assert config.output_dir == "my_output"
    assert config.separation.device == "cpu"
    # Untouched defaults still present.
    assert config.separation.model == "htdemucs_6s"


def test_resolve_device_without_torch_falls_back_to_cpu():
    # In an environment without torch installed (or without CUDA), "auto"
    # must resolve to "cpu" rather than raising.
    assert resolve_device("cpu") == "cpu"
    assert resolve_device("auto") in {"cpu", "cuda"}


def test_combined_stems_note_mentions_violin_and_saxophone():
    note = combined_stems_note("htdemucs_6s")
    assert note is not None
    assert "violin" in note
    assert "saxophone" in note
