"""End-to-end tests for generic writings, assets, and optional PDFs."""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from demolab_cli import _paths, build

pytestmark = pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")


def _assemble(root: Path, *, demo: bool = True) -> None:
    shutil.copytree(_paths.SCAFFOLD / "skeleton", root, dirs_exist_ok=True)
    if demo:
        source = _paths.PACKAGE.parent
        shutil.copy2(source / "demolab.yaml", root / "demolab.yaml")
        shutil.copytree(source / "writings", root / "writings", dirs_exist_ok=True)
        shutil.copytree(source / "assets", root / "assets", dirs_exist_ok=True)


def _build(root: Path, entry: str | None = None) -> None:
    subprocess.run(
        [sys.executable, "-m", "demolab_cli.build", *([entry] if entry else [])],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, check=True,
    )


def _build_result(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "demolab_cli.build"],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    assert not legacy_bundle.exists()
    assert not legacy_demo.exists()
    assert (root / "temp" / "experiment.txt").read_text() == "preserve user scratch"
    assert (root / ".demolab" / "bundle" / "main.typ").is_file()
    assert (root / ".demolab" / "bundle" / "index.json").is_file()
    first = {p.name: _sha256(p) for p in (root / "artifacts" / "pdfs").glob("*.pdf")}
    _build(root)
    second = {p.name: _sha256(p) for p in (root / "artifacts" / "pdfs").glob("*.pdf")}
    assert first == second
    site = root / "artifacts" / "site"
    assert (site / "welcome.html").exists()
    assert (site / "assets" / "example.json").exists() or (site / "example.json").exists()
    assert "Writings" in (site / "all.html").read_text()
    assert "Experiments" not in (site / "all.html").read_text()
    assert 'class="theme-docs"' in (site / "api.html").read_text()
    assert 'class="theme-docs"' in (site / "documentation.html").read_text()
    assert 'class="theme-docs"' in (site / "pinglab-docs.html").read_text()
    assert 'class="theme-docs"' not in (site / "pages.html").read_text()
    homepage = (site / "index.html").read_text()
    assert homepage.count('href="documentation"') == 1  # header link only; directory stays hidden
    assert 'href="api"' not in homepage
    assert '<nav class="site-links" aria-label="Site links">' in homepage
    assert '<a href="documentation">Developer docs</a>' in homepage
    assert '<a href="https://github.com/eoinmurray/demolab">Source</a>' in homepage
    assert 'href="api"' in (site / "all.html").read_text()
    parent = (site / "documentation.html").read_text()
    children = ("pinglab-docs", "snnlang-docs", "snnsim-docs", "snnviz-docs")
    assert all((site / f"{child}.html").exists() for child in children)
    positions = [parent.index(f'href="{child}"') for child in children]
    assert positions == sorted(positions)
    assert "Pinglab docs" in parent and "Developer guides and API notes for Pinglab." in parent
    assert '<span class="coll-count">1 entry</span>' in parent
    assert parent.count('<span class="coll-count">0 entries</span>') == 3


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
    site = root / "artifacts" / "site"
    assert (site / "notes.html").exists()
    assert 'href="notes">Notes</a>' in (site / "index.html").read_text()
    assert 'href="note">Note</a>' in (site / "notes.html").read_text()


