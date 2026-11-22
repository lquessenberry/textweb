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

Future work: SQLite FTS5 index, snapshot storage, peer comparison.
