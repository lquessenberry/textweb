#!/usr/bin/env python3
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assemble_site import assemble  # noqa: E402
from check_sites import down_result  # noqa: E402
from common import load_json, write_json  # noqa: E402
from generate_exports import exports_match  # noqa: E402
from nightly import run  # noqa: E402
from validate_schema import validate_root  # noqa: E402

NOW = datetime(2026, 11, 22, 4, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)


def ok_probe(url, timeout):
    return {
        "status": "ok",
        "health": "verified",
        "http_status": 200,
        "media_type": "text/html",
        "mime_type": "text/html",
        "size_bytes": 20,
    }


def base_catalog(resources):
    return {
        "version": "0.1.0",
        "updated": "2026-11-21",
        "description": "fixture catalog",
        "tiers": {"1": "mirror fully"},
        "sections": [
            {"name": "News", "range": "1-2", "resources": resources},
        ],
        "notes": "keep me",
    }


def base_sites(records):
    return {
        "version": "0.2.0",
        "updated": "2026-11-21",
        "description": "fixture sites",
        "sites": records,
    }


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "data" / "schema", self.root / "data" / "schema")

    def tearDown(self):
        self.tmp.cleanup()

    def write_fixture(self, sites, catalog):
        write_json(self.root / "data" / "sites.json", sites)
        write_json(self.root / "data" / "catalog-250.json", catalog)

    def test_sample_check_updates_shared_url_once_and_is_idempotent(self):
        calls = []

        def probe(url, timeout):
            calls.append(url)
            return ok_probe(url, timeout)

        self.write_fixture(
            base_sites(
                [
                    {
                        "name": "Alpha",
                        "url": "https://a.example/",
                        "category": "directory",
                        "description": "first",
                        "text_friendly": True,
                        "tags": ["a", "b"],
                    },
                    {"name": "Floodgap", "url": "gopher://gopher.floodgap.com/", "category": "gopher", "description": "gopher", "text_friendly": True, "tags": ["gopher"]},
                ]
            ),
            base_catalog(
                [
                    {"name": "Alpha", "url": "https://a.example/", "tier": 1, "tags": ["news"]},
                    {"name": "Beta", "url": "https://b.example/", "tier": 2},
                ]
            ),
        )
        code = run(self.root, mode="network", now=NOW, limit=1, workers=1, pause=0, probe=probe)
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["https://a.example/"])
        sites = load_json(self.root / "data" / "sites.json")
        catalog = load_json(self.root / "data" / "catalog-250.json")
        alpha = sites["sites"][0]
        self.assertEqual(alpha["tags"], ["a", "b"])
        self.assertEqual(alpha["description"], "first")
        self.assertEqual(alpha["status"], "ok")
        self.assertEqual(alpha["health"], "verified")
        self.assertEqual(alpha["source"], "a.example")
        self.assertEqual(alpha["license"], "unknown")
        self.assertEqual(alpha["peer_votes"], 0)
        self.assertIsNone(alpha["content_hash"])
        self.assertEqual(alpha["snapshot"], "data/snapshots/2026-11-22.json.gz")
        self.assertEqual(sites["sites"][1]["status"], "skipped")
        self.assertEqual(sites["license"], "MIT")
        self.assertEqual(sites["schema_version"], "1.0.0")
        beta = catalog["sections"][0]["resources"][1]
        self.assertEqual(beta["status"], "unchecked")
        self.assertIsNone(beta["last_checked"])
        self.assertEqual(beta["tier"], 2)
        self.assertEqual(catalog["notes"], "keep me")
        self.assertEqual(catalog["tiers"]["1"], "mirror fully")
        self.assertTrue((self.root / "exports" / "sites.txt").exists())
        self.assertTrue((self.root / "exports" / "index.gmi").exists())
        self.assertTrue((self.root / "exports" / "gophermap").exists())
        self.assertEqual(
            (self.root / "api" / "v1" / "sites.json").read_bytes(),
            (self.root / "data" / "sites.json").read_bytes(),
        )
        status = load_json(self.root / "api" / "v1" / "status.json")
        self.assertEqual(status["counts"]["sites"]["up"], 1)
        self.assertEqual(status["counts"]["sites"]["skipped"], 1)
        self.assertEqual(status["last_run"], "2026-11-22T04:00:00Z")
        index = load_json(self.root / "data" / "snapshots" / "index.json")
        self.assertEqual(index["snapshots"][0]["role"], "daily")
        self.assertEqual(index["snapshots"][0]["href"], "/data/snapshots/2026-11-22.json.gz")

        first_sites = (self.root / "data" / "sites.json").read_bytes()
        first_catalog = (self.root / "data" / "catalog-250.json").read_bytes()
        first_export = (self.root / "exports" / "sites.txt").read_bytes()
        again = run(self.root, mode="network", now=NOW, limit=1, workers=1, pause=0, probe=probe)
        self.assertEqual(again, 0)
        self.assertEqual((self.root / "data" / "sites.json").read_bytes(), first_sites)
        self.assertEqual((self.root / "data" / "catalog-250.json").read_bytes(), first_catalog)
        self.assertEqual((self.root / "exports" / "sites.txt").read_bytes(), first_export)
        self.assertEqual(run(self.root, mode="dry-run"), 0)

        next_day = run(self.root, mode="network", now=LATER, limit=1, workers=1, pause=0, probe=probe)
        self.assertEqual(next_day, 0)
        refreshed = load_json(self.root / "data" / "sites.json")
        self.assertEqual(refreshed["sites"][0]["last_checked"], "2026-11-23")
        self.assertEqual(refreshed["sites"][0]["fetched_at"], "2026-11-23T04:00:00Z")
        self.assertEqual(refreshed["generated_at"], "2026-11-23T04:00:00Z")
        self.assertIsNone(refreshed["sites"][0]["content_hash"])

    def test_full_outage_does_not_write(self):
        sites = base_sites(
            [
                {"name": f"H{i}", "url": f"https://h{i}.example/", "category": "news", "description": "x", "text_friendly": True, "tags": ["n"]}
                for i in range(5)
            ]
        )
        catalog = base_catalog([{"name": "H0", "url": "https://h0.example/", "tier": 1}])
        self.write_fixture(sites, catalog)
        before = (self.root / "data" / "sites.json").read_bytes()
        code = run(
            self.root,
            mode="network",
            now=NOW,
            workers=1,
            pause=0,
            probe=lambda url, timeout: down_result(),
        )
        self.assertEqual(code, 2)
        self.assertEqual((self.root / "data" / "sites.json").read_bytes(), before)
        self.assertFalse((self.root / "api").exists())
        self.assertFalse((self.root / "data" / "snapshots").exists())

    def test_no_network_preserves_a_hand_edit(self):
        self.write_fixture(
            base_sites(
                [
                    {"name": "Alpha", "url": "https://a.example/", "category": "directory", "description": "first", "text_friendly": True, "tags": ["a"]},
                ]
            ),
            base_catalog([{"name": "Alpha", "url": "https://a.example/", "tier": 1, "tags": ["news"]}]),
        )
        self.assertEqual(run(self.root, mode="no-network", now=NOW), 0)
        sites = load_json(self.root / "data" / "sites.json")
        sites["sites"][0]["description"] = "edited by hand"
        write_json(self.root / "data" / "sites.json", sites)
        self.assertEqual(run(self.root, mode="no-network", now=LATER), 0)
        rewritten = load_json(self.root / "data" / "sites.json")
        self.assertEqual(rewritten["sites"][0]["description"], "edited by hand")
        self.assertEqual(rewritten["sites"][0]["status"], "unchecked")
        catalog = load_json(self.root / "data" / "catalog-250.json")
        self.assertEqual(validate_root(self.root, require_snapshots=False), [])
        self.assertEqual(exports_match(self.root, rewritten, catalog), [])

    def test_assemble_copies_api_and_index(self):
        site = self.root / "mini"
        (site / "api" / "v1").mkdir(parents=True)
        (site / "api" / "v1" / "status.json").write_text("{}\n", encoding="utf-8")
        (site / "exports").mkdir()
        (site / "exports" / "sites.txt").write_text("hello\n", encoding="utf-8")
        (site / "index.html").write_text("<p>hi</p>\n", encoding="utf-8")
        out = self.root / "out"
        assemble(site, out)
        self.assertEqual((out / "api" / "v1" / "status.json").read_text(encoding="utf-8"), "{}\n")
        self.assertEqual((out / "exports" / "sites.txt").read_text(encoding="utf-8"), "hello\n")
        self.assertTrue((out / "index.html").exists())


