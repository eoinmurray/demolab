"""Shared path model: where the package's data lives, where the user's lab is, and the
`.demolab/` staging dir that bridges the two for Typst.

The engine ships in site-packages, but typst `--root` confines all file reads to the lab
tree — so the handful of files Typst must read (lib.typ, imported by user writings; the web
assets + VERSION, read by lib.typ/main.typ) are materialised into a gitignored `.demolab/`
at the lab root, refreshed whenever the installed package version changes. Everything else
is read from the package directly.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
TYP = PACKAGE / "typ"
SCAFFOLD = PACKAGE / "scaffold"
DEPLOY = PACKAGE / "deploy"
RUNBOOKS = PACKAGE / "runbooks"
GUIDES = PACKAGE / "guides"
VERSION = (PACKAGE / "VERSION").read_text().strip()

MARKER = "demolab.yaml"

# Everything stage() writes into <lab>/.demolab/ (plus the VERSION stamp).
_STAGED = ("lib.typ", "style.css", "cite-popover.js", "favicon.svg")


def find_lab_root(start: Path | None = None) -> Path | None:
    """Nearest ancestor of `start` (default: cwd) holding demolab.yaml — the lab marker
    `demolab init`/`demolab scaffold` write. Like git finding its root."""
    start = (start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if (d / MARKER).is_file():
            return d
    return None


def require_lab_root() -> Path:
    root = find_lab_root()
    if root is None:
        sys.exit("demolab: not inside a lab (no demolab.yaml found from here upward).\n"
                 "  Start one with `demolab init` in an empty directory.")
    return root


def stage(root: Path) -> Path:
    """Materialise <root>/.demolab/ (idempotent; refreshed on version-stamp mismatch).
    Returns the staging dir."""
    dot = root / ".demolab"
    stamp = dot / "VERSION"
    prev = stamp.read_text().strip() if stamp.is_file() else None
    if prev == VERSION and all((dot / n).is_file() for n in _STAGED):
        return dot
    dot.mkdir(exist_ok=True)
    for name in _STAGED:
        shutil.copy2(TYP / name, dot / name)
    stamp.write_text(VERSION + "\n")
    if prev and prev != VERSION:
        print(f"→ engine {prev} → {VERSION} — run `demolab docs CHANGELOG --print` to see what changed",
              flush=True)
    return dot