def test_targeted_build_accepts_an_ordinary_slug(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    shutil.rmtree(root / "artifacts" / "pdfs", ignore_errors=True)
    _build(root, "welcome")
    assert sorted(p.name for p in (root / "artifacts" / "pdfs").glob("*.pdf")) == ["welcome.pdf"]
    assert not (root / "artifacts" / "site").exists()


def test_web_only_build_prunes_site_pdfs_but_preserves_shareable_files(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    _build(root)
    (root / "demolab.yaml").write_text(
        (root / "demolab.yaml").read_text() + "\npdfs: false\n", encoding="utf-8"
    )
    committed = root / "artifacts" / "pdfs"
    shutil.rmtree(committed)
    committed.mkdir(parents=True)
    sentinel = committed / "existing.pdf"
    sentinel.write_bytes(b"keep")
    _build(root)
    site = root / "artifacts" / "site"
    assert not (site / "pdfs").exists()
    assert sentinel.read_bytes() == b"keep"
    assert 'class="row-pdf"' not in (site / "all.html").read_text()
    assert 'class="entry-pdf"' not in (site / "welcome.html").read_text()


def test_targeted_pdf_rejects_web_only_presentation(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    (root / "demolab.yaml").write_text("name: Test\npdfs: false\n")
    proc = subprocess.run(
        [sys.executable, "-m", "demolab_cli.build", "welcome"],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "PDF publishing is disabled" in proc.stderr


def test_bad_writing_is_stubbed_without_taking_down_site(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    (root / "writings" / "broken.typ").write_text(
        '#let meta = (title: "Broken", date: "2026-08-23")\n'
        '#let body = [#image("/assets/missing.svg")]\n'
    )
    _build(root)
    site = root / "artifacts" / "site"
    assert (site / "welcome.html").exists()
    assert (site / "broken.html").exists()
    assert "failed to build" in (site / "broken.html").read_text().lower()
    assert "broken" not in (site / "all.html").read_text().lower()


def test_pdfs_config_defaults_on_and_validates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(build, "ROOT", tmp_path)
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

    page = (root / "artifacts" / "site" / "lifecycle.html").read_text()
    expected = ("scout-plan", "scout", "study-plan", "study", "untyped")
    positions = [page.index(f'href="{entry_id}"') for entry_id in expected]
    assert positions == sorted(positions)
    for status in ("ExpScoutPlan", "ExpScout", "ExpStudyPlan", "ExpStudy"):
        assert f'class="status">{status}</span>' in page
    assert 'class="status">final</span>' not in page


def test_authored_dates_render_consistently_with_semantic_html(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root, demo=False)
    writings = root / "writings"
    (writings / "changed.typ").write_text(
        '#let meta = (title: "Changed", created_at: "2026-08-24", '
        'updated_at: "2026-08-27", collection: "dates")\n#let body = [Body.]\n'
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

    site = root / "artifacts" / "site"
    changed = (site / "changed.html").read_text()
    listing = (site / "dates.html").read_text()
    expected = (
        '<time datetime="2026-08-24">24 August 2026</time> · Updated '
        '<time datetime="2026-08-27">27 August 2026</time>'
    )
    assert expected in changed
    assert (
        '<time datetime="2026-08-24">24 August 2026</time> · Updated '
        '<time datetime="2026-08-27">27 August 2026</time>'
    ) in listing
    assert "Created <time" not in changed
    assert "Created <time" not in listing
    assert '<a class="entry-collection" href="dates">Dates</a>' in changed
    unchanged = (site / "unchanged.html").read_text()
    assert (
        '<time datetime="2026-08-24">24 August 2026</time> · Updated '
        '<time datetime="2026-08-24">24 August 2026</time>'
    ) in unchanged
    assert '<time datetime="2026-08-23">23 August 2026</time>' in (
        site / "legacy.html"
    ).read_text()

    if shutil.which("pdftotext") is not None:
        assert "Created 24 August 2026 · Updated 27 August 2026" in _pdf_text(
            site / "pdfs" / "changed.pdf"
        )
        book = _pdf_text(site / "pdfs" / "book.pdf")
        assert "Created 24 August 2026 · Updated 27 August 2026" in book
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

    index = (root / "artifacts" / "site" / "index.html").read_text()
    assert '<ul class="coll-list">' in index
    assert "Recently worked on" not in index
    assert 'href="note"' not in index


def test_expanded_homepage_recent_and_collection_ordering(tmp_path: Path) -> None:
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
        ("alpha", "2026-08-24", "2026-08-27", "work", "ExpStudy"),
        ("beta", "2026-08-26", None, "work", "ExpScoutPlan"),
        ("gamma", "2026-08-26", None, "work", "ExpStudy"),
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

    index_path = root / "artifacts" / "site" / "index.html"
    index = index_path.read_text()
    recent = index[index.index("Recently worked on"):index.index('href="second"')]
    assert recent.index('href="alpha"') < recent.index('href="gamma"')
    assert 'href="beta"' not in recent
    assert 'href="talk"' not in recent
    assert index.index('<h3><a href="second"') < index.index('<h3><a href="work"')
    assert '<a class="row-collection" href="work">Work</a>' in recent
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
        rebuilt.index("Recently worked on"):rebuilt.index('href="second"')
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

    index = (root / "artifacts" / "site" / "index.html").read_text()
    assert "Recently worked on" not in index
    assert 'href="note"' in index


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
