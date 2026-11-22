#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_exports import parse_gopher, render_gemini, render_gopher, render_html, render_text  # noqa: E402


def sample_sites():
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-11-22T04:00:00Z",
        "source": "https://github.com/lquessenberry/textweb",
        "license": "MIT",
        "checksum": "sha256:" + ("ab" * 32),
        "counts": {"total": 3, "up": 1, "down": 0, "unchecked": 1, "skipped": 1},
        "sites": [
            {
                "name": "<b>Example</b>",
                "url": 'https://example.com/?q="x"',
                "description": "a & b",
                "status": "ok",
                "last_checked": "2026-11-22",
            },
            {
                "name": "Floodgap Gopher",
                "url": "gopher://gopher.floodgap.com/",
                "description": "Gopher root",
                "status": "skipped",
                "last_checked": "2026-11-22",
            },
            {
                "name": "Later",
                "url": "https://later.example/path",
                "description": "",
                "status": "unchecked",
                "last_checked": None,
            },
        ],
    }


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.sites = sample_sites()
        self.catalog = {
            "checksum": "sha256:" + ("cd" * 32),
            "counts": {"total": 1, "up": 0, "down": 0, "unchecked": 1, "skipped": 0},
        }

    def test_every_export_lists_every_site_and_provenance(self):
        rendered = [
            render_text(self.sites, self.catalog),
            render_html(self.sites, self.catalog),
            render_gopher(self.sites, self.catalog),
            render_gemini(self.sites, self.catalog),
        ]
        for text in rendered:
            self.assertIn("schema_version: 1.0.0", text)
            self.assertIn("generated_at: 2026-11-22T04:00:00Z", text)
            self.assertIn("license: MIT", text)
            self.assertIn(self.sites["checksum"], text)
            self.assertIn("catalog_checksum:", text)
            self.assertIn("Example", text)
            self.assertIn("Floodgap Gopher", text)
            self.assertIn("Later", text)

    def test_html_escapes_names_and_urls(self):
        page = render_html(self.sites, self.catalog)
        self.assertIn("&lt;b&gt;Example&lt;/b&gt;", page)
        self.assertIn("a &amp; b", page)
        self.assertIn("https://example.com/?q=&quot;x&quot;", page)
        self.assertNotIn('href="https://example.com/?q="x""', page)

    def test_gopher_lines(self):
        text = render_gopher(self.sites, self.catalog)
        self.assertIn('h<b>Example</b>\tURL:https://example.com/?q="x"\t\t', text)
        self.assertIn("1Floodgap Gopher\t/\tgopher.floodgap.com\t70", text)

    def test_gopher_parser_reads_type_and_selector(self):
        item_type, selector, host, port = parse_gopher("gopher://gopher.example:7070/0/docs/readme.txt")
        self.assertEqual((item_type, selector, host, port), ("0", "/docs/readme.txt", "gopher.example", "7070"))

    def test_gemini_links(self):
        text = render_gemini(self.sites, self.catalog)
        self.assertIn('=> https://example.com/?q="x" <b>Example</b>', text)
        self.assertIn("=> gopher://gopher.floodgap.com/ Floodgap Gopher", text)
        self.assertIn("API: /api/v1/status.json", text)


if __name__ == "__main__":
    unittest.main()
