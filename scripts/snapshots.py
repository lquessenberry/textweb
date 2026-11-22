#!/usr/bin/env python3
"""Compact daily status snapshots and retention.

Snapshots live in the git tree (gzipped JSON, one UTC day per file) because
textweb is carried offline, pinned, and cloned. Actions artifacts expire and
are not in a clone. Each file stores status rows only, not page bodies.

Retention keeps every snapshot in the last `DAILY_KEEP` days (including today)
and, for older days, the latest snapshot in each calendar month.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from common import (
    LICENSE,
    SCHEMA_VERSION,
    SOURCE,
    canonical_json,
    checksum,
    format_date,
    order_obj,
    write_bytes,
)

DAILY_KEEP = 30
SNAPSHOT_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json\.gz$")
INDEX_KEYS = [
    "schema_version",
    "generated_at",
    "source",
    "license",
    "retention",
    "snapshots",
]
ENTRY_KEYS = ["date", "file", "href", "bytes", "sha256", "role", "counts"]
SNAPSHOT_KEYS = [
    "schema_version",
    "generated_at",
    "date",
    "source",
    "license",
    "counts",
    "checksum",
    "sites",
    "catalog",
]


def snapshot_file(day: str) -> str:
    return f"data/snapshots/{day}.json.gz"


def snapshot_href(day: str) -> str:
    return f"/{snapshot_file(day)}"


def gzip_bytes(data: bytes) -> bytes:
    """Gzip with a fixed header so the same payload always hashes the same."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0, compresslevel=9) as handle:
        handle.write(data)
    return buffer.getvalue()


def select_retained_dates(
    dates: list[date] | set[date],
    today: date,
    daily: int = DAILY_KEEP,
) -> dict[date, str]:
    """Map each kept date to `daily` or `monthly`."""
    if daily < 1:
        raise ValueError("daily must be >= 1")
    cutoff = today - timedelta(days=daily - 1)
    roles: dict[date, str] = {}
    monthly_best: dict[tuple[int, int], date] = {}
    for item in dates:
        if item >= cutoff:
            roles[item] = "daily"
            continue
        key = (item.year, item.month)
        current = monthly_best.get(key)
        if current is None or item > current:
            monthly_best[key] = item
    for item in monthly_best.values():
        roles[item] = "monthly"
    return roles


def _compact_row(record: Mapping[str, Any], *, section: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": record.get("name"),
        "url": record.get("url"),
        "status": record.get("status"),
        "health": record.get("health"),
    }
    if record.get("last_checked"):
        row["last_checked"] = record["last_checked"]
    if record.get("http_status") is not None:
        row["http_status"] = record["http_status"]
    if section is not None and record.get("tier") is not None:
        row["tier"] = record["tier"]
    if section is not None:
        row["section"] = section
    return row


def snapshot_payload(
    sites: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    generated_at: str,
    day: str,
) -> dict[str, Any]:
    site_rows = [_compact_row(record) for record in sites.get("sites", [])]
    catalog_rows = [
        _compact_row(resource, section=section.get("name"))
        for section in catalog.get("sections", [])
        for resource in section.get("resources", [])
    ]
    body = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "date": day,
        "source": SOURCE,
        "license": LICENSE,
        "counts": {
            "sites": sites.get("counts"),
            "catalog": catalog.get("counts"),
        },
        "checksum": checksum({"catalog": catalog_rows, "sites": site_rows}),
        "sites": site_rows,
        "catalog": catalog_rows,
    }
    return order_obj(body, SNAPSHOT_KEYS)


def write_snapshot(
    root: Path,
    sites: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    when: datetime,
    generated_at: str,
) -> Path:
    day = format_date(when)
    payload = snapshot_payload(sites, catalog, generated_at=generated_at, day=day)
    raw = canonical_json(payload).encode("utf-8")
    path = root / snapshot_file(day)
    write_bytes(path, gzip_bytes(raw))
    return path


def _dated_files(directory: Path) -> dict[date, Path]:
    found: dict[date, Path] = {}
    if not directory.exists():
        return found
    for path in directory.iterdir():
        if not path.is_file():
            continue
        match = SNAPSHOT_NAME.match(path.name)
        if not match:
            continue
        found[datetime.strptime(match.group(1), "%Y-%m-%d").date()] = path
    return found


def apply_retention(directory: Path, today: date, daily: int = DAILY_KEEP) -> list[Path]:
    """Delete daily snapshots outside the retention window. Other files stay."""
    dated = _dated_files(directory)
    roles = select_retained_dates(dated.keys(), today, daily)
    removed: list[Path] = []
    for item, path in dated.items():
        if item not in roles:
            path.unlink()
            removed.append(path)
    return removed


def build_index(directory: Path, *, generated_at: str, today: date) -> dict[str, Any]:
    dated = _dated_files(directory)
    roles = select_retained_dates(dated.keys(), today)
    entries = []
    for item in sorted(roles):
        path = dated[item]
        blob = path.read_bytes()
        payload = json.loads(gzip.decompress(blob))
        entries.append(
            order_obj(
                {
                    "date": item.isoformat(),
                    "file": snapshot_file(item.isoformat()),
                    "href": snapshot_href(item.isoformat()),
                    "bytes": len(blob),
                    "sha256": "sha256:" + hashlib.sha256(blob).hexdigest(),
                    "role": roles[item],
                    "counts": payload.get("counts"),
                },
                ENTRY_KEYS,
            )
        )
    return order_obj(
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "source": SOURCE,
            "license": LICENSE,
            "retention": {"daily": DAILY_KEEP, "monthly": True},
            "snapshots": entries,
        },
        INDEX_KEYS,
    )


def load_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(gzip.decompress(path.read_bytes()))
