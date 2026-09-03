"""Discover recursive Typst sources, write a JSON manifest, and compile the configured targets.

build.py does only what Typst can't: it globs the filesystem (Typst has no directory
listing) and orchestrates the compiler. It stages the engine's Typst surface into the lab
inside .demolab/ (Typst --root confines reads to the lab tree, while the engine lives in
site-packages), writes the discovered id/asset lists to .demolab/bundle/index.json, and
compiles; the static typ/main.typ reads that manifest and does
the rest (imports, documents, assets) in plain Typst — there is no generated source.

One `typst compile --format bundle --features bundle,html .demolab/bundle/main.typ` emits,
into .demolab/site/:
  index.html            — homepage index of writings
  <id>.html             — per-entry web page (figures inline, video plays)
  <id>.mp4              — video assets
  pdfs/<id>.pdf         — per-entry individual PDF
  pdfs/book.pdf         — every entry concatenated into one PDF (book mode)

The site (.demolab/site/) is a self-contained generated output (gitignored and deployed to
Pages). Unless `pdfs: false` is set in demolab.yaml, PDFs are also copied to the generated
.demolab/pdfs/ publication directory. Tracked publication evidence lives in `.artifacts/`;
Demolab reads it but never creates or deletes it.

Each <configured-writings>/**/<id>.typ exposes `#let meta = (...)` and `#let body = [...]`.
Entries not yet in that convention are skipped (incremental migration).
The shared LabLayout routes source-checkout inputs beneath .demo/ without
copying them; generated runtime remains .demolab/ for both layouts.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from demolab_cli import _paths, data_sources, url_inputs

# The lab being built. Discovery recognises ordinary labs and the engine's .demo/;
# DEMOLAB_ROOT overrides it (the tests build materialised labs in scratch dirs). Falls back
# to the cwd so an empty dir still gets the friendly
# empty-state build rather than an import-time error.
LAYOUT = _paths.layout_for(Path(os.environ.get("DEMOLAB_ROOT") or _paths.find_lab_root() or Path.cwd()))
ROOT = LAYOUT.root
ASSETS = LAYOUT.assets
BUILD = LAYOUT.runtime / "bundle"          # private scratch: main.typ + manifest + deck PDFs
MAIN = BUILD / "main.typ"                  # staged copy of the packaged typ/main.typ
ENTRY_MAIN = BUILD / "entry.typ"           # staged single-entry PDF wrapper
MANIFEST = BUILD / "index.json"            # scratch: id/asset lists main.typ reads
DECKS = BUILD / "decks"                    # scratch: compiled deck PDFs, embedded as assets
SITE = LAYOUT.runtime / "site"             # bundle output (HTML + mp4 + linked pdfs/)
PDFS = LAYOUT.runtime / "pdfs"             # optional standalone generated PDFs
PREVIEW = False                           # enabled only by the dev worker's explicit flag
PREPARED = False                          # author-owned preparation ran for this build
BUILD_SOURCES = {}                         # pins plus Latest, fixed for this invocation
DATA_INPUTS = {}                           # frozen paths and public video URLs


def preview_paths() -> None:
    """Keep every preview build product separate from ordinary build output."""
    global PREVIEW, BUILD, MAIN, ENTRY_MAIN, MANIFEST, DECKS, SITE, PDFS
    PREVIEW = True
    runtime = LAYOUT.runtime / "preview"
    BUILD, SITE, PDFS = runtime / "bundle", runtime / "site", runtime / "pdfs"
    MAIN, ENTRY_MAIN = BUILD / "main.typ", BUILD / "entry.typ"
    MANIFEST, DECKS = BUILD / "index.json", BUILD / "decks"


def pdfs_enabled() -> bool:
    """Whether this lab publishes PDFs (default: yes).

    demolab.yaml intentionally has no Python YAML dependency. This reads the one supported
    top-level boolean directly; Typst remains the authority for the rest of the config.
    """
    config = LAYOUT.config
    if not config.is_file():
        return True
    text = config.read_text(encoding="utf-8")
    match = re.search(r"(?m)^pdfs:\s*(true|false)\s*(?:#.*)?$", text)
    if match:
        return match.group(1) == "true"
    if re.search(r"(?m)^pdfs\s*:", text):
        raise SystemExit("error: demolab.yaml 'pdfs' must be true or false")
    return True


TYPST = _paths.find_typst(ROOT)
DEFAULT_CREATION_TIMESTAMP = "946684800"  # 2000-01-01T00:00:00Z


def typst_compile(*args: str) -> list[str]:
    """A reproducible Typst compile command shared by every PDF-producing path."""
    timestamp = os.environ.get("SOURCE_DATE_EPOCH", DEFAULT_CREATION_TIMESTAMP)
    inputs = [*LAYOUT.typst_inputs(), "--input", f"demolab-bundle-root={LAYOUT.typst_path(BUILD)}"]
    if os.environ.get("DEMOLAB_DEV") == "1":
        inputs += ["--input", "demolab-dev=true"]
    if PREVIEW:
        inputs += ["--input", "demolab-preview-file=" + LAYOUT.typst_path(LAYOUT.runtime / "preview/input.json")]
    if DATA_INPUTS:
        inputs += ["--input", "demolab-data-inputs=" + LAYOUT.typst_path(BUILD / "data-inputs.json")]
    return [TYPST, "compile", "--creation-timestamp", timestamp, *inputs, *args]


def stage() -> None:
    """Materialise everything Typst reads from inside the lab: .demolab/ (lib + web assets,
    version-stamped) and the bundle root main.typ (copied fresh every build — it's tiny, and
    a stale copy after an engine upgrade would be a subtle bug)."""
    _paths.stage(ROOT)
    # Older engines leaked bundle and demo-preview staging into the user-facing temp/ tree. Remove
    # only those known generated subtrees; preserve any experiment scratch alongside them.
    legacy_temp = ROOT / "temp"
    for generated in (() if PREVIEW else (legacy_temp / "bundle", legacy_temp / "demo-preview")):
        shutil.rmtree(generated, ignore_errors=True)
    if not PREVIEW:
        try:
            legacy_temp.rmdir()  # remove temp/ only when generated engine scratch was its last content
        except OSError:
            pass
    BUILD.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_paths.TYP / "main.typ", MAIN)
    shutil.copy2(_paths.TYP / "entry.typ", ENTRY_MAIN)


def discover() -> tuple[dict[str, Path], dict[str, Path]]:
    """Map stable basename IDs to actual sources, independently of their folders.

    Match real top-level definitions (`#let meta` / `#let body` at line start), not
    prose or comments that merely mention them. Helpers without both exports stay
    unpublished. Article and deck IDs share one namespace to prevent PDF collisions.
    """
    entries: dict[str, Path] = {}
    decks: dict[str, Path] = {}
    seen: dict[str, Path] = {}
    for p in LAYOUT.source_files():
        if p.suffix != ".typ":
            continue
        deck = p.name.endswith(".slide.typ")
        if not deck:
            lines = p.read_text(encoding="utf-8").splitlines()
            if not (any(ln.startswith("#let meta") for ln in lines)
                    and any(ln.startswith("#let body") for ln in lines)):
                continue
        entry_id = p.name.removesuffix(".slide.typ") if deck else p.stem
        # Case-insensitive checks keep output portable to Windows/macOS filesystems.
        key = entry_id.casefold()
        if key in seen:
            raise _paths.LayoutError(
                f"duplicate writing ID {entry_id!r}:\n  {seen[key]}\n  {p}\n"
                "Rename one file; source folders do not change public IDs."
            )
        seen[key] = p
        (decks if deck else entries)[entry_id] = p
    return dict(sorted(entries.items())), dict(sorted(decks.items()))


def write_manifest(ids: dict[str, Path], deck_ids: dict[str, Path], broken: dict | None = None,
                   *, publish_pdfs: bool = True) -> None:
    """Write .demolab/bundle/index.json — the id/asset lists the staged main.typ reads.

    This is the only place per-writing knowledge is assembled, and it's pure data (no Typst
    source): writing ids, static asset paths, and deck ids. An entry in `broken` carries an
    `error` field and loads no assets — main.typ renders it as a stub instead of importing it."""
    broken = broken or {}
    entries = []
    for i, source in ids.items():
        entry = {
            "id": i,
            "kind": "page",
            "source": LAYOUT.typst_path(source),
        }
        if i in broken:
            entry["error"] = broken[i]
        entries.append(entry)
    # Signal whether the optional root demolab.yaml / landing.typ exist — Typst can't stat
    # files, so main.typ only reads them (branding / the custom landing page) when these
    # flags say they're there.
    manifest = {
        "entries": entries,
        "decks": [{"id": d, "source": LAYOUT.typst_path(source)}
                  for d, source in deck_ids.items()],
        "writings": LAYOUT.writings.relative_to(LAYOUT.content).as_posix(),
        "assets": [p.relative_to(ASSETS).as_posix() for p in sorted(ASSETS.rglob("*")) if p.is_file()],
        "pdfs_enabled": publish_pdfs,
        "has_brand_config": LAYOUT.config.exists(),
        "has_landing": LAYOUT.landing.exists(),
        "data_assets": DATA_INPUTS.get("media", {}),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


def compile_decks(deck_ids: dict[str, Path]) -> dict[str, Path]:
    """Compile each standalone deck to a scratch PDF (.demolab/bundle/decks/<id>.pdf); return the ones
    that built. A deck that fails to compile is skipped with a warning rather than failing the whole
    build (main.typ only embeds decks that produced a PDF).

    main.typ embeds these as bundle assets at pdfs/<id>.pdf. Must run before the bundle compile so
    the asset `read(...)` finds the files. The dev server (devserver.py) reruns this on every
    change, so deck edits and new decks live-reload like any entry."""
    DECKS.mkdir(parents=True, exist_ok=True)
    good = {}
    for d, source in deck_ids.items():
        output = DECKS / f"{d}.pdf"
        output.unlink(missing_ok=True)
        proc = subprocess.run(
            typst_compile("--root", str(ROOT),
                          str(source), str(output)),
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            good[d] = source
        else:
            # A later CSS-only rebuild must not resurrect a stale/partial deck PDF.
            output.unlink(missing_ok=True)
            if PREVIEW or BUILD_SOURCES or PREPARED:
                mode = "preview" if PREVIEW else "data-backed build"
                raise _paths.LayoutError(f"{mode} deck {d} compilation failed:\n" + proc.stdout + proc.stderr)
            print(f"  ⚠ deck {d} failed to build — skipping it: "
                  + _error_excerpt(proc.stdout + proc.stderr).splitlines()[0], flush=True)
    return good


def _entry_from_error(err: str, candidates: dict[str, Path]) -> str | None:
    """Attribute a diagnostic/import trace to a known source, not a fixed path pattern."""
    matches = []
    for entry_id, source in candidates.items():
        relative = source.relative_to(ROOT).as_posix()
        # Typst prints both project-relative locations and root-relative import traces.
        # Boundaries avoid attributing helpers such as prefix-note.typ to note.typ.
        match = re.search(r"(?<![\w./-])/?" + re.escape(relative) + r"(?=[:`\s]|$)",
                          err.replace("\\", "/"))
        if match:
            matches.append((match.start(), entry_id))
    if matches:
        return min(matches)[1]
    return None


def _error_excerpt(err: str, lines: int = 8) -> str:
    """The first `error:` block from Typst's output, for the stub page and the warning."""
    rows = err.splitlines()
    for i, row in enumerate(rows):
        if row.lstrip().startswith("error:"):
            return "\n".join(rows[i:i + lines]).strip()
    return err.strip() or "build failed"


