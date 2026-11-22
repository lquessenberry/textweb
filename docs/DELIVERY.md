# Low-tech, P2P, and ad-hoc delivery

This index is designed to be delivered over simple protocols and low-bandwidth or local networks.

## HTTP / WWW
- Serve the static files (`index.html`, `exports/`, `data/sites.json`) with any HTTP server.
- GitHub Pages: enable in repo settings (already has `index.html`).
- Raw JSON: https://raw.githubusercontent.com/lquessenberry/textweb/main/data/sites.json

## Gemini
- Copy `gemini/` or `exports/index.gmi` to a Gemini server (e.g. Agate, Jetforce, or Gemcities).
- Clients: Lagrange, Amfora, etc.

## Gopher
- Serve `gopher/gophermap` or generated `exports/gophermap` with a Gopher server (e.g. Gophernicus, Pygopherd).
- Lynx supports Gopher natively.

## P2P and offline
- Pin the repo or JSON to IPFS.
- Share the `exports/` folder via USB, local file share, or simple HTTP on a local network.
- For mesh / ad-hoc WiFi (OLPC-style):
  - Use tools like `create_ap`, hostapd + dnsmasq, or LibreMesh / Yggdrasil for mesh.
  - Serve the static site from a Raspberry Pi or old laptop on the local network.
  - Clients can fetch `sites.json` and cache it.
- Consider tools like `syncthing` for peer sync of the index folder.

## Simple protocol ideas
- Plain text over HTTP or even netcat.
- Gemini or Gopher over local IP.
- The goal is that anyone with a terminal or low-power device can get a useful list of fast, text-based resources.

Contributions for better export generators, mesh configs, or protocol servers welcome.
