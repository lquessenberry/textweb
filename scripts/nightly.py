#!/usr/bin/env python3
"""Nightly textweb update.

Loads the curated index and catalog, probes HTTP(S) URLs, refreshes
provenance, writes a daily snapshot, and regenerates exports plus the
static API. `--dry-run` does not use the network and does not write.
`--no-network` rewrites checksums and exports after a local edit.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from check_sites import check_urls, outage_suspected, skipped_result
from common import (
    ROOT,
    SECTION_KEYS,
    build_status,
    canonical_json,
    collect_urls,
    envelope_stamps,
    finish_catalog,
    finish_sites,
    format_date,
    is_http_url,
    later_stamp,
    load_json,
    merge_probe,
    normalize_record,
    order_obj,
    utc_now,
    write_bytes,
    write_json,
    write_text,
)
from generate_exports import exports_match, write_exports
from snapshots import apply_retention, build_index, snapshot_file, write_snapshot
from validate_schema import validate_root


def update_record(
    record: dict,
    results: dict[str, dict],
    *,
    network: bool,
    today: str,
    fetched_at: str,
    snapshot_path: str | None,
) -> tuple[dict, bool]:
    url = str(record.get("url") or "")
    if is_http_url(url) and url in results:
        return merge_probe(
            record,
            results[url],
            today=today,
            fetched_at=fetched_at,
            snapshot_path=snapshot_path,
        )
    if network and not is_http_url(url):
        return merge_probe(
            record,
            skipped_result(),
            today=today,
            fetched_at=fetched_at,
            snapshot_path=snapshot_path,
        )
    new = normalize_record(record)
    changed = canonical_json(record) != canonical_json(new)
    return new, changed


def rebuild_sites(data: dict, results: dict, **kwargs) -> tuple[list[dict], bool]:
    changed = False
    records = []
    for record in data.get("sites", []):
        updated, record_changed = update_record(record, results, **kwargs)
        changed = changed or record_changed
        records.append(updated)
    return records, changed


def rebuild_catalog(data: dict, results: dict, **kwargs) -> tuple[list[dict], bool]:
    changed = False
    sections = []
    for section in data.get("sections", []):
        resources = []
        for record in section.get("resources", []):
            updated, record_changed = update_record(record, results, **kwargs)
            changed = changed or record_changed
            resources.append(updated)
        rebuilt = dict(section)
        rebuilt["resources"] = resources
        sections.append(order_obj(rebuilt, SECTION_KEYS))
    return sections, changed


def write_api(root: Path, sites: dict, catalog: dict, index_bytes: bytes | None) -> None:
    api = root / "api" / "v1"
    write_text(api / "sites.json", (root / "data" / "sites.json").read_text(encoding="utf-8"))
    write_text(api / "catalog.json", (root / "data" / "catalog-250.json").read_text(encoding="utf-8"))
    write_json(api / "status.json", build_status(sites, catalog))
    if index_bytes is not None:
        write_bytes(api / "snapshots" / "index.json", index_bytes)


def _print_downs(results: dict[str, dict]) -> None:
    for url in sorted(results):
        if results[url].get("status") != "ok":
            print(f"down {url} http_status={results[url].get('http_status')}", file=sys.stderr)


def _summary(mode: str, probed: int, sites: dict, catalog: dict) -> None:
    site_counts = sites["counts"]
    catalog_counts = catalog["counts"]
    print(
        f"{mode}: probed={probed} "
        f"sites total={site_counts['total']} up={site_counts['up']} down={site_counts['down']} "
        f"unchecked={site_counts['unchecked']} skipped={site_counts['skipped']} "
        f"catalog total={catalog_counts['total']} up={catalog_counts['up']} "
        f"down={catalog_counts['down']} unchecked={catalog_counts['unchecked']} "
        f"skipped={catalog_counts['skipped']}"
    )


def dry_run(root: Path) -> int:
    errors = validate_root(root)
    sites_path = root / "data" / "sites.json"
    catalog_path = root / "data" / "catalog-250.json"
    if sites_path.exists() and catalog_path.exists():
        sites = load_json(sites_path)
        catalog = load_json(catalog_path)
        errors.extend(exports_match(root, sites, catalog))
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    sites = load_json(sites_path)
    catalog = load_json(catalog_path)
    print(f"dry-run ok: sites={sites['counts']['total']} catalog={catalog['counts']['total']}")
    return 0


def run(
    root: Path,
    *,
    mode: str = "network",
    now: datetime | None = None,
    limit: int | None = None,
    workers: int = 4,
    timeout: int = 10,
    pause: float = 0.25,
    probe=None,
) -> int:
    if mode == "dry-run":
        return dry_run(root)
    if mode not in ("network", "no-network"):
        print(f"unknown mode {mode}", file=sys.stderr)
        return 1

    moment = utc_now() if now is None else now
    from common import as_utc, format_stamp

    moment = as_utc(moment)
    today = format_date(moment)
    fetched_at = format_stamp(moment)
    network = mode == "network"

    sites_path = root / "data" / "sites.json"
    catalog_path = root / "data" / "catalog-250.json"
    original_sites = load_json(sites_path)
    original_catalog = load_json(catalog_path)

    results: dict[str, dict] = {}
    if network:
        results = check_urls(
            collect_urls(original_sites, original_catalog),
            workers=workers,
            timeout=timeout,
            limit=limit,
            pause=pause,
            probe=probe,
        )
        if outage_suspected(results, full_run=limit is None):
            _print_downs(results)
            print(
                f"Refusing to update: all {len(results)} HTTP checks failed. "
                "Existing statuses were left unchanged so a runner outage cannot mark the catalog down.",
                file=sys.stderr,
            )
            return 2

    snapshot_path = snapshot_file(today) if network else None
    kwargs = {
        "network": network,
        "today": today,
        "fetched_at": fetched_at,
        "snapshot_path": snapshot_path,
    }
    site_records, sites_changed = rebuild_sites(original_sites, results, **kwargs)
    sections, catalog_changed = rebuild_catalog(original_catalog, results, **kwargs)
    sites_generated_at, sites_updated = envelope_stamps(
        original_sites, sites_changed, fetched_at, today
    )
    catalog_generated_at, catalog_updated = envelope_stamps(
        original_catalog, catalog_changed, fetched_at, today
    )
    sites = finish_sites(original_sites, site_records, sites_generated_at, sites_updated)
    catalog = finish_catalog(original_catalog, sections, catalog_generated_at, catalog_updated)

    index_bytes = None
    if network:
        published = later_stamp(sites["generated_at"], catalog["generated_at"]) or fetched_at
        write_snapshot(root, sites, catalog, when=moment, generated_at=published)
        snapshot_dir = root / "data" / "snapshots"
        apply_retention(snapshot_dir, moment.date())
        index = build_index(snapshot_dir, generated_at=published, today=moment.date())
        index_path = snapshot_dir / "index.json"
        write_json(index_path, index)
        index_bytes = index_path.read_bytes()
    else:
        index_path = root / "data" / "snapshots" / "index.json"
        if index_path.exists():
            index_bytes = index_path.read_bytes()

    write_json(sites_path, sites)
    write_json(catalog_path, catalog)
    write_exports(root, sites, catalog)
    write_api(root, sites, catalog, index_bytes)

    errors = validate_root(
        root,
        require_api=True,
        require_snapshots=network or (root / "data" / "snapshots" / "index.json").exists(),
    )
    errors.extend(exports_match(root, sites, catalog))
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    _summary(mode, len(results), sites, catalog)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update textweb data, snapshots, exports, and API")
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="No network and no writes; check exports and schemas")
    mode.add_argument("--no-network", action="store_true", help="Refresh metadata and exports without probing")
    parser.add_argument("--limit", type=int, default=None, help="Probe at most N unique HTTP(S) URLs")
    parser.add_argument("--workers", type=int, default=4, help="Maximum concurrent probes")
    parser.add_argument("--timeout", type=int, default=10, help="Per-request timeout in seconds")
    parser.add_argument("--pause", type=float, default=0.25, help="Seconds to wait before each probe")
    args = parser.parse_args(argv)
    if args.limit is not None and (args.dry_run or args.no_network):
        parser.error("--limit is only used when probing")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.timeout < 1:
        parser.error("--timeout must be >= 1")
    if args.pause < 0:
        parser.error("--pause must be >= 0")
    selected = "dry-run" if args.dry_run else "no-network" if args.no_network else "network"
    return run(
        args.root,
        mode=selected,
        limit=args.limit,
        workers=args.workers,
        timeout=args.timeout,
        pause=args.pause,
    )


if __name__ == "__main__":
    raise SystemExit(main())
