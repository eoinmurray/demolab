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
        shutil.copytree(
            _paths.SCAFFOLD / "demo", root, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("landing.typ", "temp", "site"),
        )


def _build(root: Path, entry: str | None = None) -> None:
    subprocess.run(
        [sys.executable, "-m", "demolab_cli.build", *([entry] if entry else [])],
        env={**os.environ, "DEMOLAB_ROOT": str(root)}, check=True,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_complete_build_is_reproducible_and_copies_assets(tmp_path: Path) -> None:
    root = tmp_path / "presentation"
    root.mkdir()
    _assemble(root)
    _build(root)
    first = {p.name: _sha256(p) for p in (root / "artifacts" / "pdfs").glob("*.pdf")}
    _build(root)
    second = {p.name: _sha256(p) for p in (root / "artifacts" / "pdfs").glob("*.pdf")}
    assert first == second
    site = root / "artifacts" / "site"
    assert (site / "welcome.html").exists()
    assert (site / "assets" / "example.json").exists() or (site / "example.json").exists()
    assert "Writings" in (site / "all.html").read_text()
    assert "Experiments" not in (site / "all.html").read_text()


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
            f'#let meta = (title: "{entry_id}", date: "2026-08-24", '
            f'collection: "lifecycle"{status_field})\n#let body = [Body.]\n'
        )

    _build(root)

    page = (root / "artifacts" / "site" / "lifecycle.html").read_text()
    expected = ("scout-plan", "scout", "study-plan", "study", "untyped")
    positions = [page.index(f'href="{entry_id}.html"') for entry_id in expected]
    assert positions == sorted(positions)
    for status in ("ExpScoutPlan", "ExpScout", "ExpStudyPlan", "ExpStudy"):
        assert f'class="status">{status}</span>' in page
    assert 'class="status">final</span>' not in page
