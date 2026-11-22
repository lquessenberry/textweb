# Low-Tech Exports

This directory will contain generated formats suitable for:
- Gopher (gophermap)
- Telnet / BBS menus
- Plain text lists
- Gemini capsules
- Simple HTML 1.0 pages

Generation scripts can live in `scripts/` and be run by the nightly workflow.

`scripts/nightly.py` writes `sites.txt`, `index.html`, `gophermap`, and `index.gmi` here. Each file starts with provenance: schema version, generated time, source, license, counts, and checksum. This README is hand-maintained. The curated `gemini/` and `gopher/` directories at the repo root are also left as written.
