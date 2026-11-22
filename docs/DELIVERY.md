# Low-tech, P2P, and ad-hoc delivery

This index is designed to be delivered over simple protocols and low-bandwidth or local networks.

## HTTP / WWW
- Serve the static files (`index.html`, `exports/`, `data/sites.json`) with any HTTP server.
- GitHub Pages: enable in repo settings (already has `index.html`).
- Raw JSON: https://raw.githubusercontent.com/lquessenberry/textweb/main/data/sites.json
- Static API (also served by GitHub Pages once enabled): `/api/v1/sites.json`, `/api/v1/catalog.json`, `/api/v1/status.json`, `/api/v1/snapshots/index.json`

## Gemini
- Copy `gemini/` or `exports/index.gmi` to a Gemini server (e.g. Agate, Jetforce, or Gemcities).
- Clients: Lagrange, Amfora, etc.

## Gopher
- Serve `gopher/gophermap` or generated `exports/gophermap` with a Gopher server (e.g. Gophernicus, Pygopherd).
- Lynx supports Gopher natively.

## Yggdrasil mesh
See [docs/YGGDRASIL.md](YGGDRASIL.md) for full details.
- End-to-end encrypted IPv6 overlay perfect for ad-hoc / mesh WiFi.
- Multicast discovery on the same LAN; static peers over Internet or local links.
- Serve the textweb static files over HTTP on your Yggdrasil address so mesh peers can reach them without the public Internet.

## IPFS
See [docs/IPFS.md](IPFS.md) for full details.
- Content-addressed (CID) distribution of the index and exports.
- Pin the CID so it remains available; retrieve via gateways or local nodes.
- Works well combined with Yggdrasil or pure local networks.

## P2P and offline
- Pin the repo or JSON to IPFS.
- Share the `exports/` folder via USB, local file share, or simple HTTP on a local network.
- For mesh / ad-hoc WiFi (OLPC-style):
  - Use tools like `create_ap`, hostapd + dnsmasq, or LibreMesh / Yggdrasil for mesh.
  - Serve the static site from a Raspberry Pi or old laptop on the local network.
  - Clients can fetch `sites.json` and cache it.
- Consider tools like `syncthing` for peer sync of the index folder.

## Static JSON API
Any static file host can serve the versioned API next to the HTML page:

- `/api/v1/sites.json` — curated index
- `/api/v1/catalog.json` — tiered catalog
- `/api/v1/status.json` — up/down/unchecked/skipped counts and the last run
- `/api/v1/snapshots/index.json` — retained daily and monthly snapshots
- `/data/snapshots/YYYY-MM-DD.json.gz` — compact status snapshot for that day

## Daily health checks
The GitHub Action in `.github/workflows/nightly-check.yml` runs every day at 04:00 UTC (and can be triggered manually). It:
- Checks HTTP sites and updates `last_checked` / `status` in `data/sites.json` and `data/catalog-250.json`
- Writes a gzipped snapshot under `data/snapshots/` (last 30 days, plus the latest of each older month)
- Regenerates the plain-text, HTML, Gopher, and Gemini exports
- Refreshes `api/v1/`

## Simple protocol ideas
- Plain text over HTTP or even netcat.
- Gemini or Gopher over local IP.
- The goal is that anyone with a terminal or low-power device can get a useful list of fast, text-based resources.

Contributions for better export generators, mesh configs, or protocol servers welcome.
