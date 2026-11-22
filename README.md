# textweb

Curated, nightly-updated index of text-browser friendly, classic, and low-tech websites.

**Purpose**: Replenish the extremely fast, capable text-based internet for Lynx, Links, w3m, ELinks, BBS, telnet, Gopher, Gemini, and retro hardware.

## Goals
- Machine-readable index (JSON) that any project can consume
- Human-readable wiki (Markdown)
- Low-tech exports (plain text lists, Gopher maps, etc.)
- Nightly health checks and updates
- Easy contribution and integration

## Quick Start
- Browse the human-readable list: [wiki/sites.md](wiki/sites.md)
- Machine data: [data/sites.json](data/sites.json)
- Directories & discovery tools are included as first-class entries

## Formats
- `data/sites.json` — Canonical structured index
- `wiki/` — Markdown pages suitable for GitHub Wiki or static site generation
- `exports/` — Plain text, Gopher, and other low-tech formats (generated)

## Nightly Updates
A GitHub Action will eventually:
1. Validate URLs
2. Check HTTP status and basic text-browser friendliness
3. Update last_checked timestamps
4. Open PRs or commit updates for dead/changed links

See `.github/workflows/`.

## Contributing
PRs welcome. Add sites to `data/sites.json` following the schema, or open an issue.

## Related
- Bobcat, Greycoder, 1MB Club, Wiby, FrogFind, The Old Net, Protoweb

MIT License. Help rebuild the fast text web.