def compile_bundle(ids: dict[str, Path], deck_ids: dict[str, Path], *,
                   destination: Path, publish_pdfs: bool = True) -> dict:
    """Compile the whole bundle. If an entry fails (a missing figure, a Typst error), flag it and
    retry, so it renders as a stub page instead of taking the rest of the site down with it. Returns
    the {id: error} map of entries that were stubbed."""
    broken: dict = {}
    while True:
        write_manifest(ids, deck_ids, broken=broken, publish_pdfs=publish_pdfs)
        # A failed compiler may have emitted partial files. Each retry starts clean too.
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        proc = subprocess.run(
            typst_compile("--format", "bundle", "--features", "bundle,html",
                          "--root", str(ROOT), str(MAIN), str(destination) + "/"),
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            return broken
        err = proc.stdout + proc.stderr
        bad = _entry_from_error(err, {i: source for i, source in ids.items() if i not in broken})
        # Ordinary publication is resilient when Typst identifies the one article that failed.
        # Its frozen input map prevents fallback to another run, while a stub lets unrelated
        # articles publish. Preview remains fail-closed because it replaces accepted session
        # state atomically. A prepare command already failed before compilation if its own output
        # was invalid; successful preparation does not make a later article-local error global.
        if PREVIEW:
            raise _paths.LayoutError("preview compilation failed:\n" + err)
        if bad is None:
            # Not attributable to one entry (an engine, asset, or deck error): surface the real
            # failure rather than looping.
            if BUILD_SOURCES:
                raise _paths.LayoutError("data-backed build compilation failed:\n" + err)
            sys.stderr.write(err)
            raise subprocess.CalledProcessError(proc.returncode, proc.args, proc.stdout, proc.stderr)
        broken[bad] = _error_excerpt(err)
        print(f"  ⚠ {bad} failed to build — stubbing it, keeping the rest: "
              + broken[bad].splitlines()[0], flush=True)


def compile_entry(entry_id: str, ids: dict[str, Path], decks: dict[str, Path]) -> None:
    """Compile one ordinary writing directly to its generated standalone PDF."""
    if entry_id not in ids:
        detail = " (it is a slide deck; use `demolab slides`)" if entry_id in decks else ""
        raise SystemExit(f"error: no buildable entry named {entry_id!r}{detail}")
    PDFS.mkdir(parents=True, exist_ok=True)
    output = BUILD / "entry-next.pdf" if BUILD_SOURCES or PREPARED else PDFS / f"{entry_id}.pdf"
    proc = subprocess.run(
        typst_compile("--root", str(ROOT), "--input", f"entry={entry_id}",
                      "--input", f"entry-source={LAYOUT.typst_path(ids[entry_id])}",
                      "--input", f"has-brand={str(LAYOUT.config.exists()).lower()}",
                      str(ENTRY_MAIN), str(output)),
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        if BUILD_SOURCES or PREPARED:
            output.unlink(missing_ok=True)
        sys.stderr.write(proc.stdout + proc.stderr)
        raise subprocess.CalledProcessError(proc.returncode, proc.args, proc.stdout, proc.stderr)
    if BUILD_SOURCES or PREPARED:
        output.replace(PDFS / f"{entry_id}.pdf")
    print(f"built {entry_id} -> {PDFS.relative_to(ROOT)}/{entry_id}.pdf"
          " (site and book not updated)", flush=True)


def main() -> None:
    global BUILD_SOURCES, DATA_INPUTS, PREPARED
    if "--preview" in sys.argv:
        preview_paths()
    # --generate-only writes the manifest + deck PDFs without compiling the bundle: a hand
    # tool for inspecting what the compiler will see. (Dev serving is devserver.py, which runs
    # a full build on each change; it doesn't use this flag.)
    generate_only = "--generate-only" in sys.argv
    # --skip-decks reuses the deck PDFs already in .demolab/bundle/decks/ instead of recompiling
    # them. The dev server passes it when a change touched no Typst source, helper, or data,
    # so a CSS-only edit needn't recompile decks. Safe only when
    # those PDFs exist (a full build ran first); a bare `demolab build` never skips.
    skip_decks = "--skip-decks" in sys.argv
    no_pdf_copy = "--no-pdf-copy" in sys.argv
    entry_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(entry_args) > 1:
        raise SystemExit("error: build accepts at most one entry id")
    # Validate configuration and collisions before writing generated files.
    ids, decks = discover()
    PREPARED = url_inputs.prepare(LAYOUT, article=entry_args[0] if entry_args else "")
    publish_pdfs = pdfs_enabled()
    BUILD_SOURCES = {} if PREVIEW else data_sources.resolve_build_sources(LAYOUT, ids)
    selected = (json.loads((LAYOUT.runtime / "preview/input.json").read_text(encoding="utf-8"))
                if PREVIEW else BUILD_SOURCES)
    DATA_INPUTS = data_sources.inventory(LAYOUT, selected) if selected else {}
    stage()
    if DATA_INPUTS:
        (BUILD / "data-inputs.json").write_text(json.dumps(DATA_INPUTS) + "\n", encoding="utf-8")
    if entry_args:
        if not publish_pdfs:
            raise SystemExit("error: PDF publishing is disabled by demolab.yaml (pdfs: false)")
        compile_entry(entry_args[0], ids, decks)
        return
    deck_ids = decks if publish_pdfs else {}
    # Zero writings is a valid state (a freshly `demolab scaffold`-ed repo): main.typ renders
    # a friendly empty-state homepage, so we build rather than error.
    # Compile decks first so their PDFs exist for the asset embeds in main.typ (skip reuses the
    # PDFs already on disk). Either way, only decks that actually have a PDF are referenced.
    if skip_decks:
        good_decks = {d: source for d, source in deck_ids.items() if (DECKS / f"{d}.pdf").exists()}
    else:
        good_decks = compile_decks(deck_ids)
    if PREVIEW and len(good_decks) != len(deck_ids):
        raise _paths.LayoutError("preview deck compilation failed; see diagnostics above")
    write_manifest(ids, good_decks, publish_pdfs=publish_pdfs)
    if generate_only:
        print(f"wrote manifest for {len(ids)} entries: {', '.join(ids)}"
              + (f" + {len(good_decks)} decks: {', '.join(good_decks)}" if good_decks else ""))
        return
    # One bad entry (a missing figure, a Typst error) becomes a stub page instead of failing the
    # whole site — compile_bundle flags it and retries.
    # Compile a fresh candidate so deleted/moved sources cannot leave published ghost pages.
    # Keep the last usable site if compilation fails, and never touch authored inputs.
    candidate = BUILD / "site-next"
    try:
        broken = compile_bundle(ids, good_decks, publish_pdfs=publish_pdfs, destination=candidate)
        if PREVIEW and broken:
            raise _paths.LayoutError("preview compilation failed:\n" + "\n".join(
                f"{entry}: {error}" for entry, error in broken.items()))
        if SITE.exists():
            shutil.rmtree(SITE)
        candidate.replace(SITE)
    finally:
        if candidate.exists():
            shutil.rmtree(candidate)
    good = [i for i in ids if i not in broken]
    # Copy the site's compiled PDFs (entries, book, and decks) to .demolab/pdfs/.
    if publish_pdfs and not no_pdf_copy:
        shutil.rmtree(PDFS, ignore_errors=True)
        PDFS.mkdir(parents=True, exist_ok=True)
        for pdf in sorted((SITE / "pdfs").glob("*.pdf")):
            shutil.copy(pdf, PDFS / pdf.name)
    # The verbose detail (which ids built / stubbed, where the generated PDFs live) gets its own line;
    # the CONCISE summary is printed LAST, because the dev-server watch loop echoes only build.py's
    # final stdout line on each rebuild. So a `demolab dev` session shows a terse one-liner, while a
    # one-shot `demolab build` still prints the full id list above it.
    print(f"  entries: {', '.join(good)}"
          + (f"  ·  decks: {', '.join(good_decks)}" if good_decks else "")
          + (f"  ·  ⚠ stubbed: {', '.join(sorted(broken))}" if broken else "")
          + (f"  ·  pdfs -> {PDFS.relative_to(ROOT)}/" if publish_pdfs and not no_pdf_copy
             else "  ·  preview PDFs kept in site output" if publish_pdfs
             else "  ·  PDF publishing disabled"))
    summary = f"built {len(good)} entries" + (f" + {len(good_decks)} decks" if good_decks else "")
    if broken:
        summary += f", {len(broken)} stubbed"
    print(f"{summary} -> {SITE.relative_to(ROOT)}/", flush=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except _paths.LayoutError as exc:
        sys.exit(f"error: {exc}")
