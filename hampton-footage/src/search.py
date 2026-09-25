"""Step 1: search YouTube for every query in config/search_terms.txt.

Writes data/raw_results.json: one record per unique video, with the metadata
filter.py needs (title, description, tags, duration, upload date, channel) and
the queries that found it.

Quota: the YouTube Data API gives 10,000 units per day (reset at midnight
Pacific time). A search costs 100 units per page; fetching video details costs
1 unit per 50 videos. This script:
  * fetches one page (50 results) per query by default (10 queries ~ 1,000 units),
  * caches every API response under data/raw/ and reuses it on re-runs,
  * keeps a per-day ledger in data/quota_ledger.json and refuses to go past
    --budget units in one Pacific day (default 2,000).

Usage:
    python src/search.py                # search, reusing cached responses
    python src/search.py --dry-run      # show what it would cost, call nothing
    python src/search.py --refresh      # ignore the cache and search again
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from common import CONFIG_DIR, DATA_DIR, RAW_DIR, RAW_RESULTS, load_env, parse_iso_duration, read_lines, slugify

API_BASE = "https://www.googleapis.com/youtube/v3"
SEARCH_COST = 100
VIDEOS_COST = 1
VIDEOS_BATCH = 50
DAILY_QUOTA = 10_000
DEFAULT_BUDGET = 2_000
LEDGER = DATA_DIR / "quota_ledger.json"
SEARCH_CACHE = RAW_DIR / "search"
VIDEOS_CACHE = RAW_DIR / "videos.json"


class QuotaExhausted(Exception):
    pass


class ApiError(Exception):
    pass


class QuotaLedger:
    """Tracks units spent per Pacific-time day so repeated runs stay under budget."""

    def __init__(self, path: Path, budget: int):
        self.path = path
        self.budget = budget
        self.data = json.loads(path.read_text()) if path.exists() else {}

    @staticmethod
    def today() -> str:
        return datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()

    def spent_today(self) -> int:
        return self.data.get(self.today(), 0)

    def reserve(self, units: int) -> None:
        if self.spent_today() + units > self.budget:
            raise QuotaExhausted(
                f"Next call needs {units} units; {self.spent_today()} of the "
                f"{self.budget}-unit daily budget already used."
            )

    def record(self, units: int) -> None:
        self.data[self.today()] = self.spent_today() + units
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True))


def api_get(session: requests.Session, endpoint: str, params: dict, api_key: str) -> dict:
    """GET an API endpoint. Error messages never include the URL (it holds the key)."""
    response = session.get(f"{API_BASE}/{endpoint}", params={**params, "key": api_key}, timeout=30)
    if response.status_code == 200:
        return response.json()
    try:
        error = response.json().get("error", {})
        reasons = {e.get("reason") for e in error.get("errors", [])}
        message = error.get("message", "")
    except ValueError:
        reasons, message = set(), response.text[:200]
    if reasons & {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
        raise QuotaExhausted(f"YouTube says the quota is used up: {message}")
    raise ApiError(f"{endpoint} failed with HTTP {response.status_code}: {message}")


def search_query(session, api_key, query, pages, ledger, refresh) -> list[str]:
    """Return video IDs for one query, from cache when possible."""
    cache = SEARCH_CACHE / f"{slugify(query)}.json"
    if cache.exists() and not refresh:
        cached = json.loads(cache.read_text())
        if cached.get("pages", 0) >= pages:
            print(f"  cached   {query!r}: {len(cached['video_ids'])} videos")
            return cached["video_ids"]

    video_ids: list[str] = []
    responses = []
    page_token = None
    for _ in range(pages):
        ledger.reserve(SEARCH_COST)
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 50,
            "order": "relevance",
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get(session, "search", params, api_key)
        ledger.record(SEARCH_COST)
        responses.append(data)
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid and vid not in video_ids:
                video_ids.append(vid)
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(
        {"query": query, "pages": pages, "fetched": datetime.now().isoformat(timespec="seconds"),
         "video_ids": video_ids, "responses": responses},
        indent=2,
    ))
    print(f"  searched {query!r}: {len(video_ids)} videos")
    return video_ids


def fetch_details(session, api_key, video_ids, ledger, refresh) -> dict:
    """Title, description, tags, duration etc. for each video, cached by ID."""
    cached = {} if refresh or not VIDEOS_CACHE.exists() else json.loads(VIDEOS_CACHE.read_text())
    missing = [v for v in video_ids if v not in cached]
    try:
        for start in range(0, len(missing), VIDEOS_BATCH):
            batch = missing[start:start + VIDEOS_BATCH]
            ledger.reserve(VIDEOS_COST)
            data = api_get(session, "videos",
                           {"part": "snippet,contentDetails", "id": ",".join(batch), "maxResults": 50},
                           api_key)
            ledger.record(VIDEOS_COST)
            for item in data.get("items", []):
                cached[item["id"]] = item
    finally:
        VIDEOS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        VIDEOS_CACHE.write_text(json.dumps(cached, indent=2))
    return cached


def to_record(item: dict, queries: list[str]) -> dict:
    snippet = item.get("snippet", {})
    duration_iso = item.get("contentDetails", {}).get("duration", "")
    return {
        "video_id": item["id"],
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "tags": snippet.get("tags", []),
        "channel": snippet.get("channelTitle", ""),
        "channel_id": snippet.get("channelId", ""),
        "published_at": snippet.get("publishedAt", ""),
        "category_id": snippet.get("categoryId", ""),
        "duration_iso": duration_iso,
        "duration_seconds": parse_iso_duration(duration_iso),
        "queries": queries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terms", type=Path, default=CONFIG_DIR / "search_terms.txt")
    parser.add_argument("--pages", type=int, default=1,
                        help="result pages (50 videos, 100 units) per query; default 1")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                        help=f"max units to spend per Pacific day; default {DEFAULT_BUDGET} of {DAILY_QUOTA}")
    parser.add_argument("--refresh", action="store_true", help="ignore cached responses")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and cost, call nothing")
    args = parser.parse_args(argv)

    if args.budget > DAILY_QUOTA:
        parser.error(f"--budget cannot exceed the daily quota of {DAILY_QUOTA}")

    queries = read_lines(args.terms)
    ledger = QuotaLedger(LEDGER, args.budget)
    worst_case = len(queries) * args.pages * (SEARCH_COST + VIDEOS_COST)
    print(f"{len(queries)} queries x {args.pages} page(s): up to ~{worst_case} units "
          f"(budget {args.budget}, already used today {ledger.spent_today()}).")
    if args.dry_run:
        for q in queries:
            print(f"  {q}")
        return 0

    load_env()
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("YOUTUBE_API_KEY is not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        return 1

    session = requests.Session()
    found: dict[str, list[str]] = {}
    stopped = None
    try:
        for query in queries:
            for vid in search_query(session, api_key, query, args.pages, ledger, args.refresh):
                found.setdefault(vid, []).append(query)
    except (QuotaExhausted, ApiError) as exc:
        stopped = exc
        print(f"Stopped searching: {exc}", file=sys.stderr)

    details = {}
    if found:
        try:
            details = fetch_details(session, api_key, list(found), ledger, args.refresh)
        except (QuotaExhausted, ApiError) as exc:
            stopped = stopped or exc
            print(f"Stopped fetching details: {exc}", file=sys.stderr)
            details = json.loads(VIDEOS_CACHE.read_text()) if VIDEOS_CACHE.exists() else {}

    records = [to_record(details[vid], qs) for vid, qs in found.items() if vid in details]
    RAW_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RAW_RESULTS.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Wrote {len(records)} unique videos to {RAW_RESULTS.relative_to(RAW_RESULTS.parents[1])}. "
          f"Units used today: {ledger.spent_today()}.")
    return 2 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
