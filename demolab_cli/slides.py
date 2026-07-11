"""Compile standalone Typst decks to artifacts/pdfs/ — the engine behind `demolab slides`.

A "standalone" writing is any writings/*.typ that does NOT declare the bundle contract
(`#let meta` + `#let body`); bundle entries are built by build.py instead. Stdlib Python
(no grep/basename, so it runs on Windows), sharing build.py's root + typst resolution.
"""
import re
import subprocess
import sys

from demolab_cli import build

_META = re.compile(r"^#let meta", re.M)
_BODY = re.compile(r"^#let body", re.M)


def is_bundle_entry(source: str) -> bool:
    return bool(_META.search(source) and _BODY.search(source))


def main() -> None:
    build.stage()  # a deck may import /.demolab/lib.typ (video, data-file, …)
    build.PDFS.mkdir(parents=True, exist_ok=True)
    found = failed = False
    for f in sorted(build.WRITINGS.glob("*.typ")):
        if is_bundle_entry(f.read_text(encoding="utf-8")):
            continue
        found = True
        out = build.PDFS / (f.name.removesuffix(".typ") + ".pdf")
        proc = subprocess.run([build.TYPST, "compile", "--root", str(build.ROOT), str(f), str(out)])
        if proc.returncode == 0:
            print(f"wrote {out.relative_to(build.ROOT)}", flush=True)
        else:
            failed = True  # typst already printed the error; keep compiling the rest
    if not found:
        print("no standalone decks in writings/", flush=True)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
