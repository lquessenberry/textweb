#!/usr/bin/env python3
"""Deterministic JSON, provenance, and checksum helpers for textweb.

Collection files carry the metadata described in docs/COMMONS.md:
schema_version, generated_at, source, license, counts, and a checksum.
The checksum is sha256 of the canonical JSON of the records only
(the sites array, or the catalog sections array). Envelope timestamps
are not part of the hash, so a same-day rerun with the same observations
does not churn the checksum.

`name` is the document title. `content_hash` stays null until a body is
stored; the nightly health check does not download page bodies.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.0.0"
SOURCE = "https://github.com/lquessenberry/textweb"
LICENSE = "MIT"
USER_AGENT = (
    "textweb-check/1.0 (+https://github.com/lquessenberry/textweb; nightly health check)"
)

ROOT = Path(__file__).resolve().parent.parent

SITE_FILE_KEYS = [
    "version",
    "schema_version",
    "updated",
    "generated_at",
    "description",
    "source",
    "license",
    "counts",
    "checksum",
    "sites",
]

CATALOG_FILE_KEYS = [
    "version",
    "schema_version",
    "updated",
    "generated_at",
    "description",
    "source",
    "license",
    "counts",
    "checksum",
    "tiers",
    "sections",
    "notes",
]

# Site objects already use name, url, category, description, text_friendly, tags.
# Catalog resources already use name, url, tier, tags. Status fields are appended.
RECORD_KEYS = [
    "name",
    "url",
    "category",
    "description",
    "text_friendly",
    "tier",
    "tags",
    "status",
    "last_checked",
    "http_status",
    "health",
    "fetched_at",
    "media_type",
    "mime_type",
    "size_bytes",
    "license",
    "source",
    "content_hash",
    "snapshot",
    "peer_votes",
]

SECTION_KEYS = ["name", "range", "resources"]
COUNT_KEYS = ["total", "up", "down", "unchecked", "skipped"]

STATUS_FILE_KEYS = [
    "schema_version",
    "generated_at",
    "source",
    "license",
    "last_run",
    "counts",
    "checksums",
]


def as_utc(when: datetime) -> datetime:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).replace(microsecond=0)


def utc_now() -> datetime:
    return as_utc(datetime.now(timezone.utc))


def format_stamp(when: datetime) -> str:
    return as_utc(when).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_date(when: datetime) -> str:
    return as_utc(when).strftime("%Y-%m-%d")


def order_obj(obj: Mapping[str, Any], preferred: Iterable[str]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in preferred:
        if key in obj:
            ordered[key] = obj[key]
    for key, value in obj.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def checksum(obj: Any) -> str:
    digest = hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_bytes(path: Path, blob: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(blob)
    temporary.replace(path)


def write_json(path: Path, obj: Any) -> None:
    write_text(path, dump_json(obj))


def host_of(url: str) -> str | None:
    from urllib.parse import urlparse

    return urlparse(url).hostname or None


STATUS_TO_COUNT = {
    "ok": "up",
    "down": "down",
    "unchecked": "unchecked",
    "skipped": "skipped",
}


def tally(records: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {key: 0 for key in COUNT_KEYS}
    for record in records:
        counts["total"] += 1
        status = record.get("status") or "unchecked"
        bucket = STATUS_TO_COUNT.get(status)
        if bucket is None:
            raise ValueError(f"unknown status {status!r}")
        counts[bucket] += 1
    return counts


def iter_resources(catalog: Mapping[str, Any]):
    for section in catalog.get("sections", []):
        for resource in section.get("resources", []):
            yield section, resource


def blank_status() -> dict[str, Any]:
    return {
        "status": "unchecked",
        "last_checked": None,
        "http_status": None,
        "health": "unchecked",
        "fetched_at": None,
        "media_type": None,
        "mime_type": None,
        "size_bytes": None,
        "license": "unknown",
        "source": None,
        "content_hash": None,
        "snapshot": None,
        "peer_votes": 0,
    }


def apply_defaults(record: Mapping[str, Any]) -> dict[str, Any]:
    """Add provenance fields without dropping or reordering curated values."""
    merged = blank_status()
    merged.update(record)
    if not merged.get("license"):
        merged["license"] = "unknown"
    if merged.get("peer_votes") is None:
        merged["peer_votes"] = 0
    if not merged.get("source"):
        merged["source"] = host_of(str(merged.get("url") or ""))
    if not merged.get("status"):
        merged["status"] = "unchecked"
    if not merged.get("health"):
        merged["health"] = "unchecked"
    return order_obj(merged, RECORD_KEYS)


def is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Fill missing provenance. Non-HTTP URLs are classified skipped, not probed."""
    new = apply_defaults(record)
    url = str(new.get("url") or "")
    if not is_http_url(url) and new.get("status") == "unchecked":
        new["status"] = "skipped"
        new["health"] = "unchecked"
    return order_obj(new, RECORD_KEYS)


