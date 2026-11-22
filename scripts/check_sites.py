#!/usr/bin/env python3
"""Basic health check for sites in data/sites.json.
Updates last_checked and status where possible.
"""
import json
import requests
from datetime import date
from pathlib import Path

DATA = Path("data/sites.json")
TODAY = date.today().isoformat()

def check_url(url):
    try:
        r = requests.head(url, timeout=10, allow_redirects=True, headers={"User-Agent": "textweb-check/0.1"})
        return r.status_code < 400
    except Exception:
        return False

def main():
    data = json.loads(DATA.read_text())
    changed = False
    for site in data.get("sites", []):
        url = site.get("url", "")
        if url.startswith("http"):
            ok = check_url(url)
            site["last_checked"] = TODAY
            site["status"] = "ok" if ok else "down"
            changed = True
    if changed:
        data["updated"] = TODAY
        DATA.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Updated {DATA}")
    else:
        print("No changes")

if __name__ == "__main__":
    main()
