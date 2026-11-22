#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import checksum, order_obj, tally  # noqa: E402


class OrderAndChecksumTest(unittest.TestCase):
    def test_order_keeps_known_keys_and_extras(self):
        ordered = order_obj({"b": 1, "extra": 3, "a": 2}, ["a", "b"])
        self.assertEqual(list(ordered), ["a", "b", "extra"])

    def test_checksum_ignores_key_order(self):
        self.assertEqual(checksum({"b": 1, "a": 2}), checksum({"a": 2, "b": 1}))

    def test_checksum_changes_when_values_change(self):
        self.assertNotEqual(checksum([{"url": "https://a.example"}]), checksum([{"url": "https://b.example"}]))

    def test_tally_counts_each_status(self):
        counts = tally(
            [
                {"status": "ok"},
                {"status": "ok"},
                {"status": "down"},
                {"status": "skipped"},
                {},
            ]
        )
        self.assertEqual(counts, {"total": 5, "up": 2, "down": 1, "unchecked": 1, "skipped": 1})


if __name__ == "__main__":
    unittest.main()
