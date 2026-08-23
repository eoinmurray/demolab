"""Discover writings/*.typ, write a JSON manifest, and compile the configured targets.

build.py does only what Typst can't: it globs the filesystem (Typst has no directory
listing) and orchestrates the compiler. It stages the engine's Typst surface into the lab
(.demolab/ + temp/bundle/main.typ — typst --root confines reads to the lab tree, and the
engine lives in site-packages), writes the discovered id/asset lists to
temp/bundle/index.json, and compiles; the static typ/main.typ reads that manifest and does
the rest (imports, documents, assets) in plain Typst — there is no generated source.

One `typst compile --format bundle --features bundle,html temp/bundle/main.typ` emits,
into artifacts/site/:
  index.html            — homepage index of writings
  <id>.html             — per-entry web page (figures inline, video plays)
  <id>.mp4              — video assets
  pdfs/<id>.pdf         — per-entry individual PDF
  pdfs/book.pdf         — every entry concatenated into one PDF (book mode)

The site (artifacts/site/) is a self-contained build output (gitignored, deployed to
Pages). Unless `pdfs: false` is set in demolab.yaml, PDFs are also mirrored to the
committed artifacts/pdfs/ as shareable deliverables.

Each writings/<id>.typ exposes `#let meta = (...)` and `#let body = [...]`.
Entries not yet in that convention are skipped (incremental migration).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from demolab_cli import _paths

# The lab being built. Normally found by walking up from the cwd for demolab.yaml;
# DEMOLAB_ROOT overrides it (the test fixtures and `demolab dev --demo` build materialised
# labs in scratch dirs). Falls back to the cwd so an empty dir still gets the friendly
# empty-state build rather than an import-time error.
ROOT = Path(os.environ.get("DEMOLAB_ROOT") or _paths.find_lab_root() or Path.cwd()).resolve()
WRITINGS = ROOT / "writings"
ASSETS = ROOT / "assets"
BUILD = ROOT / "temp" / "bundle"           # scratch: staged main.typ + manifest + deck PDFs
MAIN = BUILD / "main.typ"                  # staged copy of the packaged typ/main.typ
ENTRY_MAIN = BUILD / "entry.typ"           # staged single-entry PDF wrapper
MANIFEST = BUILD / "index.json"            # scratch: id/asset lists main.typ reads
DECKS = BUILD / "decks"                    # scratch: compiled deck PDFs, embedded as assets
SITE = ROOT / "artifacts" / "site"         # bundle output (HTML + mp4 + pdfs/), gitignored
PDFS = ROOT / "artifacts" / "pdfs"         # committed copy of the PDFs (shareable)


def pdfs_enabled() -> bool:
    """Whether this lab publishes PDFs (default: yes).

    demolab.yaml intentionally has no Python YAML dependency. This reads the one supported
    top-level boolean directly; Typst remains the authority for the rest of the config.
    """
    config = ROOT / "demolab.yaml"
    if not config.is_file():
        return True
    text = config.read_text(encoding="utf-8")
    match = re.search(r"(?m)^pdfs:\s*(true|false)\s*(?:#.*)?$", text)
    if match:
        return match.group(1) == "true"
    if re.search(r"(?m)^pdfs\s*:", text):
        raise SystemExit("error: demolab.yaml 'pdfs' must be true or false")
    return True


def _find_typst() -> str:
    """The typst CLI — needs --features bundle,html (experimental). A lab-local install wins
    (.tools/bin — the no-package-manager fallback for locked-down machines), then PATH;
    shutil.which resolves typst.exe on Windows, where a bare name can fail."""
    for name in ("typst.exe", "typst"):
        local = ROOT / ".tools" / "bin" / name
        if local.exists():
            return str(local)
    return shutil.which("typst") or "typst"


TYPST = _find_typst()
DEFAULT_CREATION_TIMESTAMP = "946684800"  # 2000-01-01T00:00:00Z


def typst_compile(*args: str) -> list[str]:
    """A reproducible Typst compile command shared by every PDF-producing path."""
    timestamp = os.environ.get("SOURCE_DATE_EPOCH", DEFAULT_CREATION_TIMESTAMP)
    return [TYPST, "compile", "--creation-timestamp", timestamp, *args]


def stage() -> None:
    """Materialise everything Typst reads from inside the lab: .demolab/ (lib + web assets,
    version-stamped) and the bundle root main.typ (copied fresh every build — it's tiny, and
    a stale copy after an engine upgrade would be a subtle bug)."""
    _paths.stage(ROOT)
    BUILD.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_paths.TYP / "main.typ", MAIN)
    shutil.copy2(_paths.TYP / "entry.typ", ENTRY_MAIN)


def discover():
    """Entry ids (exp*/ar*) that follow the meta+body convention, sorted.

    Match real top-level definitions (`#let meta` / `#let body` at line start), not
    prose or comments that merely mention them. Slide decks (`*.slide.typ`) are a
    separate category — see discover_decks — so they're skipped here."""
    ids = []
    for p in sorted(WRITINGS.glob("*.typ")):
        if p.name.endswith(".slide.typ"):
            continue
        lines = p.read_text().splitlines()
        has_meta = any(ln.startswith("#let meta") for ln in lines)
        has_body = any(ln.startswith("#let body") for ln in lines)
        if has_meta and has_body:
            ids.append(p.stem)
    return ids


