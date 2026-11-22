# Portable Knowledge Commons

Treat the textweb index as a self-healing, low-bandwidth knowledge commons rather than a simple list of links.

## Core principles
- Store source snapshots, not only live pages.
- Prefer RSS, Gemini, Gopher, and plain-text formats whenever available.
- Generate a common searchable index across news, reference works, directories, and archived material.
- Repair continuously: validate links, compare copies across peers, replace broken snapshots, and record provenance.
- Distribute updates among surviving nodes: each device can act as both client and lightweight cache.
- Expose everything through one character-oriented interface (Lynx, w3m, Links, or a custom terminal UI).

## Tiers
**Tier 1 — mirror fully** (public-domain, openly licensed, government, permissively licensed):
Wikipedia, Wiktionary, Project Gutenberg, Open Library, GNU manuals, RFCs, Python/Rust/Go docs, POSIX, Linux documentation, Debian package indexes, selected government datasets.

**Tier 2 — mirror metadata and excerpts**:
Major news RSS feeds, scientific feeds, aggregators, public-interest reporting.

**Tier 3 — retain links plus periodic snapshots**:
Directories, search engines, commercial publishers, sites with unstable or restrictive terms.

**Tier 4 — discover but do not automatically mirror**:
Social networks, video-heavy services, high-bandwidth sources.

## Document metadata schema
Each cached document carries a small metadata record:
```json
{
  "url": "https://example.org/article",
  "title": "Article title",
  "source": "publisher",
  "fetched_at": "2026-11-21T23:00:00Z",
  "content_hash": "sha256:...",
  "media_type": "text/html",
  "mime_type": "text/html",
  "size_bytes": 48213,
  "license": "unknown",
  "snapshot": "snapshots/2026/11/...",
  "health": "verified",
  "peer_votes": 3
}
```

## Repair loop
```
FETCH → PARSE → SANITIZE → EXTRACT → DEDUPLICATE → STORE
  → VERIFY LINKS → COMPARE PEERS → REPAIR → PUBLISH INDEX
```

Key design points:
- Prefer feeds: RSS/Atom provides clean text and much lower bandwidth.
- Extract before storage: Strip scripts, images, video, advertising, and navigation.
- Store several representations: original file, normalized plain text, and extracted links.
- Validate snapshots: compare content hashes with other repository nodes.
- Quarantine updates: A changed snapshot should not automatically replace a trusted copy.
- Track provenance: Preserve the source URL, retrieval time, and transformation history.
- Support partial repair: If a complete snapshot is unavailable, retain the last verified copy.
- Use a low-cost search index: SQLite FTS5 is a strong starting point.
- Expose RSS and JSON: Feed readers and scripts can consume the repository without a browser.
- Distribute selectively: Large archives should sync only to designated nodes rather than every low-power device.

## Important limitation
A fully self-contained mirror must account for copyright, robots directives, access controls, and updates that invalidate old versions. “Self-contained” is technically feasible for public-domain, openly licensed, government, and permissively licensed material. For copyrighted publications, a safer design is to retain metadata, summaries where licensed, and links to the canonical source.

## Starter catalog
See `data/catalog-250.json` for a structured version of the 250-resource starter list (news, aggregators, wikis, computing references, low-bandwidth tools, specialized public-interest resources).

This vision builds on the existing textweb index, Gemini/Gopher exports, Yggdrasil mesh, and IPFS content addressing.
