# VR Concert Audio Pipeline

Takes a single song recording (WAV or FLAC) and produces:

1. **Stems** via [Demucs](https://github.com/facebookresearch/demucs)
   (`htdemucs_6s` model): `vocals`, `drums`, `bass`, `guitar`, `piano`, `other`.
2. **Musical analysis** via [librosa](https://librosa.org/): tempo, a beat
   grid with timestamps, downbeats, and estimated section boundaries.
3. **`beat_map.json`**, **`markers.csv`**, and a plain-text **`summary.txt`**,
   all with timestamps in seconds — meant to drive lighting/avatar/effect
   cues in a VR concert recreation.

No real audio is included in this repo. Everything below was developed and
tested against a short **synthetic** clip generated in code (see
`tests/synthetic_audio.py`) — sine-tone "chords" plus a clicky beat pulse at
a known BPM, with a deliberate tonal change partway through to exercise
section detection. Supply your own WAV/FLAC at runtime via `--input` or
`config.yaml`.

## Layout

```
vr_concert_audio/
  config.yaml                  # default config (edit input_path per song)
  requirements.txt
  vr_audio_pipeline/
    cli.py                     # entry point: python -m vr_audio_pipeline.cli
    config.py                  # config loading + defaults
    separation.py              # Demucs stem separation
    analysis.py                # librosa tempo/beat/downbeat/section analysis
    output.py                  # beat_map.json / markers.csv / summary.txt writers
  tests/
    synthetic_audio.py         # generates the synthetic test clip
    test_pipeline.py           # pytest suite, runs entirely on synthetic audio
  input/                       # put your real song here (gitignored)
  output/                      # pipeline outputs land here (gitignored)
```

## Setup on Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip ffmpeg libsndfile1

cd vr_concert_audio
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Install torch matching your hardware BEFORE the rest of requirements.txt.
# GPU (CUDA 12.1 example — check https://pytorch.org/get-started/locally/
# for the command matching your driver/CUDA version):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
# CPU-only server:
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt
```

The first run downloads the `htdemucs_6s` model weights (a few hundred MB)
from Demucs' model hub, so the server needs outbound internet access at
least once; after that the weights are cached locally (`~/.cache/torch`).

## Usage

```bash
# Edit config.yaml (or copy it) to point at your file, then:
python -m vr_audio_pipeline.cli --config config.yaml

# Or override individual fields without editing the config:
python -m vr_audio_pipeline.cli \
  --input input/my_song.wav \
  --output-dir output/my_song \
  --device cuda   # or cpu / auto (default: auto-detect)
```

Useful flags:
- `--skip-separation` — run only the librosa analysis (fast, no GPU/Demucs
  needed). Good for iterating on beat/section detection.
- `--skip-analysis` — run only stem separation.
- `--model` — override the Demucs model (default `htdemucs_6s`).

Outputs land in `output_dir/`:
- `stems/vocals.wav`, `stems/drums.wav`, `stems/bass.wav`,
  `stems/guitar.wav`, `stems/piano.wav`, `stems/other.wav`
- `beat_map.json` — tempo, every beat/downbeat timestamp, section list, and
  (if separation ran) stem file paths.
- `markers.csv` — a flat, sorted `time_seconds,type,label` table combining
  downbeats and section starts, convenient to import into a VR
  timeline/animation tool.
- `summary.txt` — a short human-readable recap.

## Testing without a real song

```bash
source .venv/bin/activate
pip install pytest
python -m pytest tests/ -v
```

The suite generates a synthetic clip on the fly (nothing is committed) and
checks: tempo/beat/downbeat detection lands near the clip's known BPM,
detected sections tile the clip with no gaps, all three output files are
written with the expected shape, and the CLI's `--skip-separation` path
runs end-to-end. Demucs/torch are **not** exercised by the automated tests
(no GPU in CI/dev sandboxes and the model weights aren't downloaded there);
`separation.py` is still built to run for real once torch/demucs are
installed — validate it once against your own audio, e.g.:

```bash
python -m vr_audio_pipeline.cli --input input/my_song.wav --output-dir /tmp/smoke_test
```

## Handling violin and saxophone ("other" stem)

`htdemucs_6s` only separates vocals/drums/bass/guitar/piano/other — violin
and saxophone are **not** dedicated stems and will end up mixed into
`other` along with anything else the model doesn't recognize. Options if
you need them isolated:

1. **Re-run Demucs on the `other` stem** with a different model as a second
   pass — won't cleanly split violin from sax, but can pull residual
   drums/bass bleed out if any remains.
2. **Spleeter** (Deezer) or other 4/5-stem separators don't have violin/sax
   stems either — same limitation, different model.
3. **Train or fine-tune** a Demucs model on a violin/sax-labeled dataset —
   accurate but a significant undertaking, only worth it for a production
   pipeline used across many songs.
4. **Manual isolation** — if the multitrack/stems from the original
   recording session are available (unlikely for a live concert
   recreation), use those directly instead of source separation.
5. **Spectral/pitch-based heuristics** on the `other` stem (e.g. isolating
   energy in violin's or sax's typical pitch range with a bandpass +
   harmonic/percussive separation) — cheap to try, unreliable when the two
   overlap in range or with residual guitar/piano bleed.

For a VR concert, option 1 or accepting `other` as a single "everything
else" avatar/effect layer is usually the pragmatic choice unless the
setlist is dominated by violin/sax parts.

## Assumptions made (no input song was available this session)

Since this was built without a real recording to test against, these
choices were made and should be revisited once real audio is available:

- **4/4 time signature.** Downbeats are estimated by picking whichever
  beat-grid phase (every 4th beat) has the strongest low-frequency onset
  energy, i.e. a lightweight heuristic tuned for common 4/4 pop/rock
  songs — not a dedicated downbeat tracker. If a song is in 3/4, 6/8, etc.,
  this will misplace downbeats; swapping in something like madmom's
  `DBNDownBeatTrackingProcessor` would give more accurate results (not
  included here to keep the dependency list smaller unless it's needed).
- **Section boundaries are structural change points, not labeled
  verse/chorus/solo.** `analysis.py` finds *where* the music's timbre and
  harmony content changes using a self-similarity/novelty method, then
  labels boundaries generically (`section_1`, `section_2`, ...). Turning
  those into meaningful verse/chorus/solo labels needs a human listen (or
  a separate structure-labeling model) — the pipeline doesn't guess genre
  conventions.
- **Sample rate 44.1kHz for analysis config default**, but the synthetic
  test clip uses 22.05kHz for faster test runs — both are supported since
  librosa resamples on load.
- **`shifts: 0`, `segment: null`** for Demucs by default — fastest
  settings. If separation quality matters more than speed (especially on
  CPU-only hardware), raise `shifts` to 1-2 in `config.yaml`, at the cost
  of proportionally longer runtime.
- **`device: auto`** picks CUDA if `torch.cuda.is_available()`, else CPU.
  No multi-GPU handling — assumes a single-GPU or CPU-only server.
- **Minimum section length defaults to 8 seconds** (`min_section_seconds`
  in config) to avoid flagging every bar as a new "section"; tune this per
  song if sections are getting merged or over-split.
- Real audio files (WAV/FLAC/MP3/etc.), the `input/` and `output/`
  directories, and the Python virtualenv are all gitignored — nothing
  audio-related should ever be committed to this repo.
