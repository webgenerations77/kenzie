"""Generate a short synthetic audio clip for testing the pipeline without
a real song recording.

The clip is built from sine tones (not a real instrument recording) but has
a clear, steady 120 BPM click/beat pulse plus two audibly distinct
"sections" (a change in chord/frequency content partway through), so the
librosa analysis has real tempo/beat/section structure to find.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

SAMPLE_RATE = 22050


def make_synthetic_clip(
    path: str,
    duration_seconds: float = 12.0,
    bpm: float = 120.0,
    sr: int = SAMPLE_RATE,
) -> None:
    n_samples = int(duration_seconds * sr)
    t = np.arange(n_samples) / sr

    # Section A (first half): a two-note pad, section B (second half): a
    # higher, brighter pad -> gives the section detector real novelty to find.
    half = n_samples // 2
    section_a_freqs = [220.0, 277.18]  # A3, C#4
    section_b_freqs = [329.63, 415.30]  # E4, G#4

    pad = np.zeros(n_samples)
    for f in section_a_freqs:
        pad[:half] += 0.15 * np.sin(2 * np.pi * f * t[:half])
    for f in section_b_freqs:
        pad[half:] += 0.15 * np.sin(2 * np.pi * f * t[half:])

    # A steady click/beat pulse at the given BPM (like a kick drum), which
    # also anchors clear downbeats every 4th click.
    beat_period = 60.0 / bpm
    click = np.zeros(n_samples)
    click_len = int(0.03 * sr)
    envelope = np.exp(-np.linspace(0, 20, click_len))
    beat_index = 0
    beat_time = 0.0
    while beat_time < duration_seconds:
        start = int(beat_time * sr)
        end = min(start + click_len, n_samples)
        length = end - start
        # Accent every 4th beat (the downbeat) so there is real signal for
        # the downbeat-phase heuristic to lock onto.
        amplitude = 0.9 if beat_index % 4 == 0 else 0.6
        click[start:end] += amplitude * envelope[:length]
        beat_time += beat_period
        beat_index += 1

    mix = pad + click
    mix = mix / np.max(np.abs(mix)) * 0.9
    sf.write(path, mix.astype(np.float32), sr)


if __name__ == "__main__":
    import sys

    out_path = sys.argv[1] if len(sys.argv) > 1 else "synthetic_clip.wav"
    make_synthetic_clip(out_path)
    print(f"Wrote {out_path}")
