#!/usr/bin/env python3
"""Generate plain text, HTML, Gopher, and Gemini exports from data/sites.json.

Headers carry the collection provenance (schema version, generated_at, source,
license, counts, checksum). Curated gemini/ and gopher/ files are left alone;
those are hand-maintained entry points. This script only writes exports/.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from common import ROOT, format_counts, load_json, one_line, write_text


def _header_lines(sites: Mapping[str, Any], catalog: Mapping[str, Any] | None) -> list[str]:
    lines = [
        f"schema_version: {sites.get('schema_version', '')}",
        f"generated_at: {sites.get('generated_at', '')}",
        f"source: {sites.get('source', '')}",
        f"license: {sites.get('license', '')}",
        f"checksum: {sites.get('checksum', '')}",
        f"counts: {format_counts(sites.get('counts'))}",
    ]
    if catalog and catalog.get("checksum"):
        lines.append(f"catalog_checksum: {catalog.get('checksum', '')}")
        lines.append(f"catalog_counts: {format_counts(catalog.get('counts'))}")
    return lines


def render_text(sites: Mapping[str, Any], catalog: Mapping[str, Any] | None = None) -> str:
    lines = ["textweb — Text-friendly & classic sites", *_header_lines(sites, catalog), ""]
    blocks = ["\n".join(lines), ""]
    for site in sites.get("sites", []):
        blocks.append(f"{one_line(site.get('name', ''))}: {one_line(site.get('url', ''))}")
        description = site.get("description") or ""
        if description:
            blocks.append(f"  {one_line(description)}")
        checked = site.get("last_checked") or "-"
        blocks.append(f"  status: {site.get('status', 'unchecked')}  last_checked: {checked}")
        blocks.append("")
    return "\n".join(blocks).rstrip("\n") + "\n"


def render_html(sites: Mapping[str, Any], catalog: Mapping[str, Any] | None = None) -> str:
    header = "<br>\n".join(html.escape(line) for line in _header_lines(sites, catalog))
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>textweb</title>",
        "</head>",
        "<body>",
        "<h1>textweb</h1>",
        "<p>Text-friendly and classic sites</p>",
        f"<p>{header}</p>",
        '<p><a href="../api/v1/status.json">API status</a> | '
        '<a href="../api/v1/sites.json">API sites</a> | '
        '<a href="../api/v1/catalog.json">API catalog</a></p>',
        "<ul>",
    ]
    for site in sites.get("sites", []):
        name = html.escape(one_line(site.get("name", "")))
        url = html.escape(one_line(site.get("url", "")), quote=True)
        description = html.escape(one_line(site.get("description") or ""))
        status = html.escape(str(site.get("status", "unchecked")))
        parts.append(f'<li><a href="{url}">{name}</a> — {description} ({status})</li>')
    parts.append("</ul>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts) + "\n"


def parse_gopher(url: str) -> tuple[str, str, str, str]:
    """Return item type, selector, host, and port for a gopher URL."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = str(parsed.port or 70)
    path = parsed.path or "/"
    if path in ("", "/"):
        return "1", "/", host, port
    body = path[1:]
    if body and body[0] in "0123456789+TgIh":
        item_type = body[0]
        rest = body[1:]
        if rest.startswith("/"):
            selector = rest or "/"
        elif rest == "":
            selector = "/"
        else:
            selector = "/" + rest
        return item_type, selector, host, port
    return "1", path, host, port


def render_gopher(sites: Mapping[str, Any], catalog: Mapping[str, Any] | None = None) -> str:
    lines = ["itextweb — Text-friendly sites\t\t\t"]
    for line in _header_lines(sites, catalog):
        lines.append(f"i{one_line(line)}\t\t\t")
    lines.append("i\t\t\t")
    for site in sites.get("sites", []):
        name = one_line(site.get("name", ""))
        url = one_line(site.get("url", ""))
        if url.startswith("http://") or url.startswith("https://"):
            lines.append(f"h{name}\tURL:{url}\t\t")
        elif url.startswith("gopher://"):
            item_type, selector, host, port = parse_gopher(url)
            lines.append(f"{item_type}{name}\t{selector}\t{host}\t{port}")
        else:
            lines.append(f"i{name} {url}\t\t\t")
    return "\n".join(lines) + "\n"


def _gemini_text(value: Any) -> str:
    text = one_line(value)
    if text.startswith("=>") or text.startswith("```"):
        return " " + text
    return text


def render_gemini(sites: Mapping[str, Any], catalog: Mapping[str, Any] | None = None) -> str:
    lines = ["# textweb", ""]
    lines.extend(_header_lines(sites, catalog))
    lines.append("")
    lines.append("API: /api/v1/status.json")
    lines.append("")
    for site in sites.get("sites", []):
        url = one_line(site.get("url", ""))
        name = _gemini_text(site.get("name", ""))
        lines.append(f"=> {url} {name}")
        description = site.get("description") or ""
        if description:
            lines.append(_gemini_text(description))
        checked = site.get("last_checked") or "-"
        lines.append(f"status: {site.get('status', 'unchecked')}  last_checked: {checked}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write_exports(
    root: Path,
    sites: Mapping[str, Any],
    catalog: Mapping[str, Any] | None = None,
) -> None:
    export_dir = root / "exports"
    write_text(export_dir / "sites.txt", render_text(sites, catalog))
    write_text(export_dir / "index.html", render_html(sites, catalog))
    write_text(export_dir / "gophermap", render_gopher(sites, catalog))
    write_text(export_dir / "index.gmi", render_gemini(sites, catalog))


def exports_match(
    root: Path,
    sites: Mapping[str, Any],
    catalog: Mapping[str, Any] | None = None,
) -> list[str]:
    expected = {
        "sites.txt": render_text(sites, catalog),
        "index.html": render_html(sites, catalog),
        "gophermap": render_gopher(sites, catalog),
        "index.gmi": render_gemini(sites, catalog),
    }
    errors = []
    for name, text in expected.items():
        path = root / "exports" / name
        if not path.exists():
            errors.append(f"exports/{name} is missing")
            continue
        current = path.read_text(encoding="utf-8")
        if current != text:
            errors.append(f"exports/{name} is out of date")
    return errors


def main(argv: list[str] | None = None) -> int:
    root = ROOT
    sites = load_json(root / "data" / "sites.json")
    catalog_path = root / "data" / "catalog-250.json"
    catalog = load_json(catalog_path) if catalog_path.exists() else None
    write_exports(root, sites, catalog)
    print("Exports generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
