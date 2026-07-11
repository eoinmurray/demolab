"""init / staging / lab-root discovery — the package-distribution machinery.

These run against the source tree (the package dir IS the working tree in an editable
install), so no wheel build is needed.
"""
import json
import shutil
from pathlib import Path

import pytest

from demolab_cli import _paths
from demolab_cli import cli


@pytest.fixture()
def fresh_dir(tmp_path, monkeypatch):
    d = tmp_path / "lab"
    d.mkdir()
    monkeypatch.chdir(d)
    return d


# ── lab-root discovery ──────────────────────────────────────────────────────
def test_walk_up_finds_marker(tmp_path):
    (tmp_path / "demolab.yaml").write_text("name: x\n")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert _paths.find_lab_root(nested) == tmp_path


def test_walk_up_none_without_marker(tmp_path):
    assert _paths.find_lab_root(tmp_path) is None


# ── staging ─────────────────────────────────────────────────────────────────
def test_stage_materialises_and_stamps(tmp_path):
    dot = _paths.stage(tmp_path)
    assert (dot / "lib.typ").is_file()
    assert (dot / "style.css").is_file()
    assert (dot / "VERSION").read_text(encoding="utf-8").strip() == _paths.VERSION


def test_stage_is_idempotent_and_refreshes_on_version_change(tmp_path):
    dot = _paths.stage(tmp_path)
    (dot / "lib.typ").write_text("clobbered")
    _paths.stage(tmp_path)  # same stamp -> no-op, clobber survives
    assert (dot / "lib.typ").read_text(encoding="utf-8") == "clobbered"
    (dot / "VERSION").write_text("0.0.1\n")  # stale stamp -> full refresh
    _paths.stage(tmp_path)
    assert (dot / "lib.typ").read_text(encoding="utf-8") != "clobbered"
    assert (dot / "VERSION").read_text(encoding="utf-8").strip() == _paths.VERSION


# ── init ────────────────────────────────────────────────────────────────────
def test_init_lays_down_a_lab(fresh_dir):
    assert cli.main(["init"]) == 0
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml", ".gitignore",
                 "demolab.yaml", "HOUSESTYLE.local.md"):
        assert (fresh_dir / name).is_file(), name
    assert (fresh_dir / ".github" / "workflows" / "tests.yml").is_file()
    assert (fresh_dir / ".demolab" / "lib.typ").is_file()
    for d in ("writings", "experiments", "tools", "artifacts"):
        assert (fresh_dir / d).is_dir(), d
    # project name derives from the directory
    assert 'name = "lab"' in (fresh_dir / "pyproject.toml").read_text(encoding="utf-8")
    # no stale references to the vendored-engine world
    assert "demolab-engine" not in (fresh_dir / "AGENTS.md").read_text(encoding="utf-8")


def test_init_refuses_inside_existing_lab(fresh_dir, capsys):
    (fresh_dir / "demolab.yaml").write_text("name: x\n")
    with pytest.raises(SystemExit):
        cli.main(["init"])


def test_init_refuses_any_nonempty_dir(fresh_dir):
    (fresh_dir / "unrelated.txt").write_text("stuff")  # no template collision — still refused
    with pytest.raises(SystemExit):
        cli.main(["init"])
    assert not (fresh_dir / "demolab.yaml").exists(), "nothing was laid down"


def test_init_tolerates_git_droppings(fresh_dir):
    (fresh_dir / ".git").mkdir()
    (fresh_dir / ".DS_Store").write_text("")
    assert cli.main(["init"]) == 0
    assert (fresh_dir / "demolab.yaml").is_file()


def test_init_refuses_collisions_without_force(fresh_dir):
    (fresh_dir / "README.md").write_text("mine")
    with pytest.raises(SystemExit):
        cli.main(["init"])
    assert (fresh_dir / "README.md").read_text(encoding="utf-8") == "mine"


def test_init_force_overwrites(fresh_dir):
    (fresh_dir / "README.md").write_text("mine")
    assert cli.main(["init", "--force"]) == 0
    assert (fresh_dir / "README.md").read_text(encoding="utf-8") != "mine"


def test_init_refuses_in_source_repo(tmp_path, monkeypatch):
    (tmp_path / "demolab_cli").mkdir()
    (tmp_path / "demolab_cli" / "VERSION").write_text("1.0.0\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cli.main(["init"])


# ── demo manifest coverage ──────────────────────────────────────────────────
def test_demo_manifest_covers_demo_content():
    """Every content file the demo overlay lays into a lab must be removable again:
    covered by a demo-manifest.json path (exactly, or via a listed parent dir)."""
    manifest = json.loads((_paths.SCAFFOLD / "demo-manifest.json").read_text(encoding="utf-8"))
    covered = set(manifest["paths"])
    demo = _paths.SCAFFOLD / "demo"
    missing = []
    for p in demo.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(demo).as_posix()
        # not part of the user-facing overlay: the upstream landing (site/), local build
        # noise, and the transient --landing copy
        if rel.startswith(("site/", "temp/", "artifacts/site/")) or rel == "landing.typ":
            continue
        if "__pycache__" in rel or rel.endswith(".DS_Store"):
            continue
        # demolab.yaml is shared lab config the demo overlays with its own branding —
        # clearing must NOT delete it (it's the lab marker), so it's rightly unlisted.
        if rel == "demolab.yaml":
            continue
        if rel in covered or any(rel.startswith(c + "/") for c in covered):
            continue
        missing.append(rel)
    assert not missing, "demo files clear-demo-content would leave behind:\n  " + "\n  ".join(missing)


# ── root templates ──────────────────────────────────────────────────────────
def test_root_templates_reference_package_world():
    root = _paths.SCAFFOLD / "root"
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml", "gitignore"):
        text = (root / name).read_text(encoding="utf-8")
        assert "demolab-engine" not in text, f"{name} references the dead vendored-engine layout"
    assert "demolab-cli" in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert ".demolab/" in (root / "gitignore").read_text(encoding="utf-8")
