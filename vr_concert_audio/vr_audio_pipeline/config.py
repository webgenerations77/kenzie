"""Config loading and defaults for the VR concert audio pipeline."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "input_path": "input/song.wav",
    "output_dir": "output",
    "separation": {
        "model": "htdemucs_6s",
        "device": "auto",
        "shifts": 0,
        "segment": None,
        "stem_format": "wav",
    },
    "analysis": {
        "sample_rate": 44100,
        "tightness": 100,
        "min_section_seconds": 8.0,
        "max_sections": None,
    },
    "output": {
        "beat_map_filename": "beat_map.json",
        "markers_filename": "markers.csv",
        "summary_filename": "summary.txt",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@dataclass
class SeparationConfig:
    model: str = "htdemucs_6s"
    device: str = "auto"
    shifts: int = 0
    segment: Optional[float] = None
    stem_format: str = "wav"


@dataclass
class AnalysisConfig:
    sample_rate: int = 44100
    tightness: int = 100
    min_section_seconds: float = 8.0
    max_sections: Optional[int] = None


@dataclass
class OutputConfig:
    beat_map_filename: str = "beat_map.json"
    markers_filename: str = "markers.csv"
    summary_filename: str = "summary.txt"


@dataclass
class PipelineConfig:
    input_path: str
    output_dir: str
    separation: SeparationConfig = field(default_factory=SeparationConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineConfig":
        merged = _deep_merge(DEFAULT_CONFIG, data)
        return cls(
            input_path=merged["input_path"],
            output_dir=merged["output_dir"],
            separation=SeparationConfig(**merged["separation"]),
            analysis=AnalysisConfig(**merged["analysis"]),
            output=OutputConfig(**merged["output"]),
        )

    @classmethod
    def load(cls, path: Optional[str | Path]) -> "PipelineConfig":
        if path is None:
            return cls.from_dict({})
        path = Path(path)
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)

    def apply_overrides(self, **overrides: Any) -> None:
        for key, value in overrides.items():
            if value is None:
                continue
            if key in {"input_path", "output_dir"}:
                setattr(self, key, value)
            elif hasattr(self.separation, key):
                setattr(self.separation, key, value)
            elif hasattr(self.analysis, key):
                setattr(self.analysis, key, value)
