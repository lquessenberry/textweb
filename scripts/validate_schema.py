#!/usr/bin/env python3
"""Validate textweb JSON files against data/schema and derived checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from common import (
    LICENSE,
    ROOT,
    SCHEMA_VERSION,
    SOURCE,
    build_status,
    checksum,
    dump_json,
    iter_resources,
    load_json,
    tally,
)
from snapshots import SNAPSHOT_NAME, load_snapshot

SCHEMA_FILES = {
    "sites": "sites.schema.json",
    "catalog": "catalog.schema.json",
    "status": "status.schema.json",
    "snapshot": "snapshot.schema.json",
    "snapshot-index": "snapshot-index.schema.json",
}


def _schema_errors(instance: object, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema)
    found = sorted(validator.iter_errors(instance), key=lambda err: list(err.absolute_path))
    messages = []
    for err in found:
        loc = "/".join(str(part) for part in err.absolute_path) or "(root)"
        messages.append(f"{loc}: {err.message}")
    return messages


def _load_schema(schema_dir: Path, name: str) -> dict:
    return load_json(schema_dir / SCHEMA_FILES[name])


def _checksum_errors(label: str, payload: object, checksum_value: str) -> list[str]:
    if checksum_value != checksum(payload):
        return [f"{label}: checksum mismatch"]
    return []


def validate_root(
    root: Path,
    *,
    schema_dir: Path | None = None,
    require_api: bool = True,
    require_snapshots: bool = True,
) -> list[str]:
    schema_dir = schema_dir or root / "data" / "schema"
    errors: list[str] = []
    sites_path = root / "data" / "sites.json"
    catalog_path = root / "data" / "catalog-250.json"
    if not sites_path.exists():
        return ["data/sites.json is missing"]
    if not catalog_path.exists():
        return ["data/catalog-250.json is missing"]

    sites = load_json(sites_path)
    catalog = load_json(catalog_path)
    sites_schema = _load_schema(schema_dir, "sites")
    catalog_schema = _load_schema(schema_dir, "catalog")
    for message in _schema_errors(sites, sites_schema):
        errors.append(f"data/sites.json {message}")
    for message in _schema_errors(catalog, catalog_schema):
        errors.append(f"data/catalog-250.json {message}")

    for label, document, records in (
        ("data/sites.json", sites, sites.get("sites", [])),
        (
            "data/catalog-250.json",
            catalog,
            catalog.get("sections", []),
        ),
    ):
        if document.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label}: schema_version is not {SCHEMA_VERSION}")
        if document.get("source") != SOURCE:
            errors.append(f"{label}: source is not the textweb repository")
        if document.get("license") != LICENSE:
            errors.append(f"{label}: license is not {LICENSE}")
    errors.extend(_checksum_errors("data/sites.json", sites.get("sites", []), sites.get("checksum")))
    errors.extend(
        _checksum_errors("data/catalog-250.json", catalog.get("sections", []), catalog.get("checksum"))
    )
    try:
        expected_site_counts = tally(sites.get("sites", []))
    except ValueError as exc:
        errors.append(f"data/sites.json: {exc}")
    else:
        if sites.get("counts") != expected_site_counts:
            errors.append("data/sites.json: counts do not match sites")
    catalog_resources = [resource for _section, resource in iter_resources(catalog)]
    try:
        expected_catalog_counts = tally(catalog_resources)
    except ValueError as exc:
        errors.append(f"data/catalog-250.json resources: {exc}")
    else:
        if catalog.get("counts") != expected_catalog_counts:
            errors.append("data/catalog-250.json: counts do not match resources")

    api = root / "api" / "v1"
    api_sites = api / "sites.json"
    api_catalog = api / "catalog.json"
    api_status = api / "status.json"
    if require_api:
        for path in (api_sites, api_catalog, api_status):
            if not path.exists():
                errors.append(f"{path.relative_to(root).as_posix()} is missing")
    if api_sites.exists() and api_sites.read_text(encoding="utf-8") != sites_path.read_text(encoding="utf-8"):
        errors.append("api/v1/sites.json does not match data/sites.json")
    if api_catalog.exists() and api_catalog.read_text(encoding="utf-8") != catalog_path.read_text(encoding="utf-8"):
        errors.append("api/v1/catalog.json does not match data/catalog-250.json")
    if api_status.exists():
        expected_status = dump_json(build_status(sites, catalog))
        if api_status.read_text(encoding="utf-8") != expected_status:
            errors.append("api/v1/status.json does not match the data files")
        else:
            status_schema = _load_schema(schema_dir, "status")
            status = load_json(api_status)
            for message in _schema_errors(status, status_schema):
                errors.append(f"api/v1/status.json {message}")

    snapshot_dir = root / "data" / "snapshots"
    index_path = snapshot_dir / "index.json"
    api_index = api / "snapshots" / "index.json"
    if require_snapshots and not index_path.exists():
        errors.append("data/snapshots/index.json is missing")
    if index_path.exists():
        index = load_json(index_path)
        index_schema = _load_schema(schema_dir, "snapshot-index")
        for message in _schema_errors(index, index_schema):
            errors.append(f"data/snapshots/index.json {message}")
        if api_index.exists() and api_index.read_bytes() != index_path.read_bytes():
            errors.append("api/v1/snapshots/index.json does not match data/snapshots/index.json")
        elif require_api and not api_index.exists():
            errors.append("api/v1/snapshots/index.json is missing")
        snapshot_schema = _load_schema(schema_dir, "snapshot")
        listed = {}
        for entry in index.get("snapshots", []):
            listed[entry.get("file")] = entry
            rel = entry.get("file")
            if rel and not (root / rel).exists():
                errors.append(f"{rel} is listed but missing")
        for path in sorted(snapshot_dir.glob("*.json.gz")):
            if not SNAPSHOT_NAME.match(path.name):
                continue
            rel = f"data/snapshots/{path.name}"
            blob = path.read_bytes()
            entry = listed.get(rel)
            if listed and entry is None:
                errors.append(f"{rel} is not listed in the snapshot index")
            if entry is not None:
                digest = "sha256:" + hashlib.sha256(blob).hexdigest()
                if entry.get("sha256") != digest:
                    errors.append(f"{rel}: index sha256 mismatch")
                if entry.get("bytes") != len(blob):
                    errors.append(f"{rel}: index size mismatch")
            try:
                payload = load_snapshot(path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{rel}: {exc}")
                continue
            for message in _schema_errors(payload, snapshot_schema):
                errors.append(f"{rel} {message}")
            expected = checksum({"catalog": payload.get("catalog"), "sites": payload.get("sites")})
            if payload.get("checksum") != expected:
                errors.append(f"{rel}: checksum mismatch")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate textweb data files")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = validate_root(args.root)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("schemas ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
