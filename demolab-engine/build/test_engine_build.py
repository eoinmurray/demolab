"""Engine smoke test — builds the shipped scaffold fixtures end-to-end.

The demo under `demolab-engine/scaffold/demo/` doubles as the engine's integration test:
we assemble a throwaway repo (skeleton + demo) in a tmp dir, point `build.py` at it via
`DEMOLAB_ROOT`, and assert the compiler emits a real site. The empty case (skeleton only)
proves a freshly-scaffolded repo builds a friendly empty-state homepage rather than erroring.

Needs the `typst` CLI on PATH (same as `task build`); skipped if it's missing.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "demolab-engine"
SCAFFOLD = ENGINE / "scaffold"

pytestmark = pytest.mark.skipif(
    shutil.which("typst") is None, reason="typst CLI not installed"
)


def _assemble(root: Path, *, demo: bool) -> None:
    """Lay down a full working tree at `root`: engine build/ + skeleton (+ demo overlay).

    The engine's build/ is copied (not symlinked) into the fixture: writings import
    `/demolab-engine/build/lib.typ` root-relative, and typst requires the source to live
    under --root, so a symlink pointing outside the tmp dir is rejected."""
    shutil.copytree(ENGINE / "build", root / "demolab-engine" / "build")
    shutil.copy(ENGINE / "VERSION", root / "demolab-engine" / "VERSION")  # read by web-styles' generator meta
    shutil.copytree(SCAFFOLD / "skeleton", root, dirs_exist_ok=True)
    if demo:
        shutil.copytree(SCAFFOLD / "demo", root, dirs_exist_ok=True)


def _build(root: Path) -> None:
    subprocess.run(
        [sys.executable, str(ENGINE / "build" / "build.py")],
        env={**os.environ, "DEMOLAB_ROOT": str(root)},
        check=True,
    )


def test_demo_fixture_builds_full_site(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _assemble(root, demo=True)
    _build(root)

    site = root / "artifacts" / "site"
    assert (site / "index.html").exists()
    assert (site / "all.html").exists()
    assert (site / "pdfs" / "book.pdf").exists()
    assert (site / "exp000.html").exists(), "per-entry page emitted"
    assert (site / "pdfs" / "exp000.pdf").exists(), "per-entry PDF emitted"

    index = (site / "index.html").read_text()
    # ".empty-state" also appears in the inlined stylesheet, so key on the rendered copy.
    assert "Your lab is ready" not in index, "demo has content, so no empty state"
    entry = (site / "exp000.html").read_text()
    assert "<img" in entry or "<svg" in entry, "a figure made it into the entry page"


def test_empty_tree_builds_empty_state(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _assemble(root, demo=False)
    _build(root)

    site = root / "artifacts" / "site"
    assert (site / "index.html").exists(), "homepage always exists"
    assert not (site / "all.html").exists(), "no all-entries page without content"
    assert not (site / "pdfs" / "book.pdf").exists(), "no book without content"
    assert "Your lab is ready" in (site / "index.html").read_text()
