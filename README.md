# textweb

Curated, nightly-updated index of text-browser friendly, classic, Gemini, Gopher, and low-tech websites — evolving into a portable knowledge commons.

**Purpose**: Replenish the extremely fast, capable text-based internet for Lynx, Links, w3m, ELinks, BBS, telnet, Gopher, Gemini, and retro hardware — including low-bandwidth, mesh, and offline delivery.

## Quick links
- **Knowledge commons vision**: [docs/COMMONS.md](docs/COMMONS.md)
- Starter catalog of ~250 resources: [data/catalog-250.json](data/catalog-250.json)
- Human wiki: [wiki/sites.md](wiki/sites.md)
- Machine data: [data/sites.json](data/sites.json) — raw: https://raw.githubusercontent.com/lquessenberry/textweb/main/data/sites.json
- Static page: [index.html](index.html)
- Exports: [exports/](exports/) (plain text, HTML, Gopher, Gemini)
- Gemini: [gemini/](gemini/)
- Gopher: [gopher/](gopher/)
- Delivery notes (Yggdrasil, IPFS, ad-hoc WiFi): [docs/DELIVERY.md](docs/DELIVERY.md)
- Yggdrasil details: [docs/YGGDRASIL.md](docs/YGGDRASIL.md)
- IPFS details: [docs/IPFS.md](docs/IPFS.md)

## Nightly updates
GitHub Action in `.github/workflows/nightly-check.yml` runs health checks and regenerates exports.

## Contributing
Add sites to `data/sites.json` or expand the catalog. See `data/SCHEMA.md` and `docs/COMMONS.md` for the snapshot metadata and repair loop ideas. PRs welcome.

MIT License. Help rebuild the fast text web and a portable knowledge commons.