def discover_decks():
    """Deck ids from `writings/<id>.slide.typ` — standalone touying slide decks, sorted.

    Touying decks are paged-only (they don't survive HTML export, see the deck header
    comment), so they aren't bundle entries. Instead they're compiled to standalone PDFs
    and linked from the homepage. Each deck declares `#let meta` (title/date) but no
    `#let body`; the meta is imported to label the link."""
    return [p.name.removesuffix(".slide.typ") for p in sorted(WRITINGS.glob("*.slide.typ"))]


def write_manifest(ids: list[str], deck_ids: list[str], broken: dict | None = None,
                   *, publish_pdfs: bool = True) -> None:
    """Write temp/bundle/index.json — the id/asset lists the staged main.typ reads.

    This is the only place per-writing knowledge is assembled, and it's pure data (no Typst
    source): writing ids, static asset paths, and deck ids. An entry in `broken` carries an
    `error` field and loads no assets — main.typ renders it as a stub instead of importing it."""
    broken = broken or {}
    entries = []
    for i in ids:
        entry = {
            "id": i,
            "kind": "page",
        }
        if i in broken:
            entry["error"] = broken[i]
        entries.append(entry)
    # Signal whether the optional root demolab.yaml / landing.typ exist — Typst can't stat
    # files, so main.typ only reads them (branding / the custom landing page) when these
    # flags say they're there.
    manifest = {
        "entries": entries,
        "decks": [{"id": d} for d in deck_ids],
        "assets": [p.relative_to(ASSETS).as_posix() for p in sorted(ASSETS.rglob("*")) if p.is_file()],
        "pdfs_enabled": publish_pdfs,
        "has_brand_config": (ROOT / "demolab.yaml").exists(),
        "has_landing": (ROOT / "landing.typ").exists(),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


def compile_decks(deck_ids: list[str]) -> list[str]:
    """Compile each standalone deck to a scratch PDF (temp/bundle/decks/<id>.pdf); return the ones
    that built. A deck that fails to compile is skipped with a warning rather than failing the whole
    build (main.typ only embeds decks that produced a PDF).

    main.typ embeds these as bundle assets at pdfs/<id>.pdf. Must run before the bundle compile so
    the asset `read(...)` finds the files. The dev server (devserver.py) reruns this on every
    change, so deck edits and new decks live-reload like any entry."""
    DECKS.mkdir(parents=True, exist_ok=True)
    good = []
    for d in deck_ids:
        proc = subprocess.run(
            typst_compile("--root", str(ROOT),
                          str(WRITINGS / f"{d}.slide.typ"), str(DECKS / f"{d}.pdf")),
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            good.append(d)
        else:
            print(f"  ⚠ deck {d} failed to build — skipping it: "
                  + _error_excerpt(proc.stdout + proc.stderr).splitlines()[0], flush=True)
    return good


def _entry_from_error(err: str, candidates: set) -> str | None:
    """Which entry did a bundle-compile error come from? Parsed from a `/writings/<id>.typ` mention
    in the message (only ids we can still drop)."""
    for m in re.finditer(r"/writings/([A-Za-z0-9_-]+)\.typ", err):
        if m.group(1) in candidates:
            return m.group(1)
    return None


def _error_excerpt(err: str, lines: int = 8) -> str:
    """The first `error:` block from Typst's output, for the stub page and the warning."""
    rows = err.splitlines()
    for i, row in enumerate(rows):
        if row.lstrip().startswith("error:"):
            return "\n".join(rows[i:i + lines]).strip()
    return err.strip() or "build failed"


def compile_bundle(ids: list[str], deck_ids: list[str], *, publish_pdfs: bool = True) -> dict:
    """Compile the whole bundle. If an entry fails (a missing figure, a Typst error), flag it and
    retry, so it renders as a stub page instead of taking the rest of the site down with it. Returns
    the {id: error} map of entries that were stubbed."""
    broken: dict = {}
    while True:
        write_manifest(ids, deck_ids, broken=broken, publish_pdfs=publish_pdfs)
        proc = subprocess.run(
            typst_compile("--format", "bundle", "--features", "bundle,html",
                          "--root", str(ROOT), str(MAIN), str(SITE) + "/"),
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            return broken
        err = proc.stdout + proc.stderr
        bad = _entry_from_error(err, set(ids) - broken.keys())
        if bad is None:
            # Not attributable to one entry (an engine, asset, or deck error): surface the real
            # failure rather than looping.
            sys.stderr.write(err)
            raise subprocess.CalledProcessError(proc.returncode, proc.args, proc.stdout, proc.stderr)
        broken[bad] = _error_excerpt(err)
        print(f"  ⚠ {bad} failed to build — stubbing it, keeping the rest: "
              + broken[bad].splitlines()[0], flush=True)


def compile_entry(entry_id: str, ids: list[str]) -> None:
    """Compile one ordinary writing directly to its committed standalone PDF."""
    if entry_id not in ids:
        slide = WRITINGS / f"{entry_id}.slide.typ"
        detail = " (it is a slide deck; use `demolab slides`)" if slide.exists() else ""
        raise SystemExit(f"error: no buildable entry named {entry_id!r}{detail}")
    PDFS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        typst_compile("--root", str(ROOT), "--input", f"entry={entry_id}",
                      "--input", f"has-brand={str((ROOT / 'demolab.yaml').exists()).lower()}",
                      str(ENTRY_MAIN), str(PDFS / f"{entry_id}.pdf")),
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise subprocess.CalledProcessError(proc.returncode, proc.args, proc.stdout, proc.stderr)
    print(f"built {entry_id} -> {PDFS.relative_to(ROOT)}/{entry_id}.pdf"
          " (site and book not updated)", flush=True)


def main() -> None:
    # --generate-only writes the manifest + deck PDFs without compiling the bundle: a hand
    # tool for inspecting what the compiler will see. (Dev serving is devserver.py, which runs
    # a full build on each change; it doesn't use this flag.)
    generate_only = "--generate-only" in sys.argv
    # --skip-decks reuses the deck PDFs already in temp/bundle/decks/ instead of recompiling
    # them. The dev server passes it when a change touched no deck source or data asset, so a
    # prose/CSS/lib edit doesn't pay for deck compilation it can't have affected. Safe only when
    # those PDFs exist (a full build ran first); a bare `demolab build` never skips.
    skip_decks = "--skip-decks" in sys.argv
    no_mirror = "--no-mirror" in sys.argv
    entry_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(entry_args) > 1:
        raise SystemExit("error: build accepts at most one entry id")
    stage()
    ids = discover()
    publish_pdfs = pdfs_enabled()
    if entry_args:
        if not publish_pdfs:
            raise SystemExit("error: PDF publishing is disabled by demolab.yaml (pdfs: false)")
        compile_entry(entry_args[0], ids)
        return
    deck_ids = discover_decks() if publish_pdfs else []
    # Zero writings is a valid state (a freshly `demolab scaffold`-ed repo): main.typ renders
    # a friendly empty-state homepage, so we build rather than error.
    # Compile decks first so their PDFs exist for the asset embeds in main.typ (skip reuses the
    # PDFs already on disk). Either way, only decks that actually have a PDF are referenced.
    if skip_decks:
        good_decks = [d for d in deck_ids if (DECKS / f"{d}.pdf").exists()]
    else:
        good_decks = compile_decks(deck_ids)
    write_manifest(ids, good_decks, publish_pdfs=publish_pdfs)
    SITE.mkdir(parents=True, exist_ok=True)
    if not publish_pdfs:
        # Bundle compilation updates named outputs but does not prune outputs from an earlier
        # build. The site tree is regenerable, so remove stale PDFs before a web-only compile;
        # the committed artifacts/pdfs/ record remains deliberately untouched.
        shutil.rmtree(SITE / "pdfs", ignore_errors=True)
    if generate_only:
        print(f"wrote manifest for {len(ids)} entries: {', '.join(ids)}"
              + (f" + {len(good_decks)} decks: {', '.join(good_decks)}" if good_decks else ""))
        return
    # One bad entry (a missing figure, a Typst error) becomes a stub page instead of failing the
    # whole site — compile_bundle flags it and retries.
    broken = compile_bundle(ids, good_decks, publish_pdfs=publish_pdfs)
    good = [i for i in ids if i not in broken]
    # mirror the compiled PDFs (entries, book, and decks) to the committed artifacts/pdfs/
    if publish_pdfs and not no_mirror:
        PDFS.mkdir(parents=True, exist_ok=True)
        for pdf in sorted((SITE / "pdfs").glob("*.pdf")):
            shutil.copy(pdf, PDFS / pdf.name)
    # The verbose detail (which ids built / stubbed, where the PDFs mirror) goes on its own line;
    # the CONCISE summary is printed LAST, because the dev-server watch loop echoes only build.py's
    # final stdout line on each rebuild. So a `demolab dev` session shows a terse one-liner, while a
    # one-shot `demolab build` still prints the full id list above it.
    print(f"  entries: {', '.join(good)}"
          + (f"  ·  decks: {', '.join(good_decks)}" if good_decks else "")
          + (f"  ·  ⚠ stubbed: {', '.join(sorted(broken))}" if broken else "")
          + (f"  ·  pdfs -> {PDFS.relative_to(ROOT)}/" if publish_pdfs and not no_mirror
             else "  ·  preview PDFs left untracked" if publish_pdfs
             else "  ·  PDF publishing disabled"))
    summary = f"built {len(good)} entries" + (f" + {len(good_decks)} decks" if good_decks else "")
    if broken:
        summary += f", {len(broken)} stubbed"
    print(f"{summary} -> {SITE.relative_to(ROOT)}/", flush=True)


if __name__ == "__main__":
    sys.exit(main())
