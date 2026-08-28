"""End-to-end tests for generic writings, assets, and optional PDFs."""
import base64
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
        shutil.copytree(source / "data", root / ".artifacts", dirs_exist_ok=True)
        shutil.copytree(source / "data", root / "data", dirs_exist_ok=True)
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
    assert (site / "welcome.html").exists()
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


@pytest.mark.parametrize("source_layout", [False, True])
def test_source_demo_renders_single_gallery_and_comparison_cases(
    tmp_path: Path, source_layout: bool,
) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    (_assemble_demo if source_layout else _assemble)(root)
    layout = _paths.layout_for(root)
    inputs = [p for base in (layout.content / "data", layout.data, layout.writings)
              for p in base.rglob("*") if p.is_file()]
    before = {p: _sha256(p) for p in inputs}
    runs = {f"benchmark-{experiment}-run-{run}" for experiment in ("a", "b")
            for run in ("001", "002")}
    assert {p.name for p in (layout.content / "data").iterdir()} == runs
    records = {}
    for run in sorted(runs):
        directory = layout.data / run
        record = json.loads((directory / "numbers.json").read_text())
        assert record["synthetic"] is True
        assert record["run_id"] == run
        assert record["data_key"] == run.split("-run-")[0]
        assert record["correct"] / record["total"] * 100 == record["accuracy_percent"]
        chart = ET.parse(directory / "accuracy.svg")
        bar = chart.find(".//{http://www.w3.org/2000/svg}rect[@id='value']")
        assert bar is not None
        assert float(bar.attrib["width"]) == record["accuracy_percent"] * 5
        records[run] = record
    for experiment in ("a", "b"):
        first, second = (records[f"benchmark-{experiment}-run-{run}"] for run in ("001", "002"))
        assert first["created_at"] < second["created_at"]
        assert first["accuracy_percent"] != second["accuracy_percent"]
    _build(root)
    manifest = json.loads((root / ".demolab" / "bundle" / "index.json").read_text())
    assert all("error" not in entry for entry in manifest["entries"])
    site = root / ".demolab" / "site"
    cases = {
        "benchmark-a": ["benchmark-a-run-001"],
        "benchmark-gallery": ["benchmark-a-run-001", "benchmark-b-run-002"],
        "benchmark-comparison": sorted(runs),
        "benchmark-empty": [],
    }
    assert {entry["id"] for entry in manifest["entries"]} == {"api", "welcome", *cases}
    for article, selected in cases.items():
        page = (site / f"{article}.html").read_text()
        pdf = _pdf_text(site / "pdfs" / f"{article}.pdf")
        figures = re.findall(r'<img src="data:image/svg\+xml;base64,([^"]+)"', page)
        assert [base64.b64decode(figure) for figure in figures] == [
            (layout.data / run / "accuracy.svg").read_bytes() for run in selected
        ]
        for run in selected:
            percentage = records[run]["accuracy_percent"]
            assert run in page and f"{percentage}% accuracy" in page
            assert f"{percentage}% accuracy" in pdf
        for run in runs - set(selected):
            assert run not in page
        if article == "benchmark-comparison":
            for difference in (24, 20):
                assert f"{difference} percentage points" in page
                assert f"{difference} percentage points" in pdf
        if article == "benchmark-empty":
            assert page.count('class="fig-pending"') == 2
            assert "Awaiting a run." in page and "Awaiting a run." in pdf
            assert "Image pending" in page and "Video pending" in page
        assert f'href="{article}"' in (site / "welcome.html").read_text()
        assert f'href="{article}"' in (site / "data-source-demos.html").read_text()
    assert 'href="data-source-demos"' in (site / "index.html").read_text()
    assert 'href="benchmark-a"' in (site / "welcome.html").read_text()
    assert before == {p: _sha256(p) for p in inputs}
    if source_layout:
        assert not (root / ".demo" / ".demolab").exists()
        assert not (root / "writings").exists()
        assert not (root / ".artifacts").exists()
        assert not (root / "demolab.yaml").exists()


def test_demo_cli_clean_and_rebuild_preserve_inputs_from_nested_directory(tmp_path: Path) -> None:
    root = tmp_path / "engine"
    _assemble_demo(root)
    demo = root / ".demo"
    before = {p.relative_to(demo): _sha256(p) for p in demo.rglob("*") if p.is_file()}
    proc = _cli(demo / "writings", "build", "benchmark-a")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "64% accuracy" in _pdf_text(root / ".demolab/pdfs/benchmark-a.pdf")
    proc = _cli(root, "build")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    proc = _cli(demo / "data/benchmark-a-run-002", "clean")
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
        '#import "/.demolab/lib.typ": data-file\n'
        '#let data-file = data-file.with(sources: ("benchmark-a": "benchmark-a-run-001"))\n'
        '#let meta = (title: "Demo deck", created_at: "2026-08-27")\n'
        '#let data = json(data-file("benchmark-a/numbers.json"))\n'
        'Deck accuracy: #data.accuracy_percent%\n'
    )
    _build(root)
    site = root / ".demolab" / "site"
    assert "Demo landing page" in (site / "index.html").read_text()
    assert (site / "example.txt").read_text() == "Demo static asset\n"
    assert "Deck accuracy: 64%" in _pdf_text(site / "pdfs/demo.pdf")
    assert "64% accuracy" in _pdf_text(site / "pdfs/book.pdf")
    (demo / "demolab.yaml").write_text("name: Web demo\npdfs: false\n")
    proc = _cli(root, "build", "benchmark-a")
    assert proc.returncode != 0
    assert "PDF publishing is disabled" in proc.stderr
    _build(root)
    assert not (site / "pdfs").exists()
    assert "Web demo" in (site / "index.html").read_text()


