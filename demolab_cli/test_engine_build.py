"""End-to-end tests for generic writings, assets, and optional PDFs."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pytest

from demolab_cli import _paths, build

pytestmark = pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")


def _assemble(root: Path, *, demo: bool = True) -> None:
    shutil.copytree(_paths.SCAFFOLD / "skeleton", root, dirs_exist_ok=True)
    if demo:
        source = _paths.PACKAGE.parent / ".demo"
        shutil.copy2(source / "demolab.yaml", root / "demolab.yaml")
        shutil.copytree(source / "writings", root / "writings", dirs_exist_ok=True)
        if (source / "assets").is_dir():
            shutil.copytree(source / "assets", root / "assets", dirs_exist_ok=True)
        if (source / "data").is_dir():
            shutil.copytree(source / "data", root / ".artifacts", dirs_exist_ok=True)
            shutil.copytree(source / "data", root / "data", dirs_exist_ok=True)
        if (source / "scripts").is_dir():
            shutil.copytree(source / "scripts", root / "scripts", dirs_exist_ok=True)


def _assemble_demo(root: Path) -> None:
    shutil.copytree(_paths.PACKAGE.parent / ".demo", root / ".demo", dirs_exist_ok=True)
    engine = root / "demolab_cli"
    engine.mkdir()
    (engine / "build.py").write_text("# Source-checkout marker for the fixture.\n")
    (engine / "VERSION").write_text(_paths.VERSION + "\n")


def _build(root: Path, entry: str | None = None) -> None:
    subprocess.run(
        [sys.executable, "-m", "demolab_cli.build", *([entry] if entry else [])],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, check=True,
    )


def _unpin_demo(root: Path) -> None:
    """Exercise legacy Typst-only defaults without pins or discovery."""
    config = _paths.layout_for(root).config
    text = config.read_text()
    if "build:\n" in text:
        config.write_text(text[:text.index("build:\n")] + text[text.index("book-title:"):])


def _build_result(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "demolab_cli.build"],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True,
    )


def _cli(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "demolab_cli.cli", *args], cwd=cwd,
        env={k: v for k, v in os.environ.items() if k != "DEMOLAB_ROOT"},
        capture_output=True, text=True,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("source_layout", [False, True])
def test_configured_nested_writings_build_all_targets(tmp_path, source_layout):
    root = tmp_path / "lab"
    root.mkdir()
    if source_layout:
        _assemble_demo(root)
    else:
        _assemble(root, demo=False)
    layout = _paths.layout_for(root)
    layout.config.write_text('name: Nested sources\nwritings: "articles/research" # custom root\n')
    sources = layout.content / "articles" / "research"
    nested = sources / "physics notes"
    nested.mkdir(parents=True)
    helper = nested / "helper.typ"
    helper.write_text('#let message = [Nested helper content.]\n')
    entry = nested / "entropy.typ"
    entry.write_text('#import "helper.typ": message\n'
                     '#let meta = (title: "Entropy", created_at: "2026-08-27", collection: "physics")\n'
                     '#let body = [#message]\n')
    talks = nested / "talks"
    talks.mkdir()
    deck = talks / "keynote.slide.typ"
    deck.write_text('#import "../helper.typ": message\n'
                    '#let meta = (title: "Keynote", created_at: "2026-08-27")\n#message\n')
    # The old default tree must not also be published when another root is configured.
    legacy = layout.content / "writings" / "old.typ"
    legacy.parent.mkdir(exist_ok=True)
    legacy.write_text('#let meta = (title: "Old", created_at: "2026-08-27")\n#let body = [Old.]\n')
    before = {p: _sha256(p) for p in (helper, entry, deck, legacy, layout.config)}
    _build(root)
    site = root / ".demolab" / "site"
    page = (site / "entropy.html").read_text()
    assert '<script src="image-lightbox.js" defer></script>' in page
    assert (site / "image-lightbox.js").is_file()
    manifest = json.loads((root / ".demolab" / "bundle" / "index.json").read_text())
    assert manifest["entries"] == [{"id": "entropy", "kind": "page", "source": layout.typst_path(entry)}]
    assert manifest["decks"] == [{"id": "keynote", "source": layout.typst_path(deck)}]
    assert "Nested helper content." in (site / "entropy.html").read_text()
    assert 'href="entropy"' in (site / "physics.html").read_text()
    assert not (site / "old.html").exists()
    assert not (site / "helper.html").exists()
    assert not (site / "physics notes").exists()
    for name in ("entropy", "keynote", "book"):
        assert "Nested helper content." in _pdf_text(site / "pdfs" / f"{name}.pdf")
        assert (root / ".demolab" / "pdfs" / f"{name}.pdf").is_file()
    site_before = {p.relative_to(site): _sha256(p) for p in site.rglob("*") if p.is_file()}
    result = _cli(nested, "build", "entropy")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "site and book not updated" in result.stdout
    assert site_before == {p.relative_to(site): _sha256(p) for p in site.rglob("*") if p.is_file()}
    assert before == {p: _sha256(p) for p in before}


def test_nested_default_writings_keep_broken_entry_isolation(tmp_path):
    _assemble(tmp_path, demo=False)
    nested = tmp_path / "writings" / "nested"
    nested.mkdir()
    (nested / "helper.typ").write_text('#let broken = image("/assets/missing.svg")\n')
    (nested / "bad.typ").write_text('#import "helper.typ": broken\n'
        '#let meta = (title: "Bad", created_at: "2026-08-27")\n#let body = [#broken]\n')
    (nested / "good.typ").write_text(
        '#let meta = (title: "Good", created_at: "2026-08-27")\n#let body = [Good nested article.]\n')
    _build(tmp_path)
    site = tmp_path / ".demolab" / "site"
    assert "failed to build" in (site / "bad.html").read_text()
    assert "Good nested article." in (site / "good.html").read_text()
    assert not (site / "pdfs" / "bad.pdf").exists()
    assert not (site / "helper.html").exists()


def test_switching_source_root_prunes_outputs_and_failed_build_preserves_site(tmp_path):
    _assemble(tmp_path, demo=False)
    config = tmp_path / "demolab.yaml"
    first = tmp_path / "writings" / "one" / "old.typ"
    first.parent.mkdir()
    first.write_text('#let meta = (title: "Old", created_at: "2026-08-27", collection: "old-group")\n'
                     '#let body = [Old content.]\n')
    _build(tmp_path)
    site = tmp_path / ".demolab" / "site"
    assert (site / "old.html").exists() and (site / "old-group.html").exists()
    assert (site / "pdfs" / "old.pdf").exists()
    second = tmp_path / "articles" / "two" / "new.typ"
    second.parent.mkdir(parents=True)
    second.write_text('#let meta = (title: "New", created_at: "2026-08-27", collection: "new-group")\n'
                      '#let body = [New content.]\n')
    config.write_text("writings: articles\n")
    _build(tmp_path)
    assert (site / "new.html").exists()
    assert not (site / "old.html").exists()
    assert not (site / "old-group.html").exists()
    assert not (site / "pdfs" / "old.pdf").exists()
    assert not (tmp_path / ".demolab" / "pdfs" / "old.pdf").exists()
    before = {p.relative_to(site): _sha256(p) for p in site.rglob("*") if p.is_file()}
    duplicate = second.parent.parent / "new.typ"
    duplicate.write_text(second.read_text())
    result = _build_result(tmp_path)
    assert result.returncode != 0 and "duplicate writing ID" in result.stderr
    assert str(second) in result.stderr and str(duplicate) in result.stderr
    assert before == {p.relative_to(site): _sha256(p) for p in site.rglob("*") if p.is_file()}
    duplicate.unlink()
    # A template/config error after discovery also leaves the prior site untouched.
    config.write_text("writings: articles\nindex:\n  mode: unsupported\n")
    result = _build_result(tmp_path)
    assert result.returncode != 0
    assert before == {p.relative_to(site): _sha256(p) for p in site.rglob("*") if p.is_file()}
    config.write_text("writings: articles\n")
    moved = second.parent.parent / "new.typ"
    second.rename(moved)
    _build(tmp_path)
    assert before == {p.relative_to(site): _sha256(p) for p in site.rglob("*") if p.is_file()}
    moved.unlink()
    _build(tmp_path)
    assert not (site / "new.html").exists()
    assert not (site / "new-group.html").exists()
    assert not (site / "all.html").exists()
    assert not (site / "pdfs" / "book.pdf").exists()
    assert "under articles/" in (site / "index.html").read_text()
    assert first.is_file()  # switching roots never deletes user-owned sources


def _pdf_text(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    proc = subprocess.run(
        [pdftotext, str(path), "-"], capture_output=True, text=True, check=True,
    )
    return proc.stdout


def test_complete_build_is_reproducible_and_copies_assets(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    legacy_bundle = root / "temp" / "bundle"
    legacy_bundle.mkdir(parents=True)
    (legacy_bundle / "stale.txt").write_text("old engine scratch")
    legacy_demo = root / "temp" / "demo-preview"
    legacy_demo.mkdir()
    (legacy_demo / "stale.txt").write_text("old demo scratch")
    (root / "temp" / "experiment.txt").write_text("preserve user scratch")
    _build(root)
    assert (root / ".demolab" / "site" / "index.html").is_file()
    assert not (root / "artifacts" / "site").exists()
    assert not legacy_bundle.exists()
    assert not legacy_demo.exists()
    assert (root / "temp" / "experiment.txt").read_text() == "preserve user scratch"
    assert (root / ".demolab" / "bundle" / "main.typ").is_file()
    assert (root / ".demolab" / "bundle" / "index.json").is_file()
    first = {p.name: _sha256(p) for p in (root / ".demolab" / "pdfs").glob("*.pdf")}
    stale_pdf = root / ".demolab" / "pdfs" / "removed-entry.pdf"
    stale_pdf.write_bytes(b"stale")
    _build(root)
    second = {p.name: _sha256(p) for p in (root / ".demolab" / "pdfs").glob("*.pdf")}
    assert first == second
    assert not stale_pdf.exists()
    site = root / ".demolab" / "site"
    assert (site / "first-observation.html").exists()
    assert "Writings" in (site / "all.html").read_text()
    assert "Experiments" not in (site / "all.html").read_text()
    assert 'class="theme-docs"' in (site / "create-a-page.html").read_text()
    assert 'class="theme-docs"' in (site / "guides.html").read_text()
    assert 'class="theme-docs"' not in (site / "examples.html").read_text()
    homepage = (site / "index.html").read_text()
    assert 'href="examples"' in homepage
    assert 'href="guides"' in homepage
    assert 'href="first-observation"' in homepage
    assert '<nav class="site-links" aria-label="Site links">' in homepage
    assert '<a href="https://github.com/eoinmurray/demolab">Source</a>' in homepage
    assert 'href="create-a-page"' in (site / "all.html").read_text()


@pytest.mark.parametrize("source_layout", [False, True])
def test_source_demo_renders_fresh_stub_collections(
    tmp_path: Path, source_layout: bool,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    (_assemble_demo if source_layout else _assemble)(root)
    layout = _paths.layout_for(root)
    inputs = [p for p in layout.content.rglob("*") if p.is_file()]
    before = {p: _sha256(p) for p in inputs}
    assert not (layout.content / "data").exists()
    assert not (layout.content / "scripts").exists()
    assert preview_config_absent(layout.config)
    _build(root)
    manifest = json.loads((root / ".demolab" / "bundle" / "index.json").read_text())
    assert all("error" not in entry for entry in manifest["entries"])
    site = root / ".demolab" / "site"
    ids = {"first-observation", "planned-study", "create-a-page", "organise-collections"}
    assert {entry["id"] for entry in manifest["entries"]} == ids
    assert all((site / f"{entry_id}.html").is_file() for entry_id in ids)
    assert all((site / "pdfs" / f"{entry_id}.pdf").is_file() for entry_id in ids)
    assert 'href="first-observation"' in (site / "examples.html").read_text()
    guides = (site / "guides.html").read_text()
    assert guides.index('href="create-a-page"') < guides.index('href="organise-collections"')
    assert before == {p: _sha256(p) for p in inputs}
    if source_layout:
        assert not (root / ".demo" / ".demolab").exists()
        assert not (root / "writings").exists()
        assert not (root / ".artifacts").exists()
        assert not (root / "demolab.yaml").exists()


def preview_config_absent(config: Path) -> bool:
    return "preview:" not in config.read_text() and "build:" not in config.read_text()


def test_demo_cli_clean_and_rebuild_preserve_inputs_from_nested_directory(tmp_path: Path) -> None:
    root = tmp_path / "engine"
    _assemble_demo(root)
    demo = root / ".demo"
    before = {p.relative_to(demo): _sha256(p) for p in demo.rglob("*") if p.is_file()}
    proc = _cli(demo / "writings", "build", "first-observation")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "State what was observed" in _pdf_text(root / ".demolab/pdfs/first-observation.pdf")
    proc = _cli(root, "build")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    proc = _cli(demo / "writings", "clean")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (root / ".demolab").exists()
    assert before == {p.relative_to(demo): _sha256(p) for p in demo.rglob("*") if p.is_file()}
    proc = _cli(demo, "build")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (root / ".demolab/site/index.html").is_file()
    assert not (demo / ".demolab").exists()
    assert before == {p.relative_to(demo): _sha256(p) for p in demo.rglob("*") if p.is_file()}


def test_demo_layout_reaches_assets_landing_decks_and_pdf_config(tmp_path: Path) -> None:
    root = tmp_path / "engine"
    _assemble_demo(root)
    demo = root / ".demo"
    assets = demo / "assets"
    assets.mkdir()
    (assets / "example.txt").write_text("Demo static asset\n")
    (demo / "landing.typ").write_text('#let body = [Demo landing page]\n')
    (demo / "writings" / "demo.slide.typ").write_text(
        '#let meta = (title: "Demo deck", created_at: "2026-08-27")\n'
        'A minimal demo deck.\n'
    )
    _build(root)
    site = root / ".demolab" / "site"
    assert "Demo landing page" in (site / "index.html").read_text()
    assert (site / "example.txt").read_text() == "Demo static asset\n"
    assert "minimal demo deck" in _pdf_text(site / "pdfs/demo.pdf")
    assert "State what was observed" in _pdf_text(site / "pdfs/book.pdf")
    (demo / "demolab.yaml").write_text("name: Web demo\npdfs: false\n")
    proc = _cli(root, "build", "first-observation")
    assert proc.returncode != 0
    assert "PDF publishing is disabled" in proc.stderr
    _build(root)
    assert not (site / "pdfs").exists()
    assert "Web demo" in (site / "index.html").read_text()


@pytest.mark.parametrize(
    ("source", "expected"),
    ((None, "Selected 11"), ("benchmark-a-run-002", "Selected 22"),
     ("missing-run", None), ("../outside", None)),
)
def test_data_file_sources_are_optional_and_never_fall_back(
    tmp_path: Path, source: str | None, expected: str | None,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text("name: Source mapping\npdfs: false\n")
    artifacts = root / ".artifacts"
    for directory, value in (("benchmark-a", 11), ("benchmark-a-run-002", 22)):
        path = artifacts / directory / "numbers.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"value": value}))
    outside = root / "outside" / "numbers.json"
    outside.parent.mkdir()
    outside.write_text(json.dumps({"value": 99}))
    binding = ("#let source-file = data-file\n" if source is None else
               f'#let source-file = data-file.with(sources: ("benchmark-a": "{source}"))\n')
    (root / "writings" / "mapped.typ").write_text(
        '#import "/.demolab/lib.typ": *\n'
        '#let meta = (title: "Mapped", created_at: "2026-08-27")\n'
        + binding
        + '#let result = json(source-file("benchmark-a/numbers.json"))\n'
          '#let body = [Selected #result.value]\n'
    )
    _build(root)
    page = (root / ".demolab/site/mapped.html").read_text()
    if expected is None:
        assert "failed to build" in page.lower()
        assert all(value not in page for value in ("Selected 11", "Selected 22", "Selected 99"))
    else:
        assert expected in page


@pytest.mark.parametrize(
    ("config", "message"),
    (
        (
            "collections:\n  parent:\n    children: [missing]\n",
            "collection 'parent' has unknown child 'missing'",
        ),
        (
            "collections:\n"
            "  first:\n    children: [child]\n"
            "  second:\n    children: [child]\n"
            "  child: {}\n",
            "collection 'child' has duplicate parentage",
        ),
        (
            "collections:\n"
            "  first:\n    children: [second]\n"
            "  second:\n    children: [third]\n"
            "  third:\n    children: [first]\n",
            "collection cycle:",
        ),
    ),
)
def test_nested_collection_graph_validation(tmp_path: Path, config: str, message: str) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(config)
    proc = _build_result(root)
    assert proc.returncode != 0
    assert message in proc.stderr


def test_flat_collection_config_remains_backward_compatible(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "collections:\n  notes:\n    label: Notes\n    description: Flat collection.\n"
    )
    (root / "writings" / "note.typ").write_text(
        '#let meta = (title: "Note", created_at: "2026-08-26", collection: "notes")\n'
        '#let body = [Body.]\n'
    )
    _build(root)
    site = root / ".demolab" / "site"
    assert (site / "notes.html").exists()
    assert 'href="notes">Notes</a>' in (site / "index.html").read_text()
    assert 'href="note">Note</a>' in (site / "notes.html").read_text()


def test_docs_theme_changes_skin_without_changing_functional_markup(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "name: Theme parity\npdfs: false\ncollections:\n"
        "  plain:\n    label: Plain\n    description: Same description.\n"
        "  docs:\n    label: Docs\n    description: Same description.\n    theme: docs\n"
    )
    for entry_id, collection in (("plain-note", "plain"), ("docs-note", "docs")):
        (root / "writings" / f"{entry_id}.typ").write_text(
            '#let meta = (title: "Same title", created_at: "2026-08-26", '
            f'collection: "{collection}", status: "ExpStudy")\n'
            '#let body = [Same body.\n\n== Same section\n\nSame text.]\n'
        )

    _build(root)
    site = root / ".demolab" / "site"

    def functional_body(path: Path) -> str:
        body = path.read_text().split("<body>", 1)[1]
        body = re.sub(r'<div class="theme-docs" aria-hidden="true"></div>', "", body)
        return (body
                .replace("plain-note", "entry").replace("docs-note", "entry")
                .replace('href="plain"', 'href="collection"')
                .replace('href="docs"', 'href="collection"')
                .replace(">Plain<", ">Collection<").replace(">Docs<", ">Collection<"))

    assert functional_body(site / "plain-note.html") == functional_body(site / "docs-note.html")
    assert functional_body(site / "plain.html") == functional_body(site / "docs.html")


def test_targeted_build_accepts_an_ordinary_slug(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    shutil.rmtree(root / ".demolab" / "pdfs", ignore_errors=True)
    _build(root, "first-observation")
    assert sorted(p.name for p in (root / ".demolab" / "pdfs").glob("*.pdf")) == ["first-observation.pdf"]
    assert not (root / ".demolab" / "site").exists()


def test_web_only_build_prunes_site_pdfs_but_preserves_shareable_files(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    _build(root)
    (root / "demolab.yaml").write_text(
        (root / "demolab.yaml").read_text() + "\npdfs: false\n", encoding="utf-8"
    )
    generated = root / ".demolab" / "pdfs"
    shutil.rmtree(generated)
    generated.mkdir(parents=True)
    generated_sentinel = generated / "existing.pdf"
    generated_sentinel.write_bytes(b"keep")
    legacy = root / "artifacts" / "pdfs"
    legacy.mkdir(parents=True)
    legacy_sentinel = legacy / "committed.pdf"
    legacy_sentinel.write_bytes(b"keep legacy")
    _build(root)
    site = root / ".demolab" / "site"
    assert not (site / "pdfs").exists()
    assert generated_sentinel.read_bytes() == b"keep"
    assert legacy_sentinel.read_bytes() == b"keep legacy"
    assert 'class="row-pdf"' not in (site / "all.html").read_text()
    assert 'class="entry-pdf"' not in (site / "first-observation.html").read_text()


def test_targeted_pdf_rejects_web_only_presentation(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    (root / "demolab.yaml").write_text("name: Test\npdfs: false\n")
    proc = subprocess.run(
        [sys.executable, "-m", "demolab_cli.build", "first-observation"],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "PDF publishing is disabled" in proc.stderr


def test_bad_writing_is_stubbed_without_taking_down_site(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    _unpin_demo(root)
    (root / "writings" / "broken.typ").write_text(
        '#let meta = (title: "Broken title", date: "2026-08-23", collection: "examples", '
        'status: "ExpStudy", tags: ("diagnostics",))\n'
        '#let body = [#image("/assets/missing.svg")]\n'
    )
    _build(root)
    site = root / ".demolab" / "site"
    assert (site / "first-observation.html").exists()
    assert (site / "broken.html").exists()
    assert "failed to build" in (site / "broken.html").read_text().lower()
    assert "broken" in (site / "broken.html").read_text()
    for listing in ("index.html", "all.html", "uncategorized.html"):
        html = (site / listing).read_text()
        assert 'href="broken"' in html
        assert "build error" in html
        assert 'pdfs/broken.pdf' not in html


def test_only_broken_writing_has_navigation_but_no_pdf_links(tmp_path: Path) -> None:
    _assemble(tmp_path, demo=False)
    (tmp_path / "writings/broken.typ").write_text(
        '#let meta = (title: "Broken", created_at: "2026-09-03")\n'
        '#let body = [#image("/assets/missing.svg")]\n')
    _build(tmp_path)
    site = tmp_path / ".demolab/site"
    index = (site / "index.html").read_text()
    assert 'href="uncategorized"' in index
    assert 'href="pdfs/book.pdf"' not in index
    for listing in ("all.html", "uncategorized.html"):
        html = (site / listing).read_text()
        assert 'href="broken"' in html and "build error" in html
        assert 'pdfs/broken.pdf' not in html
    assert not (site / "pdfs/book.pdf").exists()


def test_pdfs_config_defaults_on_and_validates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(build, "LAYOUT", _paths.layout_for(tmp_path))
    assert build.pdfs_enabled() is True
    (tmp_path / "demolab.yaml").write_text("pdfs: false\n")
    assert build.pdfs_enabled() is False
    (tmp_path / "demolab.yaml").write_text("pdfs: sometimes\n")
    with pytest.raises(SystemExit, match="must be true or false"):
        build.pdfs_enabled()


def test_source_date_epoch_overrides_default(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1234567890")
    assert build.typst_compile("input.typ")[3] == "1234567890"


def test_status_is_visible_artifact_lifecycle(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text("name: Test\npdfs: false\n")
    stages = (
        ("untyped", None),
        ("study", "ExpStudy"),
        ("study-plan", "ExpStudyPlan"),
        ("scout", "ExpScout"),
        ("scout-plan", "ExpScoutPlan"),
    )
    for entry_id, status in stages:
        status_field = "" if status is None else f', status: "{status}"'
        (root / "writings" / f"{entry_id}.typ").write_text(
            f'#let meta = (title: "{entry_id}", created_at: "2026-08-24", '
            f'collection: "lifecycle"{status_field})\n#let body = [Body.]\n'
        )

    _build(root)

    page = (root / ".demolab" / "site" / "lifecycle.html").read_text()
    expected = ("scout-plan", "scout", "study-plan", "study", "untyped")
    positions = [page.index(f'href="{entry_id}"') for entry_id in expected]
    assert positions == sorted(positions)
    for status in ("ExpScoutPlan", "ExpScout", "ExpStudyPlan", "ExpStudy"):
        assert f'class="status">{status}</span>' in page
    assert 'class="status">final</span>' not in page
    rows = [ET.fromstring(row) for row in re.findall(r'<li class="entry-row">.*?</li>', page, re.S)]
    assert len(rows) == len(stages)
    for row, entry_id in zip(rows, expected):
        heading = row.find('./div[@class="row-heading"]')
        metadata = row.find('./div[@class="row-meta"]')
        assert heading.find('.//a[@class="row-pdf"]') is None
        assert metadata.find('.//a[@class="row-pdf"]') is None
        assert metadata.find('.//span[@class="row-id"]').text == f"#{entry_id}"
        assert metadata.find('.//span[@class="status"]') is None
        status = heading.find('.//span[@class="status"]')
        assert (status.text if status is not None else None) == dict(stages)[entry_id]
        article = (root / ".demolab" / "site" / f"{entry_id}.html").read_text()
        header = ET.fromstring(re.search(r'<header class="article-header">.*?</header>', article, re.S)[0])
        assert header.find('./div[@class="row-heading"]//span[@class="status"]') is None
        article_metadata = header.find('./div[@class="entry-meta"]/div[@class="row-meta"]')
        article_status = article_metadata.find('./span[@class="status"]')
        assert (article_status.text if article_status is not None else None) == dict(stages)[entry_id]
        if article_status is not None:
            collection_index = list(article_metadata).index(article_metadata.find('./a[@class="entry-collection"]'))
            assert article_metadata[collection_index + 1] is article_status


def test_tags_render_as_cross_collection_navigation(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "name: Tagged lab\ncollections:\n  notes:\n    label: Notes\n  guides:\n    label: Guides\n"
    )
    writings = root / "writings"
    (writings / "alpha.typ").write_text(
        '#let meta = (title: "Alpha", created_at: "2026-09-01", collection: "notes", '
        'status: "ExpScout", tags: ("methods", "shared-topic", "v35.0.0"))\n'
        '#let body = [Alpha body.]\n'
    )
    (writings / "beta.typ").write_text(
        '#let meta = (title: "Beta", created_at: "2026-09-02", collection: "guides", '
        'tags: ("shared-topic",))\n#let body = [Beta body.]\n'
    )
    (writings / "untagged.typ").write_text(
        '#let meta = (title: "Untagged", created_at: "2026-09-03", collection: "notes")\n'
        '#let body = [No tags.]\n'
    )
    (writings / "talk.slide.typ").write_text(
        '#let meta = (title: "Talk", created_at: "2026-09-03", tags: ("shared-topic",))\n'
        'Tagged slide.\n'
    )

    _build(root)
    site = root / ".demolab" / "site"
    assert (site / "tags.html").is_file()
    assert (site / "tags" / "methods.html").is_file()
    assert (site / "tags" / "shared-topic.html").is_file()
    assert (site / "tags" / "v35.0.0.html").is_file()
    directory = (site / "tags.html").read_text()
    assert 'href="tags/methods">methods</a>' in directory
    assert 'href="tags/shared-topic">shared-topic</a>' in directory
    assert 'href="tags/v35.0.0">v35.0.0</a>' in directory
    assert "3 entries" in directory

    shared = (site / "tags" / "shared-topic.html").read_text()
    assert 'href="../alpha"' in shared and 'href="../beta"' in shared
    assert 'href="../pdfs/talk.pdf"' in shared
    assert 'href="../untagged"' not in shared
    assert 'href="../notes">Notes</a>' in shared
    assert 'href="../guides">Guides</a>' in shared
    assert 'href="../favicon.svg"' in shared
    assert 'src="../cite-popover.js"' in shared
    assert 'src="../image-lightbox.js"' in shared

    alpha = (site / "alpha.html").read_text()
    assert '<span class="entry-tags"><a class="tag" href="tags/methods">methods</a> ' in alpha
    assert '<a class="tag" href="tags/shared-topic">shared-topic</a> ' in alpha
    assert '<a class="tag" href="tags/v35.0.0">v35.0.0</a></span>' in alpha
    assert 'class="row-tags"' in (site / "notes.html").read_text()
    assert "methods" in _pdf_text(site / "pdfs" / "alpha.pdf")
    assert 'href="tags">Browse tags</a>' in (site / "index.html").read_text()


@pytest.mark.parametrize(
    ("tags", "message"),
    (
        ('"methods"', "meta.tags must be a list"),
        ('("Not-Lowercase",)', "meta.tags values must be lowercase slugs"),
        ('("v35..0",)', "meta.tags values must be lowercase slugs"),
        ('("shared", "other", "shared")', "meta.tags must not contain duplicates"),
    ),
)
def test_invalid_tags_fail_the_build_clearly(
    tmp_path: Path, tags: str, message: str,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "writings" / "invalid.typ").write_text(
        '#let meta = (title: "Invalid", created_at: "2026-09-03", tags: ' + tags + ')\n'
        '#let body = [Invalid tags.]\n'
    )
    result = _build_result(root)
    assert result.returncode != 0
    assert message in result.stderr


def test_tags_writing_id_is_reserved_when_tags_are_used(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "writings" / "tags.typ").write_text(
        '#let meta = (title: "Tags", created_at: "2026-09-03", tags: ("methods",))\n'
        '#let body = [Reserved path.]\n'
    )
    result = _build_result(root)
    assert result.returncode != 0
    assert "writing ID 'tags' is reserved" in result.stderr


@pytest.mark.parametrize(
    ("created", "updated", "created_text", "updated_text"),
    (
        ("2026-08-24", "2026-08-27", "24 August 2026", "27 August 2026"),
        ("2026-08-24T12:30:45+02:00", "2026-08-24T11:00:00Z",
         "24 August 2026 at 12:30 pm", "24 August 2026 at 11:00 am"),
        ("2026-08-24", "2026-08-24T01:30-03:30",
         "24 August 2026", "24 August 2026 at 1:30 am"),
        ("2026-08-24T12:30:45.123456789Z", "2026-08-25",
         "24 August 2026 at 12:30 pm", "25 August 2026"),
        ("2026-12-31T23:30:00-02:00", "2027-01-01T01:30:00Z",
         "31 December 2026 at 11:30 pm", "1 January 2027 at 1:30 am"),
        ("2026-08-24T12:00:00.100Z", "2026-08-24T12:00:00.1+00:00",
         "24 August 2026 at 12:00 pm", "24 August 2026 at 12:00 pm"),
        ("2026-08-28T00:00:00.000Z", "2026-08-28T12:00:00Z",
         "28 August 2026 at 12:00 am", "28 August 2026 at 12:00 pm"),
        ("2026-08-28T14:30:00+02:00", "2026-08-28T14:30:05.120+02:00",
         "28 August 2026 at 2:30 pm", "28 August 2026 at 2:30 pm"),
    ),
)
def test_authored_dates_render_consistently_with_semantic_html(
    tmp_path: Path, created: str, updated: str, created_text: str, updated_text: str,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "name: Dates\nindex:\n  mode: expanded\n  recent: 4\n"
    )
    writings = root / "writings"
    (writings / "changed.typ").write_text(
        '#let meta = (title: "From simplified to brainlike input in a PING network", '
        f'created_at: "{created}", updated_at: "{updated}", '
        'status: "[DATA]", collection: "dates")\n#let body = [Body.]\n'
    )
    (writings / "initial.typ").write_text(
        f'#let meta = (title: "Initial", created_at: "{created}", '
        'collection: "dates")\n#let body = [Body.]\n'
    )
    (writings / "unchanged.typ").write_text(
        '#let meta = (title: "Unchanged", created_at: "2026-08-24", '
        'updated_at: "2026-08-24", collection: "dates")\n#let body = [Body.]\n'
    )
    (writings / "legacy.typ").write_text(
        '#let meta = (title: "Legacy", date: "2026-08-23", '
        'collection: "dates")\n#let body = [Body.]\n'
    )

    _build(root)

    site = root / ".demolab" / "site"
    changed = (site / "changed.html").read_text()
    listing = (site / "dates.html").read_text()

    def compact_date(value: str, display: str) -> str:
        calendar = datetime.fromisoformat(value[:10])
        return (display.replace(calendar.strftime("%B"), calendar.strftime("%b"))
                .replace(" at ", ", ").replace(calendar.strftime("%Y"), calendar.strftime("%y")))

    article_dates = {
        "changed": (("Created", created, created_text), ("Updated", updated, updated_text)),
        "initial": (("Created", created, created_text),),
        "unchanged": (("Created", "2026-08-24", "24 August 2026"),
                      ("Updated", "2026-08-24", "24 August 2026")),
        "legacy": (("Created", "2026-08-23", "23 August 2026"),),
    }
    for entry_id, expected_dates in article_dates.items():
        article = (site / f"{entry_id}.html").read_text()
        assert 'class="home-link"' not in article
        header = ET.fromstring(re.search(r'<header class="article-header">.*?</header>', article, re.S)[0])
        assert header.find('.//h2') is not None
        assert header.find('.//span[@class="row-id"]').text == f"#{entry_id}"
        metadata = header.find('./div[@class="entry-meta"]/div[@class="row-meta"]')
        assert metadata.find('./a[@class="entry-collection"]').get("href") == "dates"
        status = metadata.find('./span[@class="status"]')
        assert (status.text if status is not None else None) == ("[DATA]" if entry_id == "changed" else None)
        if status is not None:
            assert metadata[2] is status
        assert header.find('./div[@class="row-heading"]//span[@class="status"]') is None
        assert metadata[-1].get("class") == "entry-pdf"
        assert metadata[-1].get("href") == f"pdfs/{entry_id}.pdf"
        assert metadata.find('.//time') is None
        assert header.find('./div[@class="row-heading"]//time') is None
        dates = header.findall('./div[@class="entry-meta"]/div[@class="article-dates"]/div[@class="article-date"]')
        assert len(dates) == len(expected_dates)
        for date, (label, value, display) in zip(dates, expected_dates):
            assert "".join(date.itertext()) == f"{label} {compact_date(value, display)}"
            assert date.find('./time').get("datetime") == value
            assert date.find('./time').get("title") == f"{label} {display}"
    homepage = (site / "index.html").read_text()
    summaries = {
        "changed": ("Updated", updated, updated_text),
        "initial": ("Created", created, created_text),
        "unchanged": ("Updated", "2026-08-24", "24 August 2026"),
        "legacy": ("Created", "2026-08-23", "23 August 2026"),
    }
    for page in (listing, homepage, (site / "all.html").read_text()):
        headings = re.findall(r'<div class="entry-list-heading"[^>]*>Last changed</div>', page)
        if page == homepage:
            assert not headings
            assert 'class="entry-list-heading"' not in page
        else:
            assert len(headings) == 1
            assert page.index('class="entry-list-heading"') < page.index('<ul class="entry-list">')
        rows = [ET.fromstring(row) for row in re.findall(r'<li class="entry-row">.*?</li>', page, re.S)]
        assert rows
        for row in rows:
            entry_id = row.find('.//span[@class="row-id"]').text.removeprefix("#")
            label, value, display = summaries[entry_id]
            compact = compact_date(value, display)
            date = row.find('.//span[@class="row-date"]')
            assert "".join(date.itertext()) == compact
            times = row.findall('.//time')
            assert len(times) == 1
            assert times[0].get("datetime") == value
            assert times[0].get("title") == f"{label} {display}"
    assert "Created <time" not in listing
    assert '<a class="entry-collection" href="dates">Dates</a>' in changed

    if shutil.which("pdftotext") is not None:
        expected_pdf = f"Created {created_text} · Updated {updated_text}"
        assert expected_pdf in " ".join(_pdf_text(site / "pdfs" / "changed.pdf").split())
        book = " ".join(_pdf_text(site / "pdfs" / "book.pdf").split())
        assert expected_pdf in book
        assert "Created 24 August 2026 · Updated 24 August 2026" in _pdf_text(
            site / "pdfs" / "unchanged.pdf"
        )
        assert "Created 24 August 2026 · Updated 24 August 2026" in book
        assert "Created 23 August 2026" in book


@pytest.mark.parametrize(
    ("created", "updated", "message"),
    (
        ("2026-02-30", None, "date is invalid"),
        ("24-08-2026", None, "ISO calendar date"),
        ("2026-08-24", "2026-08-23", "must not be earlier"),
        ("2026-08-24T12:00:00", None, "timezone"),
        ("2026-08-24T12:00:00+24:00", None, "invalid timezone offset"),
        ("2026-08-24T12:00:00-01:60", None, "invalid timezone offset"),
        ("2026-02-30T12:00:00Z", None, "date is invalid"),
        ("2026-08-24T24:00:00Z", None, "hour"),
        ("2026-08-24T12:60:00Z", None, "minute"),
        ("2026-08-24T12:00:60Z", None, "second"),
        ("2026-08-24T12:00:00.Z", None, "ISO"),
        ("2026-08-24T12:00:00Zjunk", None, "ISO"),
        ("2026-08-24", "2026-08-24T00:30:00+01:00", "must not be earlier"),
        ("2026-08-24T01:00:00Z", "2026-08-24", "must not be earlier"),
        ("2026-08-24T12:00:00Z", "2026-08-24T13:00:00+02:00", "must not be earlier"),
        ("2026-08-24T12:00:00.000000002Z", "2026-08-24T12:00:00.000000001Z",
         "must not be earlier"),
    ),
)
def test_authored_dates_reject_invalid_values(
    tmp_path: Path, created: str, updated: str | None, message: str,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    updated_field = "" if updated is None else f', updated_at: "{updated}"'
    (root / "writings" / "invalid.typ").write_text(
        f'#let meta = (title: "Invalid", created_at: "{created}"{updated_field})\n'
        '#let body = [Body.]\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "demolab_cli.build", "invalid"],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert message in proc.stderr


def test_default_homepage_remains_collection_directory(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text("name: Test\npdfs: false\n")
    (root / "writings" / "note.typ").write_text(
        '#let meta = (title: "Note", created_at: "2026-08-24", collection: "notes")\n'
        '#let body = [Body.]\n'
    )

    _build(root)

    index = (root / ".demolab" / "site" / "index.html").read_text()
    assert '<ul class="coll-list">' in index
    assert "Recent" not in index
    assert 'href="note"' not in index


@pytest.mark.parametrize(
    ("alpha_updated", "beta_created", "gamma_created"),
    (
        ("2026-08-27", "2026-08-26", "2026-08-26"),
        ("2026-08-27T01:00:00Z", "2026-08-27T02:00:00+02:00", "2026-08-26T19:00:00-05:00"),
        ("2026-08-27T00:00:00.000000002Z", "2026-08-27T00:00:00.0000000010Z",
         "2026-08-27T00:00:00.000000001Z"),
    ),
)
def test_expanded_homepage_recent_and_collection_ordering(
    tmp_path: Path, alpha_updated: str, beta_created: str, gamma_created: str,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "name: Test\ncollection-order: [second, work, slides]\n"
        "collections:\n  second:\n    label: Second collection\n"
        "    description: Listed first.\n"
        "index:\n  mode: expanded\n  recent: 2\n"
    )
    writings = root / "writings"
    entries = (
        ("alpha", "2026-08-24", alpha_updated, "work", "ExpStudy"),
        ("beta", beta_created, None, "work", "ExpScoutPlan"),
        ("gamma", gamma_created, None, "work", "ExpStudy"),
        ("delta", "2026-08-20", None, "second", None),
    )
    for entry_id, created, updated, collection, status in entries:
        updated_field = "" if updated is None else f', updated_at: "{updated}"'
        status_field = "" if status is None else f', status: "{status}"'
        (writings / f"{entry_id}.typ").write_text(
            f'#let meta = (title: "{entry_id}", created_at: "{created}"{updated_field}, '
            f'collection: "{collection}"{status_field})\n#let body = [Body.]\n'
        )
    (writings / "talk.slide.typ").write_text(
        '#let meta = (title: "Talk", created_at: "2026-08-28", collection: "slides")\n'
        '#set page(width: 16cm, height: 9cm)\n= Talk\n'
    )

    _build(root)

    index_path = root / ".demolab" / "site" / "index.html"
    index = index_path.read_text()
    assert "Recently worked on" not in index
    assert 'class="entry-list-heading"' not in index
    assert (root / ".demolab" / "site" / "all.html").read_text().count('class="entry-list-heading"') == 1
    recent = index[index.index("Recent"):index.index('href="second"')]
    assert recent.index('href="alpha"') < recent.index('href="gamma"')
    assert 'href="beta"' not in recent
    assert 'href="talk"' not in recent
    assert index.index('<h3><a href="second"') < index.index('<h3><a href="work"')
    assert '<a class="row-collection" href="work">Work</a>' in recent
    recent_rows = [ET.fromstring(row) for row in re.findall(r'<li class="entry-row">.*?</li>', recent, re.S)]
    for row in recent_rows:
        heading = row.find('./div[@class="row-heading"]')
        metadata = row.find('./div[@class="row-meta"]')
        entry_id = metadata.find('.//span[@class="row-id"]').text.removeprefix("#")
        assert heading.find('.//a[@class="row-title"]').get("href") == entry_id
        assert heading.find('.//a[@class="row-pdf"]') is None
        identity = metadata.find('./span[@class="row-identity"]')
        assert identity[-1].get("class") == "row-pdf"
        assert identity[-1].get("href") == f"pdfs/{entry_id}.pdf"
        assert metadata.find('.//a[@class="row-collection"]').text == "Work"
        assert heading.find('./span[@class="row-date"]/time') is not None
        assert metadata.find('.//time') is None
    assert index.index('href="work"') < index.index('href="slides"')
    assert "Second collection" in index and "Listed first." in index
    work = index[index.index('href="work"'):index.index('href="slides"')]
    assert work.index('href="gamma"') < work.index('href="beta"')
    assert work.index('href="beta"') < work.index('href="alpha"')
    assert "ExpScoutPlan" in work and "ExpStudy" in work
    slides = index[index.index('href="slides"'):]
    assert 'href="pdfs/talk.pdf"' in slides

    # Filesystem/build activity cannot affect authored-date ranking.
    os.utime(writings / "beta.typ", (2_000_000_000, 2_000_000_000))
    _build(root)
    rebuilt = index_path.read_text()
    rebuilt_recent = rebuilt[
        rebuilt.index("Recent"):rebuilt.index('href="second"')
    ]
    assert rebuilt_recent.index('href="alpha"') < rebuilt_recent.index('href="gamma"')
    assert 'href="beta"' not in rebuilt_recent


@pytest.mark.parametrize("recent_line", ("", "  recent: 0\n"))
def test_expanded_homepage_can_omit_recent_section(
    tmp_path: Path, recent_line: str,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "name: Test\npdfs: false\nindex:\n  mode: expanded\n" + recent_line
    )
    (root / "writings" / "note.typ").write_text(
        '#let meta = (title: "Note", created_at: "2026-08-24", collection: "notes")\n'
        '#let body = [Body.]\n'
    )

    _build(root)

    index = (root / ".demolab" / "site" / "index.html").read_text()
    assert "Recent" not in index
    assert 'href="note"' in index
    assert 'class="entry-list-heading"' not in index


def test_expanded_homepage_rejects_negative_recent(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    (root / "demolab.yaml").write_text(
        "name: Test\npdfs: false\nindex:\n  mode: expanded\n  recent: -1\n"
    )
    (root / "writings" / "note.typ").write_text(
        '#let meta = (title: "Note", created_at: "2026-08-24", collection: "notes")\n'
        '#let body = [Body.]\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "demolab_cli.build"],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "index.recent' must be a non-negative integer" in proc.stderr