class LiveCuratedFieldsTest(unittest.TestCase):
    def test_no_network_keeps_curated_catalog_and_sites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "data", root / "data")
            before_sites = load_json(root / "data" / "sites.json")
            before_catalog = load_json(root / "data" / "catalog-250.json")
            snapshot_dir = root / "data" / "snapshots"
            before_snapshots = {}
            if snapshot_dir.exists():
                before_snapshots = {
                    path.name: path.read_bytes() for path in snapshot_dir.iterdir() if path.is_file()
                }
            code = run(root, mode="no-network", now=NOW)
            self.assertEqual(code, 0)
            after_sites = load_json(root / "data" / "sites.json")
            after_catalog = load_json(root / "data" / "catalog-250.json")
            self.assertEqual(_project_sites(before_sites), _project_sites(after_sites))
            self.assertEqual(_project_catalog(before_catalog), _project_catalog(after_catalog))
            if "schema_version" in before_sites:
                self.assertEqual(
                    (root / "data" / "sites.json").read_bytes(),
                    (ROOT / "data" / "sites.json").read_bytes(),
                )
                self.assertEqual(
                    (root / "data" / "catalog-250.json").read_bytes(),
                    (ROOT / "data" / "catalog-250.json").read_bytes(),
                )
            if snapshot_dir.exists():
                after_snapshots = {
                    path.name: path.read_bytes() for path in snapshot_dir.iterdir() if path.is_file()
                }
                self.assertEqual(before_snapshots, after_snapshots)


def _project_sites(data):
    keys = ["name", "url", "category", "description", "text_friendly", "tags"]
    return [{key: site[key] for key in keys if key in site} for site in data["sites"]]


def _project_catalog(data):
    sections = []
    for section in data["sections"]:
        resources = []
        for resource in section["resources"]:
            resources.append({key: resource[key] for key in ("name", "url", "tier", "tags") if key in resource})
        sections.append({"name": section.get("name"), "range": section.get("range"), "resources": resources})
    return {
        "version": data.get("version"),
        "description": data.get("description"),
        "tiers": data.get("tiers"),
        "notes": data.get("notes"),
        "sections": sections,
    }


if __name__ == "__main__":
    unittest.main()
