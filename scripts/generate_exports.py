#!/usr/bin/env python3
"""Generate plain text, Gopher map, Gemini, and simple HTML exports."""
import json
from pathlib import Path

DATA = Path("data/sites.json")
EXPORTS = Path("exports")
EXPORTS.mkdir(exist_ok=True)

def main():
    data = json.loads(DATA.read_text())
    sites = data.get("sites", [])

    # Plain text
    lines = ["textweb — Text-friendly & classic sites\n", f"Updated: {data.get('updated')}\n\n"]
    for s in sites:
        lines.append(f"{s.get('name')}: {s.get('url')}\n  {s.get('description', '')}\n\n")
    (EXPORTS / "sites.txt").write_text("".join(lines))

    # Simple HTML
    html = ["<!DOCTYPE html><html><head><title>textweb</title><meta charset=utf-8></head><body>",
            "<h1>textweb</h1><p>Text-friendly and classic sites</p><ul>"]
    for s in sites:
        html.append(f"<li><a href='{s.get('url')}'>{s.get('name')}</a> — {s.get('description', '')}</li>")
    html.append("</ul></body></html>")
    (EXPORTS / "index.html").write_text("\n".join(html))

    # Gopher map (simple)
    gopher = ["textweb Gopher index\n"]
    for s in sites:
        url = s.get("url", "")
        if url.startswith("http"):
            gopher.append(f"h{s.get('name')}\tURL:{url}\t\t\n")
        elif url.startswith("gopher"):
            gopher.append(f"1{s.get('name')}\t/\t{url.split('://')[1].split('/')[0]}\t70\n")
    (EXPORTS / "gophermap").write_text("".join(gopher))

    # Gemini
    gem = ["# textweb\n\nText-friendly, classic, Gemini and Gopher sites\n\n"]
    for s in sites:
        gem.append(f"=> {s.get('url')} {s.get('name')}\n{s.get('description', '')}\n\n")
    (EXPORTS / "index.gmi").write_text("".join(gem))

    print("Exports generated")

if __name__ == "__main__":
    main()
