"""Entry point for the `demolab` console command (the [project.scripts] target).

Thin launcher, kept deliberately small: it finds the repo root by walking up from the current
directory, then hands off to the real CLI in the engine (demolab-engine/build/cli.py) — which
`update demolab` swaps wholesale. It locates the engine from the *working tree*, never from this
file's own install location, so it behaves identically whether it's run as an installed console
script (this module lives in site-packages) or straight from a clone. Run `demolab` with no
arguments for the command list.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _find_repo() -> Path:
    """The nearest ancestor of the cwd that holds the engine — like git finding its root."""
    for d in (Path.cwd(), *Path.cwd().parents):
        if (d / "demolab-engine" / "build" / "cli.py").is_file():
            return d
    sys.exit("demolab: run this inside a demolab repo (no demolab-engine/build/cli.py found from here).")


def main() -> int:
    repo = _find_repo()
    sys.path.insert(0, str(repo / "demolab-engine" / "build"))
    import cli  # resolved from the working tree, so its __file__-derived paths point at this repo
    return cli.main()


if __name__ == "__main__":
    sys.exit(main())
