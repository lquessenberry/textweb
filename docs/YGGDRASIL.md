# Yggdrasil Mesh Networking

Yggdrasil is a fully decentralised, end-to-end encrypted IPv6 overlay network designed for mesh and ad-hoc topologies. It is especially useful for low-bandwidth, local, or internet-independent delivery of the textweb index (OLPC-style or mesh WiFi scenarios).

## Key properties
- **Encrypted**: All traffic is end-to-end encrypted.
- **Self-healing**: Automatically reroutes around failures.
- **Ad-hoc friendly**: Multicast discovery on the same LAN/subnet; works over Ethernet, WiFi, or Internet peerings.
- **No central points**: Pure peer-to-peer routing.
- **IPv6 overlay**: Uses the `200::/7` range; node address is derived from its public key.
- Cross-platform (Linux, macOS, Windows, Android, FreeBSD, routers, etc.).

Official site: https://yggdrasil-network.github.io/

## Basic setup
1. Install from releases or package manager (see installation docs).
2. Generate config: `yggdrasil -genconf > /etc/yggdrasil.conf`
3. Edit `Peers` section to add public peers (list at https://github.com/yggdrasil-network/public-peers or the live peers page).
   Example:
   ```
   Peers: [
     tls://example-peer.example:12345
     quic://another-peer.example:54321
   ]
   ```
4. Optionally enable a listener if you want others to peer with you:
   ```
   Listen: [
     tls://[::]:12345
   ]
   ```
5. Start: `yggdrasil -useconffile /etc/yggdrasil.conf` (or via systemd).
6. Check: `yggdrasilctl getSelf` and `yggdrasilctl getPeers`.

On the same LAN, multicast discovery often works with zero config (`yggdrasil -autoconf`).

## Using with textweb
- Once on the mesh, serve the static site / JSON over HTTP on your Yggdrasil IPv6 address.
- Clients on the mesh can fetch `http://[your-ygg-address]/data/sites.json` or the HTML exports.
- Combine with local ad-hoc WiFi (hostapd, create_ap, LibreMesh) so devices without Internet can still reach nodes that have a Yggdrasil peering.
- Ideal for offline-first or intermittent connectivity scenarios.

Public peers list and more docs: https://yggdrasil-network.github.io/