@pytest.mark.parametrize(
    ("article_id", "old_binding", "new_binding", "selected"),
    [
        ("benchmark-a", '"benchmark-a": "benchmark-a-run-001"',
         '"benchmark-a": "benchmark-a-run-002"', ["benchmark-a-run-002"]),
        ("benchmark-gallery", '"benchmark-a": "benchmark-a-run-001"',
         '"benchmark-a": "benchmark-a-run-002"', ["benchmark-a-run-002", "benchmark-b-run-002"]),
        ("benchmark-comparison", '"candidate.benchmark-a": "benchmark-a-run-002"',
         '"candidate.benchmark-a": "benchmark-a-run-001"',
         ["benchmark-a-run-001", "benchmark-a-run-001", "benchmark-b-run-001", "benchmark-b-run-002"]),
    ],
)
def test_demo_binding_changes_only_its_article_and_input(
    tmp_path: Path, article_id: str, old_binding: str, new_binding: str, selected: list[str],
) -> None:
    root = tmp_path / "engine"
    _assemble_demo(root)
    _unpin_demo(root)
    _build(root)
    site = root / ".demolab/site"
    unchanged = {name: (site / f"{name}.html").read_bytes()
                 for name in ("benchmark-a", "benchmark-gallery", "benchmark-comparison")
                 if name != article_id}
    article = root / ".demo/writings" / f"{article_id}.typ"
    text = article.read_text()
    assert old_binding in text
    article.write_text(text.replace(old_binding, new_binding))
    _build(root)
    page = (site / f"{article_id}.html").read_text()
    figures = re.findall(r'<img src="data:image/svg\+xml;base64,([^"]+)"', page)
    assert [base64.b64decode(figure) for figure in figures] == [
        (root / ".demo/data" / run / "accuracy.svg").read_bytes() for run in selected
    ]
    for run in selected:
        data = json.loads((root / ".demo/data" / run / "numbers.json").read_text())
        assert f'{data["accuracy_percent"]}% accuracy' in page
    if article_id == "benchmark-comparison":
        assert "0 percentage points" in page and "20 percentage points" in page
        assert "88% accuracy" not in page
        assert "benchmark-a-run-002" not in page
    else:
        assert "64% accuracy" not in page
    assert unchanged == {name: (site / f"{name}.html").read_bytes() for name in unchanged}


@pytest.mark.parametrize("run", ["benchmark-a-run-001", "benchmark-a-run-002",
                                 "benchmark-b-run-001", "benchmark-b-run-002"])
@pytest.mark.parametrize("filename", ["numbers.json", "accuracy.svg"])
def test_demo_missing_data_produces_visible_stub(tmp_path: Path, run: str, filename: str) -> None:
    root = tmp_path / "engine"
    _assemble_demo(root)
    _unpin_demo(root)
    (root / ".demo/data" / run / filename).unlink()
    _build(root)
    site = root / ".demolab" / "site"
    for article, affected in (
        ("benchmark-a", run == "benchmark-a-run-001"),
        ("benchmark-gallery", run in ("benchmark-a-run-001", "benchmark-b-run-002")),
        ("benchmark-comparison", True),
    ):
        page = (site / f"{article}.html").read_text().lower()
        assert ("failed to build" in page) == affected
    assert (site / "welcome.html").is_file()


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
    _build(root, "welcome")
    assert sorted(p.name for p in (root / ".demolab" / "pdfs").glob("*.pdf")) == ["welcome.pdf"]
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
    _unpin_demo(root)
    (root / "writings" / "broken.typ").write_text(
        '#let meta = (title: "Broken", date: "2026-08-23")\n'
        '#let body = [#image("/assets/missing.svg")]\n'
    )
    _build(root)
    site = root / ".demolab" / "site"
    assert (site / "welcome.html").exists()
    assert (site / "broken.html").exists()
    assert "failed to build" in (site / "broken.html").read_text().lower()
    assert "broken" not in (site / "all.html").read_text().lower()


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
    assert "Recently worked on" not in index
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
    assert 'class="entry-list-heading"' not in index
    assert (root / ".demolab" / "site" / "all.html").read_text().count('class="entry-list-heading"') == 1
    recent = index[index.index("Recently worked on"):index.index('href="second"')]
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

    index = (root / ".demolab" / "site" / "index.html").read_text()
    assert "Recently worked on" not in index
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
