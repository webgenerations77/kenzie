# hampton-footage

Finds and catalogs video of the **Dave Matthews Band at Hampton Coliseum on
12/31/1996**, the New Year's Eve show with Béla Fleck and the Flecktones. The
main targets are the **midnight countdown** and **Tripping Billies**.

There are four steps:

| Step | Script | Runs where | What it does |
|------|--------|-----------|--------------|
| 1 | `src/search.py` | anywhere | Searches YouTube for every query in `config/search_terms.txt` |
| 2 | `src/filter.py` | anywhere | Applies `config/rules.yaml` and writes `output/shortlist.csv` |
| 3 | `src/fetch.py`  | your Ubuntu server | Downloads the shortlisted clips with yt-dlp |
| 4 | `src/frames.py` | your Ubuntu server | Grabs a frame every 3 s with ffmpeg and builds one contact sheet per clip |

`src/report.py` is a placeholder for a later summary page (see Roadmap).

## Layout

```
config/search_terms.txt   search queries, one per line (# for comments)
config/rules.yaml         keep / exclude / audio-only / focus words, reupload settings
src/                      the scripts (common.py holds shared paths and helpers)
data/raw/                 cached YouTube API responses (reused so re-runs cost nothing)
data/raw_results.json     every unique video found by search.py
data/quota_ledger.json    API units spent per day
data/filtered_out.csv     what filter.py dropped, and why
data/clips/, data/frames/ downloads and extracted frames (server only, not committed)
output/shortlist.csv      the shortlist
output/audio_only.csv     matches that look like audio-only uploads
output/contact_sheets/    one JPEG per clip (server only, not committed)
tests/                    tests for search.py and filter.py
```

## Setup

You need Python 3.9 or newer.

```bash
cd hampton-footage
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then put your YouTube Data API key in `.env`:

1. Go to <https://console.cloud.google.com/>, create (or pick) a project.
2. APIs & Services → Library → enable **YouTube Data API v3**.
3. APIs & Services → Credentials → Create credentials → **API key**.
   Restricting it to the YouTube Data API is a good idea.
4. Edit `.env`: `YOUTUBE_API_KEY=your-key-here`

`.env` is in `.gitignore`. Never commit it.

## Step 1 — search

```bash
python src/search.py --dry-run   # show the queries and the cost, call nothing
python src/search.py
```

**Quota.** YouTube gives each project 10,000 units per day, reset at midnight
Pacific time. A search costs 100 units per page of 50 results; looking up video
details costs 1 unit per 50 videos. With the 10 seed queries and the defaults,
a full run costs about **1,000 units**.

To stay well inside the limit, search.py:

- fetches **one page per query** by default (`--pages 2` doubles the cost),
- **caches** every response in `data/raw/` and reuses it, so running it again
  is free — use `--refresh` only when you want fresh results,
- keeps a per-day tally in `data/quota_ledger.json` and **stops before
  going over `--budget`** (default 2,000 units/day). If it stops early, just
  run it again tomorrow — finished queries are cached.

Adding a query to `config/search_terms.txt` costs 100 units the next time you
run; the existing ones stay cached.

## Step 2 — filter

```bash
python src/filter.py
```

No API calls, so re-run it as often as you like after tweaking `config/rules.yaml`.

Rules (all in `config/rules.yaml`), checked against title, description and tags:

- **Keep** only results mentioning `1996`, `12/31/96`, `Flecktones` or
  `Live Trax 7` (plus spelling variants such as `12.31.96`, `12-31-1996`,
  `Live Trax Vol. 7`).
- **Exclude** anything mentioning `1995` or `12/30` (and `12.30`, `12-30`),
  because the band also played Hampton on New Year's Eve 1995. Exclude wins
  over keep, so a description like "1995–1996 tour" is dropped too — check
  `data/filtered_out.csv` if you think something good was lost.
- **Audio-only** matches go to `output/audio_only.csv`, not the shortlist.
  A result counts as audio-only if it comes from an auto-generated
  "- Topic" channel, says things like "audio only" or "Provided to YouTube by",
  or uses words such as "audio", "SBD", "soundboard" or "Live Trax" without any
  video word ("camcorder", "video", "footage", "pro-shot", ...).
- **Reuploads** are merged: two results with durations within 2 seconds and
  similar titles (or both longer than 10 minutes) are treated as the same
  upload. The earliest is kept and the others are listed in its `reuploads` column.
- **Focus score**: +1 for each of "Tripping Billies", "midnight",
  "countdown", "balloon", "Auld Lang Syne", "New Year's Eve" and similar.
  The shortlist is sorted by this score, highest first.

`output/shortlist.csv` columns:

| column | meaning |
|--------|---------|
| title | video title |
| link | YouTube link |
| duration | H:MM:SS |
| upload_date | YYYY-MM-DD |
| why_matched | which keep words matched and where, plus any focus words |
| focus_score | how many focus words matched |
| channel, video_id | uploader and YouTube ID |
| reuploads | links to copies that were merged into this row |

## Steps 3 and 4 — on the Ubuntu server

Copy the project (with `output/shortlist.csv`) to the server, then:

```bash
sudo apt update && sudo apt install -y ffmpeg python3-venv
cd hampton-footage
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-server.txt
```

### Step 3 — fetch

```bash
python src/fetch.py --dry-run       # list what would be downloaded
python src/fetch.py --limit 5       # try the top 5 first
python src/fetch.py                 # everything on the shortlist
python src/fetch.py --ids VIDEO_ID  # specific videos
```

Clips go to `data/clips/<video_id>.mp4` with a `.info.json` next to each.
Downloads are capped at 720p by default (`--max-height`), wait 5 seconds
between videos (`--sleep`), and anything already downloaded is skipped
(tracked in `data/clips/archive.txt`). If downloads start failing, update
yt-dlp first: `pip install -U yt-dlp`.

### Step 4 — frames and contact sheets

```bash
python src/frames.py
python src/frames.py --ids VIDEO_ID
```

For each clip this saves one frame every 3 seconds to
`data/frames/<video_id>/` and builds `output/contact_sheets/<video_id>.jpg`:
a grid of those frames with the clip time (H:MM:SS) under each one, so you can
spot the countdown or the balloon drop and jump straight to that point.
Options: `--interval` (seconds between frames), `--width` (frame size),
`--columns` (frames per row), `--force` (redo existing frames).
A 2-hour clip makes about 2,400 frames, so frames are kept small; very long
clips are shrunk further so the sheet stays a valid JPEG.

## Tests

```bash
python -m unittest discover tests
```

These cover search.py (with a fake API — no key or quota needed) and filter.py.

## Roadmap

- Run search.py with a real key and review the first shortlist.
- Tune `config/rules.yaml` and search terms based on what turns up.
- Run fetch.py and frames.py on the server.
- Build report.py: one page tying each clip to its contact sheet and the
  timestamps of the midnight countdown and Tripping Billies.
