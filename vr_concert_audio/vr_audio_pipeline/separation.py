"""Stem separation via Demucs (htdemucs_6s: vocals, drums, bass, guitar,
piano, other).

Demucs and torch are imported lazily inside `separate()` so that the rest
of the pipeline (analysis, CLI --help, config loading, tests) works even on
a machine that hasn't installed the (large, GPU-oriented) separation
dependencies yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from .config import SeparationConfig

# Stems produced by htdemucs_6s, in the order Demucs returns them.
HTDEMUCS_6S_STEMS = ["vocals", "drums", "bass", "guitar", "piano", "other"]


def resolve_device(requested: str) -> str:
    """Resolve "auto" to "cuda" if a GPU is available, else "cpu"."""
    if requested != "auto":
        return requested
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def separate(
    input_path: str | Path,
    output_dir: str | Path,
    config: SeparationConfig,
    log: Callable[[str], None] = print,
) -> dict[str, Path]:
    """Run Demucs separation and return {stem_name: wav_path}.

    Raises ImportError with a helpful message if demucs/torch aren't
    installed. Requires `demucs` (and its own `torch`/`torchaudio` deps) —
    see requirements.txt and the README setup steps.
    """
    try:
        import torch
        from demucs.apply import apply_model
        from demucs.audio import save_audio
        from demucs.pretrained import get_model
    except ImportError as exc:
        raise ImportError(
            "Demucs (and torch) are required for stem separation. "
            "Install them with `pip install -r requirements.txt` "
            "(see README.md for the Ubuntu/GPU-specific torch install)."
        ) from exc

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    stems_dir = output_dir / "stems"
    stems_dir.mkdir(parents=True, exist_ok=True)

    device = resolve_device(config.device)
    log(f"Loading Demucs model '{config.model}' on device '{device}'...")
    model = get_model(config.model)
    model.to(device)
    model.eval()

    import librosa

    wav, sr = librosa.load(str(input_path), sr=model.samplerate, mono=False)
    if wav.ndim == 1:
        wav = wav[None, :]  # mono -> (1, n) then duplicated to stereo below
    if wav.shape[0] == 1:
        wav = wav.repeat(2, axis=0)
    wav_t = torch.as_tensor(wav, dtype=torch.float32)

    log("Separating stems (this can take a while on CPU)...")
    with torch.no_grad():
        sources = apply_model(
            model,
            wav_t[None],
            device=device,
            shifts=config.shifts,
            segment=config.segment,
            split=True,
            progress=True,
        )[0]

    stem_paths: dict[str, Path] = {}
    for name, source in zip(model.sources, sources):
        out_path = stems_dir / f"{name}.{config.stem_format}"
        save_audio(source, str(out_path), model.samplerate)
        stem_paths[name] = out_path
        log(f"  wrote {out_path}")

    return stem_paths


def combined_stems_note(model_name: str) -> Optional[str]:
    """Note about instruments the given model folds into "other"."""
    if model_name == "htdemucs_6s":
        return (
            "htdemucs_6s does not have dedicated stems for violin or "
            "saxophone; both will be mixed into the 'other' stem. See "
            "README.md for options to separate them further."
        )
    return None
