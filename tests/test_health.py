#!/usr/bin/env python3
import socket
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_sites import check_urls, outage_suspected, probe_url, split_content_type  # noqa: E402


class Headers(dict):
    pass


class FakeResp:
    def __init__(self, status, headers, body=b""):
        self.status = status
        self.headers = headers
        self._body = body

    def read(self, n=-1):
        if n is None or n < 0:
            return self._body
        return self._body[:n]

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ProbeTest(unittest.TestCase):
    def test_content_type_drops_parameters(self):
        self.assertEqual(split_content_type("Text/HTML; charset=UTF-8"), ("text/html", "text/html"))
        self.assertEqual(split_content_type(None), (None, None))

    def test_head_success(self):
        def fake_open(req, timeout):
            self.assertEqual(req.get_method(), "HEAD")
            self.assertIn("textweb-check/", req.get_header("User-agent"))
            return FakeResp(200, Headers({"Content-Type": "text/plain; charset=utf-8", "Content-Length": "4"}))

        with mock.patch("check_sites._open", fake_open):
            result = probe_url("https://example.com/index", timeout=3)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["health"], "verified")
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["mime_type"], "text/plain")
        self.assertEqual(result["size_bytes"], 4)

    def test_head_405_falls_back_to_one_get(self):
        calls = []

        def fake_open(req, timeout):
            calls.append(req.get_method())
            if req.get_method() == "HEAD":
                raise urllib.error.HTTPError(req.full_url, 405, "no", Headers({}), None)
            return FakeResp(200, Headers({"Content-Type": "text/html"}), b"hi")

        with mock.patch("check_sites._open", fake_open):
            result = probe_url("https://example.com/", timeout=3)
        self.assertEqual(calls, ["HEAD", "GET"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["http_status"], 200)

    def test_timeout_is_down_without_status_code(self):
        def fake_open(req, timeout):
            raise urllib.error.URLError(socket.timeout("timed out"))

        with mock.patch("check_sites._open", fake_open):
            result = probe_url("https://example.com/", timeout=3)
        self.assertEqual(result["status"], "down")
        self.assertEqual(result["health"], "broken")
        self.assertIsNone(result["http_status"])

    def test_gopher_is_not_requested(self):
        def fake_open(req, timeout):
            raise AssertionError("network")

        with mock.patch("check_sites._open", fake_open):
            result = probe_url("gopher://gopher.example/", timeout=3)
        self.assertEqual(result["status"], "skipped")

    def test_limit_and_dedupe(self):
        seen = []

        def fake_probe(url, timeout):
            seen.append(url)
            return {"status": "ok", "health": "verified", "http_status": 200, "media_type": None, "mime_type": None, "size_bytes": None}

        results = check_urls(
            [
                "https://a.example/",
                "gopher://gopher.example/",
                "https://a.example/",
                "https://b.example/",
                "https://c.example/",
            ],
            workers=2,
            limit=2,
            pause=0,
            probe=fake_probe,
        )
        self.assertEqual(seen, ["https://a.example/", "https://b.example/"])
        self.assertEqual(set(results), set(seen))

    def test_outage_guard_is_only_for_a_full_sample(self):
        downs = {"https://a.example/": {"status": "down"}}
        many = {f"https://h{i}.example/": {"status": "down"} for i in range(5)}
        mixed = dict(many)
        mixed["https://ok.example/"] = {"status": "ok"}
        self.assertFalse(outage_suspected(downs, full_run=True))
        self.assertFalse(outage_suspected(many, full_run=False))
        self.assertTrue(outage_suspected(many, full_run=True))
        self.assertFalse(outage_suspected(mixed, full_run=True))


if __name__ == "__main__":
    unittest.main()
