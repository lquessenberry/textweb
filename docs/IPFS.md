# IPFS Content Addressing for textweb

IPFS addresses content by what it is (cryptographic hash), not where it is stored. This makes the textweb index resilient, verifiable, and distributable without a single host.

## Content Identifiers (CIDs)
A CID is a self-describing identifier:
- Based on a cryptographic hash of the content (default sha2-256).
- Includes codec information (how to interpret the data).
- Same content always produces the same CID (with the same settings).
- Any change in content produces a different CID.
- CIDv1 (preferred) looks like `bafybei...`; older CIDv0 starts with `Qm`.

Docs: https://docs.ipfs.tech/concepts/content-addressing/
CID anatomy: https://proto.school/anatomy-of-a-cid/

## Adding and pinning the index
1. Install Kubo (go-ipfs successor) or use a pinning service.
2. Add the directory or key files:
   ```
   ipfs add -r data/ exports/ wiki/ index.html
   # or just the JSON:
   ipfs add data/sites.json
   ```
3. Note the root CID.
4. Pin it so it is not garbage-collected:
   ```
   ipfs pin add <CID>
   ```
5. Share the CID. Anyone with an IPFS node or gateway can retrieve:
   - `ipfs://<CID>`
   - `https://ipfs.io/ipfs/<CID>` (or other public gateways)
   - Local gateway if running a node.

Pinning services (Pinata, Filebase, Storj, etc.) can keep content available without you running a node 24/7.

## For textweb
- Pin `data/sites.json` and the `exports/` folder.
- Publish the CID in the README or a dedicated file.
- Combine with Yggdrasil: serve an IPFS gateway over the mesh, or have mesh nodes pin the CID.
- Perfect for offline or intermittent networks — once a node has the content, others can fetch it peer-to-peer.

Gateways and more: https://docs.ipfs.tech/