def merge_probe(
    record: Mapping[str, Any],
    probe: Mapping[str, Any],
    *,
    today: str,
    fetched_at: str,
    snapshot_path: str | None,
) -> tuple[dict[str, Any], bool]:
    """Apply one observation.

    A same-day rerun that sees the same status, HTTP code, media type, and
    size leaves fetched_at and snapshot untouched so the file stays quiet.
    """
    base = apply_defaults(record)
    updated = dict(base)
    observed = {
        "status": probe.get("status") or "down",
        "health": probe.get("health") or "broken",
        "http_status": probe.get("http_status"),
        "media_type": probe.get("media_type"),
        "mime_type": probe.get("mime_type"),
        "size_bytes": probe.get("size_bytes"),
        "last_checked": today,
    }
    observation_changed = any(base.get(key) != value for key, value in observed.items())
    updated.update(observed)
    if probe.get("content_hash"):
        if base.get("content_hash") != probe["content_hash"]:
            observation_changed = True
        updated["content_hash"] = probe["content_hash"]
    if observation_changed:
        updated["fetched_at"] = fetched_at
        if snapshot_path:
            updated["snapshot"] = snapshot_path
    new = order_obj(updated, RECORD_KEYS)
    changed = canonical_json(record) != canonical_json(new)
    return new, changed


def envelope_stamps(
    original: Mapping[str, Any],
    records_changed: bool,
    now_stamp: str,
    today: str,
) -> tuple[str, str]:
    if records_changed or not original.get("generated_at"):
        return now_stamp, today
    updated = original.get("updated") or today
    return str(original["generated_at"]), str(updated)


def finish_sites(
    original: Mapping[str, Any],
    records: list[dict[str, Any]],
    generated_at: str,
    updated: str,
) -> dict[str, Any]:
    obj: dict[str, Any] = {
        "version": original.get("version", "0.2.0"),
        "schema_version": SCHEMA_VERSION,
        "updated": updated,
        "generated_at": generated_at,
        "description": original.get("description", ""),
        "source": SOURCE,
        "license": LICENSE,
        "counts": tally(records),
        "checksum": checksum(records),
        "sites": records,
    }
    for key, value in original.items():
        if key not in obj:
            obj[key] = value
    return order_obj(obj, SITE_FILE_KEYS)


def finish_catalog(
    original: Mapping[str, Any],
    sections: list[dict[str, Any]],
    generated_at: str,
    updated: str,
) -> dict[str, Any]:
    resources = [resource for section in sections for resource in section.get("resources", [])]
    notes = original["notes"] if "notes" in original else ""
    obj: dict[str, Any] = {
        "version": original.get("version", "0.1.0"),
        "schema_version": SCHEMA_VERSION,
        "updated": updated,
        "generated_at": generated_at,
        "description": original.get("description", ""),
        "source": SOURCE,
        "license": LICENSE,
        "counts": tally(resources),
        "checksum": checksum(sections),
        "tiers": original.get("tiers", {}),
        "sections": sections,
        "notes": notes,
    }
    for key, value in original.items():
        if key not in obj:
            obj[key] = value
    return order_obj(obj, CATALOG_FILE_KEYS)


def later_stamp(*stamps: str | None) -> str | None:
    values = [stamp for stamp in stamps if stamp]
    if not values:
        return None
    return max(values)


def build_status(sites: Mapping[str, Any], catalog: Mapping[str, Any]) -> dict[str, Any]:
    last_run = later_stamp(sites.get("generated_at"), catalog.get("generated_at"))
    return order_obj(
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": last_run,
            "source": SOURCE,
            "license": LICENSE,
            "last_run": last_run,
            "counts": {
                "sites": sites.get("counts"),
                "catalog": catalog.get("counts"),
            },
            "checksums": {
                "sites": sites.get("checksum"),
                "catalog": catalog.get("checksum"),
            },
        },
        STATUS_FILE_KEYS,
    )


def format_counts(counts: Mapping[str, Any] | None) -> str:
    data = counts or {}
    return " ".join(f"{key}={data.get(key, 0)}" for key in COUNT_KEYS)


def one_line(value: Any) -> str:
    return " ".join(str(value).split())


def collect_urls(sites: Mapping[str, Any], catalog: Mapping[str, Any]) -> list[str]:
    urls: list[str] = []
    for record in sites.get("sites", []):
        urls.append(str(record.get("url") or ""))
    for _section, resource in iter_resources(catalog):
        urls.append(str(resource.get("url") or ""))
    return urls
