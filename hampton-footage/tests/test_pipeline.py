"""Tests for search.py and filter.py. Run: python -m unittest discover tests"""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import common  # noqa: E402
import filter as flt  # noqa: E402
import search  # noqa: E402

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


RULES = flt.Rules.load(common.CONFIG_DIR / "rules.yaml")


def rec(vid, title, description="", tags=None, duration=300, published="2010-01-01T00:00:00Z", channel="fan"):
    return {"video_id": vid, "title": title, "description": description, "tags": tags or [],
            "duration_seconds": duration, "published_at": published, "channel": channel}


class FilterTests(unittest.TestCase):
    def classify(self, *records):
        return flt.classify(list(records), RULES)

    def test_keeps_1996_show(self):
        video, audio, rejected = self.classify(rec("a", "Dave Matthews Band - Tripping Billies - Hampton 12/31/96 camcorder"))
        self.assertEqual([r["video_id"] for r in video], ["a"])
        self.assertIn("'12/31/96' in title", video[0]["why"])
        self.assertIn("tripping billies", video[0]["why"])
        self.assertEqual(video[0]["focus_score"], 1)

    def test_keep_variants(self):
        for title in ["DMB 12.31.96 Hampton", "DMB w/ Flecktones Hampton",
                      "Live Trax Vol. 7 video", "DMB 12-31-1996"]:
            video, audio, rejected = self.classify(rec("x", title + " video"))
            self.assertEqual(len(video), 1, title)

    def test_excludes_1995_and_12_30(self):
        for title in ["DMB Hampton 12/31/95 1996 tour", "DMB 12/30/96 Hampton",
                      "DMB 12.30.96", "DMB Hampton New Years 1995"]:
            video, audio, rejected = self.classify(rec("x", title))
            self.assertEqual(len(rejected), 1, title)
            self.assertTrue(rejected[0]["why"].startswith("excluded"), title)

    def test_exclude_checks_description_and_tags(self):
        _, _, rejected = self.classify(rec("x", "DMB 1996", description="Hampton 1995"),
                                       rec("y", "DMB 1996", tags=["12/30"]))
        self.assertEqual(len(rejected), 2)

    def test_needs_keep_word(self):
        _, _, rejected = self.classify(rec("x", "Dave Matthews Band Hampton New Years"))
        self.assertEqual(rejected[0]["why"], "no keep word")

    def test_whole_word_only(self):
        _, _, rejected = self.classify(rec("x", "DMB clip 199612"))
        self.assertEqual(len(rejected), 1)

    def test_audio_only_flags(self):
        video, audio, _ = self.classify(
            rec("a", "Tripping Billies (Live Trax 7)", channel="Dave Matthews Band - Topic"),
            rec("b", "DMB 12/31/96 SBD audio"),
            rec("c", "DMB 12/31/96 full show", description="Provided to YouTube by RCA"),
            rec("d", "DMB 12/31/96 camcorder video with great audio"),
        )
        self.assertEqual(sorted(r["video_id"] for r in audio), ["a", "b", "c"])
        self.assertEqual([r["video_id"] for r in video], ["d"])

    def test_dedupe_reuploads_keeps_earliest(self):
        records = [
            rec("new", "DMB - Tripping Billies 12/31/96 (reupload HD)", duration=421, published="2015-01-01T00:00:00Z"),
            rec("old", "Dave Matthews Band Tripping Billies 12-31-96", duration=420, published="2008-01-01T00:00:00Z"),
            rec("other", "DMB Tripping Billies 12/31/96 (different camera)", duration=455),
            rec("long2", "Totally different title", duration=7201, published="2019-01-01T00:00:00Z"),
            rec("long1", "DMB full show 1996", duration=7200, published="2012-01-01T00:00:00Z"),
            rec("old", "duplicate id", duration=420),
        ]
        kept = {r["video_id"]: r for r in flt.dedupe(records, RULES)}
        self.assertEqual(sorted(kept), ["long1", "old", "other"])
        self.assertEqual(kept["old"]["reuploads"], [common.video_url("new")])
        self.assertEqual(kept["long1"]["reuploads"], [common.video_url("long2")])

    def test_main_writes_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            raw = tmp / "raw.json"
            raw.write_text(json.dumps([
                rec("a", "DMB countdown midnight 12/31/96 camcorder", duration=3725, published="2009-05-02T10:00:00Z"),
                rec("b", "DMB 1996 audio"),
                rec("c", "DMB 12/30/96"),
            ]))
            with mock.patch.object(flt, "SHORTLIST", tmp / "shortlist.csv"), \
                    mock.patch.object(flt, "AUDIO_ONLY", tmp / "audio.csv"), \
                    mock.patch.object(flt, "FILTERED_OUT", tmp / "out.csv"):
                self.assertEqual(flt.main(["--input", str(raw)]), 0)
            rows = read_csv(tmp / "shortlist.csv")
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["link"], "https://www.youtube.com/watch?v=a")
            self.assertEqual(row["duration"], "1:02:05")
            self.assertEqual(row["upload_date"], "2009-05-02")
            self.assertIn("focus: 'midnight'", row["why_matched"])
            self.assertEqual(len(read_csv(tmp / "audio.csv")), 1)
            self.assertEqual(len(read_csv(tmp / "out.csv")), 1)


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self._payload, self.text = status, payload, json.dumps(payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, quota_error_after=None):
        self.calls = []
        self.quota_error_after = quota_error_after

    def get(self, url, params, timeout):
        self.calls.append((url, params))
        if self.quota_error_after is not None and len(self.calls) > self.quota_error_after:
            return FakeResponse(403, {"error": {"message": "quota", "errors": [{"reason": "quotaExceeded"}]}})
        if url.endswith("/search"):
            n = len(self.calls)
            return FakeResponse(200, {"items": [{"id": {"videoId": f"v{n}"}}, {"id": {"videoId": "shared"}}]})
        ids = params["id"].split(",")
        return FakeResponse(200, {"items": [
            {"id": i, "snippet": {"title": f"t{i}", "publishedAt": "2010-01-01T00:00:00Z"},
             "contentDetails": {"duration": "PT7M1S"}} for i in ids]})


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.terms = self.tmp / "terms.txt"
        self.terms.write_text("# comment\nquery one\n\nquery two\n")
        self.patches = [
            mock.patch.object(search, "LEDGER", self.tmp / "ledger.json"),
            mock.patch.object(search, "SEARCH_CACHE", self.tmp / "raw" / "search"),
            mock.patch.object(search, "VIDEOS_CACHE", self.tmp / "raw" / "videos.json"),
            mock.patch.object(search, "RAW_RESULTS", self.tmp / "data" / "raw_results.json"),
            mock.patch.object(search, "load_env", lambda: None),
            mock.patch.dict("os.environ", {"YOUTUBE_API_KEY": "SECRET-KEY"}),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def run_search(self, session, *args):
        with mock.patch.object(search.requests, "Session", return_value=session):
            return search.main(["--terms", str(self.terms), *args])

    def test_search_merges_and_caches(self):
        session = FakeSession()
        self.assertEqual(self.run_search(session), 0)
        records = json.loads((self.tmp / "data" / "raw_results.json").read_text())
        by_id = {r["video_id"]: r for r in records}
        self.assertEqual(sorted(by_id), ["shared", "v1", "v2"])
        self.assertEqual(by_id["shared"]["queries"], ["query one", "query two"])
        self.assertEqual(by_id["v1"]["duration_seconds"], 421)
        self.assertEqual(len(session.calls), 3)  # 2 searches + 1 details batch
        ledger = json.loads((self.tmp / "ledger.json").read_text())
        self.assertEqual(list(ledger.values()), [201])

        second = FakeSession()
        self.assertEqual(self.run_search(second), 0)
        self.assertEqual(second.calls, [])  # everything served from cache

    def test_budget_stops_before_overspending(self):
        session = FakeSession()
        self.assertEqual(self.run_search(session, "--budget", "150"), 2)
        self.assertEqual(sum(url.endswith("/search") for url, _ in session.calls), 1)
        ledger = json.loads((self.tmp / "ledger.json").read_text())
        self.assertLessEqual(list(ledger.values())[0], 150)

    def test_quota_error_is_reported_without_key(self):
        session = FakeSession(quota_error_after=1)
        with mock.patch("sys.stderr") as err:
            self.assertEqual(self.run_search(session), 2)
        written = "".join(str(c.args[0]) for c in err.write.call_args_list)
        self.assertIn("quota", written)
        self.assertNotIn("SECRET-KEY", written)

    def test_dry_run_calls_nothing(self):
        session = FakeSession()
        self.assertEqual(self.run_search(session, "--dry-run"), 0)
        self.assertEqual(session.calls, [])

    def test_parse_duration(self):
        self.assertEqual(common.parse_iso_duration("PT1H2M3S"), 3723)
        self.assertEqual(common.parse_iso_duration("P0D"), 0)
        self.assertEqual(common.parse_iso_duration("bad"), 0)


if __name__ == "__main__":
    unittest.main()
