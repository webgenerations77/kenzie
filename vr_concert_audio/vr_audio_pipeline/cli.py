"""CLI entry point for the VR concert audio pipeline.

Usage:
    python -m vr_audio_pipeline.cli --config config.yaml
    python -m vr_audio_pipeline.cli --input input/song.wav --output-dir output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analysis import analyze
from .config import PipelineConfig
from .output import write_outputs
from .separation import combined_stems_note, separate


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Separate a song into stems (Demucs) and analyze its "
        "tempo/beat grid/sections (librosa) for VR concert recreation."
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to a YAML config file."
    )
    parser.add_argument(
        "--input", type=str, default=None, help="Override input_path from config."
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Override output_dir from config."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the Demucs model (default: htdemucs_6s).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda"],
        help="Override separation device (default: auto).",
    )
    parser.add_argument(
        "--skip-separation",
        action="store_true",
        help="Skip Demucs stem separation and only run the librosa analysis.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip librosa analysis and only run stem separation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = PipelineConfig.load(args.config)
    config.apply_overrides(
        input_path=args.input,
        output_dir=args.output_dir,
        model=args.model,
        device=args.device,
    )

    input_path = Path(config.input_path)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem_paths = None
    if not args.skip_separation:
        stem_paths = separate(input_path, output_dir, config.separation, log=print)
        note = combined_stems_note(config.separation.model)
        if note:
            print(f"Note: {note}")
    else:
        print("Skipping stem separation (--skip-separation).")

    if not args.skip_analysis:
        print("Analyzing full mix with librosa...")
        result = analyze(str(input_path), config.analysis)
        paths = write_outputs(
            result,
            output_dir,
            config.output,
            input_path=str(input_path),
            stem_paths=stem_paths,
        )
        print(f"Tempo: {result.tempo_bpm} BPM")
        print(f"Beats: {len(result.beat_times)}, Downbeats: {len(result.downbeat_times)}")
        print(f"Sections: {len(result.sections)}")
        for name, path in paths.items():
            print(f"Wrote {name}: {path}")
    else:
        print("Skipping analysis (--skip-analysis).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
