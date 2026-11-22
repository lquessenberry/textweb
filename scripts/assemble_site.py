#!/usr/bin/env python3
"""Copy the static site into a folder GitHub Pages can publish."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from common import ROOT

COPY_PATHS = [
    "index.html",
    "exports",
    "api",
    "data/sites.json",
    "data/catalog-250.json",
    "data/SCHEMA.md",
    "data/schema",
    "data/snapshots",
    "wiki",
    "gemini",
    "gopher",
    "docs",
]


def assemble(root: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for rel in COPY_PATHS:
        src = root / rel
        if not src.exists():
            continue
        dest = out / rel
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble the textweb static site")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    assemble(args.root, args.out)
    print(f"assembled {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
