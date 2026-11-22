# Schema notes

## sites.json
Array of site objects with fields: name, url, category, description, text_friendly, tags, last_checked, status, etc.

## catalog-250.json
Tiered starter catalog for the knowledge commons vision. See docs/COMMONS.md.

## Document metadata (for future snapshots)
```json
{
  "url": "...",
  "title": "...",
  "source": "...",
  "fetched_at": "ISO8601",
  "content_hash": "sha256:...",
  "media_type": "text/html",
  "size_bytes": 0,
  "license": "unknown|public-domain|cc-by|...",
  "snapshot": "path/to/snapshot",
  "health": "verified|stale|broken",
  "peer_votes": 0
}
```

Future work: SQLite FTS5 index, full-text snapshot storage, peer comparison.

## Published snapshot metadata
The generator (`scripts/nightly.py`) writes these collection fields on `data/sites.json` and `data/catalog-250.json`:

| Field | Meaning |
| --- | --- |
| `schema_version` | Schema of this file (`1.0.0`). `version` stays the curated-list version. |
| `generated_at` | UTC time the records last changed (`YYYY-MM-DDTHH:MM:SSZ`). |
| `updated` | UTC date of that change. |
| `source` | `https://github.com/lquessenberry/textweb` |
| `license` | `MIT` for the index itself. |
| `counts` | `total`, `up`, `down`, `unchecked`, `skipped`. |
| `checksum` | `sha256:` plus the hex SHA-256 of the canonical JSON (sorted keys, no extra whitespace) of the `sites` array, or the catalog `sections` array. Envelope timestamps are not hashed. |

Each site and catalog resource also gets the document fields from the top of this file, mapped as follows:

- `name` is the title. It is not copied into a second `title` field.
- `source` is the URL host (the publisher we can name without guessing).
- `fetched_at` / `last_checked` record the last observation. A same-day rerun that sees the same result does not bump `fetched_at`.
- `content_hash` is null. The checker does not store response bodies, so it does not invent a content hash.
- `media_type` and `mime_type` are the lowercase Content-Type without parameters.
- `size_bytes` is Content-Length when the server sends it, otherwise null.
- `license` stays `unknown` unless someone set it on the record.
- `snapshot` is the repo path of the run that last observed the record, or null.
- `health` is `verified` (HTTP ok), `broken` (HTTP failed), or `unchecked` (not probed, including non-HTTP).
- `peer_votes` stays 0.
- `status` is the checker result: `ok`, `down`, `unchecked`, or `skipped`.

Non-HTTP URLs are `skipped` and are not requested. JSON Schema for the files is in `data/schema/` (`sites`, `catalog`, `status`, `snapshot`, `snapshot-index`).

Daily gzipped status snapshots live in `data/snapshots/YYYY-MM-DD.json.gz`. The index keeps the last 30 daily files and the latest file from each older month. See `api/v1/snapshots/index.json`.
