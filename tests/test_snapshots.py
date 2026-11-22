#!/usr/bin/env python3
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from snapshots import apply_retention, gzip_bytes, select_retained_dates  # noqa: E402


class RetentionTest(unittest.TestCase):
    def test_keeps_thirty_daily_and_latest_older_month(self):
        today = date(2026, 11, 22)
        dates = []
        cursor = date(2026, 8, 1)
        while cursor <= today:
            dates.append(cursor)
            cursor += timedelta(days=1)
        roles = select_retained_dates(dates, today, daily=30)
        daily = {item for item, role in roles.items() if role == "daily"}
        monthly = {item for item, role in roles.items() if role == "monthly"}
        self.assertEqual(daily, {today - timedelta(days=offset) for offset in range(30)})
        self.assertEqual(
            monthly,
            {date(2026, 8, 31), date(2026, 9, 30), date(2026, 10, 23)},
        )

    def test_future_dates_are_kept(self):
        today = date(2026, 11, 22)
        roles = select_retained_dates([today, today + timedelta(days=3), date(2020, 1, 2)], today)
        self.assertEqual(roles[today], "daily")
        self.assertEqual(roles[today + timedelta(days=3)], "daily")
        self.assertEqual(roles[date(2020, 1, 2)], "monthly")

    def test_apply_retention_deletes_only_expired_snapshots(self):
        import tempfile

        today = date(2026, 11, 22)
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            keep_note = directory / "keep.txt"
            keep_note.write_text("leave me\n", encoding="utf-8")
            old = directory / "2020-01-15.json.gz"
            older = directory / "2020-01-02.json.gz"
            recent = directory / "2026-11-22.json.gz"
            for path in (old, older, recent):
                path.write_bytes(b"gzip-placeholder")
            removed = apply_retention(directory, today, daily=30)
            self.assertEqual({path.name for path in removed}, {"2020-01-02.json.gz"})
            self.assertTrue(old.exists())
            self.assertTrue(recent.exists())
            self.assertTrue(keep_note.exists())
            self.assertFalse(older.exists())

    def test_gzip_is_deterministic(self):
        self.assertEqual(gzip_bytes(b"textweb"), gzip_bytes(b"textweb"))


if __name__ == "__main__":
    unittest.main()
