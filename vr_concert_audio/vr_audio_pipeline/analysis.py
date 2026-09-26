"""Full-mix musical analysis with librosa: tempo, beat grid, downbeats,
and section-boundary estimation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import librosa
import numpy as np

from .config import AnalysisConfig


@dataclass
class AnalysisResult:
    duration_seconds: float
    tempo_bpm: float
    beat_times: list[float]
    downbeat_times: list[float]
    beats_per_bar: int
    sections: list[dict] = field(default_factory=list)


def analyze(path: str, config: AnalysisConfig) -> AnalysisResult:
    y, sr = librosa.load(path, sr=config.sample_rate, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    tempo, beat_frames = librosa.beat.beat_track(
        y=y, sr=sr, tightness=config.tightness, units="frames"
    )
    tempo = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    downbeat_times, beats_per_bar = _estimate_downbeats(y, sr, beat_times)

    sections = _estimate_sections(
        y,
        sr,
        duration=duration,
        min_section_seconds=config.min_section_seconds,
        max_sections=config.max_sections,
    )

    return AnalysisResult(
        duration_seconds=float(duration),
        tempo_bpm=round(tempo, 2),
        beat_times=[round(t, 4) for t in beat_times],
        downbeat_times=[round(t, 4) for t in downbeat_times],
        beats_per_bar=beats_per_bar,
        sections=sections,
    )


def _estimate_downbeats(
    y: np.ndarray, sr: int, beat_times: list[float]
) -> tuple[list[float], int]:
    """Approximate downbeats by picking the beat-grid phase (assuming 4/4,
    the common case for concert recordings) whose beats land on the
    strongest low-frequency onset energy on average.

    This is a lightweight heuristic, not a dedicated downbeat tracker
    (e.g. madmom's DBNDownBeatTrackingProcessor) — see README for a note
    on swapping in a more accurate model if precise downbeats matter.
    """
    beats_per_bar = 4
    if len(beat_times) < beats_per_bar:
        return list(beat_times), beats_per_bar

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    onset_times = librosa.times_like(onset_env, sr=sr)

    def strength_at(t: float) -> float:
        idx = int(np.searchsorted(onset_times, t))
        idx = min(max(idx, 0), len(onset_env) - 1)
        return float(onset_env[idx])

    best_phase, best_score = 0, -np.inf
    for phase in range(beats_per_bar):
        candidates = beat_times[phase::beats_per_bar]
        if not candidates:
            continue
        score = float(np.mean([strength_at(t) for t in candidates]))
        if score > best_score:
            best_score, best_phase = score, phase

    downbeats = beat_times[best_phase::beats_per_bar]
    return downbeats, beats_per_bar


def _estimate_sections(
    y: np.ndarray,
    sr: int,
    duration: float,
    min_section_seconds: float,
    max_sections: Optional[int],
) -> list[dict]:
    """Estimate likely section boundaries (verse/chorus/solo changes) via
    novelty detection on a self-similarity matrix of timbre + harmony
    features. This is an unsupervised approximation, not genre-aware
    structural labeling: boundaries are real change points, but the
    verse/chorus/solo *names* are placeholders for a human to relabel.
    """
    hop_length = 512
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    features = np.vstack([mfcc, chroma])
    features = librosa.util.normalize(features, axis=1)

    frame_times = librosa.frames_to_time(
        np.arange(features.shape[1]), sr=sr, hop_length=hop_length
    )

    min_frames = max(
        1, int(min_section_seconds * sr / hop_length)
    )
    if features.shape[1] <= min_frames * 2:
        # Too short to segment meaningfully; treat the whole clip as one section.
        return [
            {
                "label": "section_1",
                "start_seconds": 0.0,
                "end_seconds": round(float(duration), 3),
            }
        ]

    rec = librosa.segment.recurrence_matrix(
        features, mode="affinity", sym=True, k=min(features.shape[1] - 1, 10)
    )
    novelty = _novelty_curve(rec)

    boundary_frames = librosa.util.peak_pick(
        novelty,
        pre_max=min_frames,
        post_max=min_frames,
        pre_avg=min_frames,
        post_avg=min_frames,
        delta=0.05,
        wait=min_frames,
    )

    boundary_times = [0.0] + [
        float(frame_times[f]) for f in boundary_frames
    ] + [float(duration)]
    boundary_times = sorted(set(round(t, 3) for t in boundary_times))

    if max_sections is not None and len(boundary_times) - 1 > max_sections:
        # Keep the strongest boundaries by novelty score.
        scored = sorted(
            boundary_frames, key=lambda f: novelty[f], reverse=True
        )[: max(max_sections - 1, 0)]
        boundary_times = sorted(
            {0.0, float(duration)}
            | {round(float(frame_times[f]), 3) for f in scored}
        )

    labels = _label_sections(len(boundary_times) - 1)
    sections = []
    for i in range(len(boundary_times) - 1):
        sections.append(
            {
                "label": labels[i],
                "start_seconds": boundary_times[i],
                "end_seconds": boundary_times[i + 1],
            }
        )
    return sections


def _novelty_curve(rec: np.ndarray) -> np.ndarray:
    """Checkerboard-kernel novelty curve from a self-similarity/recurrence
    matrix, used to find likely structural boundaries.
    """
    n = rec.shape[0]
    kernel_size = max(4, min(32, n // 8))
    kernel = _checkerboard_kernel(kernel_size)
    pad = kernel_size
    padded = np.pad(rec, pad, mode="constant")
    novelty = np.zeros(n)
    for i in range(n):
        window = padded[i : i + 2 * kernel_size, i : i + 2 * kernel_size]
        if window.shape == kernel.shape:
            novelty[i] = float(np.sum(window * kernel))
    novelty = novelty - novelty.min()
    if novelty.max() > 0:
        novelty = novelty / novelty.max()
    return novelty


def _checkerboard_kernel(size: int) -> np.ndarray:
    axis = np.arange(2 * size) - size
    sign = np.sign(np.outer(axis, axis))
    gauss = np.outer(
        np.exp(-(axis**2) / (2 * (size / 2) ** 2)),
        np.exp(-(axis**2) / (2 * (size / 2) ** 2)),
    )
    return sign * gauss


def _label_sections(n: int) -> list[str]:
    """Generic placeholder labels; a human relabels these as verse/chorus/
    solo/etc after listening, since unsupervised novelty detection finds
    *where* the music changes, not *what* the new section is.
    """
    return [f"section_{i + 1}" for i in range(n)]
