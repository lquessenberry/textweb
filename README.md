# textweb

Curated, nightly-updated index of text-browser friendly, classic, Gemini, Gopher, and low-tech websites — evolving into a portable knowledge commons.

**Purpose**: Replenish the extremely fast, capable text-based internet for Lynx, Links, w3m, ELinks, BBS, telnet, Gopher, Gemini, and retro hardware — including low-bandwidth, mesh, and offline delivery.

## Quick links
- **Knowledge commons vision**: [docs/COMMONS.md](docs/COMMONS.md)
- Starter catalog of ~250 resources: [data/catalog-250.json](data/catalog-250.json)
- Human wiki: [wiki/sites.md](wiki/sites.md)
- Machine data: [data/sites.json](data/sites.json) — raw: https://raw.githubusercontent.com/lquessenberry/textweb/main/data/sites.json
- Static page: [index.html](index.html)
- JSON API: [api/v1/status.json](api/v1/status.json) (sites, catalog, status, snapshots)
- Exports: [exports/](exports/) (plain text, HTML, Gopher, Gemini)
- Gemini: [gemini/](gemini/)
- Gopher: [gopher/](gopher/)
- Delivery notes (Yggdrasil, IPFS, ad-hoc WiFi): [docs/DELIVERY.md](docs/DELIVERY.md)
- Yggdrasil details: [docs/YGGDRASIL.md](docs/YGGDRASIL.md)
- IPFS details: [docs/IPFS.md](docs/IPFS.md)

## Nightly updates
`.github/workflows/nightly-check.yml` runs at 04:00 UTC and on `workflow_dispatch`. It health-checks every HTTP(S) URL in `data/sites.json` and `data/catalog-250.json` (HEAD, one short GET only if HEAD is rejected), then refreshes status fields, a daily snapshot, the exports, and `api/v1/`. It commits with the workflow `GITHUB_TOKEN` only when the tree changed. Runs do not overlap.

The checker uses at most 4 concurrent requests, a 10 second timeout, a short pause, and one request per URL. User-Agent: `textweb-check/1.0 (+https://github.com/lquessenberry/textweb; nightly health check)`. Gopher and other non-HTTP URLs are marked `skipped` and are not contacted. If a full run cannot reach any site, it leaves the previous statuses in place.

## JSON API
Static files, suitable for GitHub Pages, a local web server, or a clone:

| Path | What it is |
| --- | --- |
| `/api/v1/sites.json` | Curated site index, same bytes as `data/sites.json` |
| `/api/v1/catalog.json` | Tiered starter catalog, same bytes as `data/catalog-250.json` |
| `/api/v1/status.json` | Up, down, unchecked, and skipped counts, plus the last run time and checksums |
| `/api/v1/snapshots/index.json` | Snapshot list (date, size, sha256, daily or monthly role) |
| `/data/snapshots/YYYY-MM-DD.json.gz` | Compact status snapshot for that UTC day |

Each data file records `schema_version`, `generated_at`, `source`, `license`, `counts`, and a `checksum` (`sha256:` of the canonical record JSON). Per-record fields follow `docs/COMMONS.md`: `source`, `fetched_at`, `content_hash`, `media_type`, `mime_type`, `size_bytes`, `license`, `snapshot`, `health`, and `peer_votes`. `name` is the title. `content_hash` stays null because the health check does not download page bodies. `peer_votes` stays 0 until peers exist. Record `license` stays `unknown` unless a curator set one. The collection license is MIT, matching this repository.

Snapshots are stored in git, gzipped, rather than as Actions artifacts. A clone, an IPFS pin, or a USB copy should still contain history. Artifacts expire and are not in the tree. Retention keeps the last 30 daily files and the latest snapshot of each older month. The rows are status only, so the files stay small.

JSON Schema for these files lives in `data/schema/` and is checked in CI.

## Run locally
```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 scripts/validate_schema.py
python3 scripts/nightly.py --dry-run          # no network, no writes
python3 scripts/nightly.py --no-network       # refresh checksums and exports after an edit
python3 scripts/nightly.py --limit 5          # polite sample of the first 5 HTTP URLs
python3 scripts/nightly.py                    # full check (what the nightly job runs)
python3 scripts/assemble_site.py --out _site  # folder Pages publishes
```

After editing a name, URL, tier, or description, run `--no-network` so the checksum and exports match. `--limit` does not clear statuses it did not probe.

## GitHub Pages
`.github/workflows/pages.yml` publishes `index.html`, `exports/`, `api/`, `data/`, `wiki/`, `gemini/`, `gopher/`, and `docs/` on each push to `main`.

Pages is not turned on by the workflow file. A maintainer needs to set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**. Until that is set, the deploy workflow has nothing to publish to.

## Contributing
Add sites to `data/sites.json` or expand the catalog. See `data/SCHEMA.md` and `docs/COMMONS.md` for the snapshot metadata and repair loop ideas. PRs welcome.

MIT License. Help rebuild the fast text web and a portable knowledge commons.
