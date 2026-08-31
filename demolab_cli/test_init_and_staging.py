"""init / staging / lab-root discovery — the package-distribution machinery.

These run against the source tree (the package dir IS the working tree in an editable
install), so no wheel build is needed.
"""
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


def test_demo_layout_separates_content_and_runtime_from_every_subdirectory(tmp_path, monkeypatch):
    # Keep this path/staging unit test independent of an installed compiler.
    monkeypatch.setattr(_paths, "_writings_setting", lambda *args: ("writings", None))
    demo = tmp_path / ".demo"
    nested = demo / "data" / "benchmark-a-run-001"
    nested.mkdir(parents=True)
    (demo / "demolab.yaml").write_text("name: Demo\n")
    engine = tmp_path / "demolab_cli"
    engine.mkdir()
    (engine / "build.py").write_text("# source marker\n")
    (engine / "VERSION").write_text("1.0.0\n")
    for start in (tmp_path, demo, nested, engine):
        assert _paths.find_lab_root(start) == tmp_path
    layout = _paths.layout_for(tmp_path)
    assert layout == _paths.layout_for(demo)
    assert layout.demo
    assert layout.content == demo
    assert layout.runtime == tmp_path / ".demolab"
    assert layout.data == demo / "data"
    assert layout.writings == demo / "writings"
    assert layout.typst_inputs() == [
        "--input", "demolab-content-root=/.demo",
        "--input", "demolab-data-root=/.demo/data",
    ]
    assert _paths.stage(demo) == layout.runtime
    assert not (demo / ".demolab").exists()
    # A real nested lab still owns its own commands.
    (nested / "demolab.yaml").write_text("name: Nested lab\n")
    assert _paths.find_lab_root(nested) == nested


def test_ordinary_lab_wins_over_demo_directory(tmp_path):
    (tmp_path / "demolab.yaml").write_text("name: Ordinary\n")
    demo = tmp_path / ".demo"
    demo.mkdir()
    (demo / "demolab.yaml").write_text("name: Nested\n")
    engine = tmp_path / "demolab_cli"
    engine.mkdir()
    (engine / "build.py").write_text("# marker\n")
    (engine / "VERSION").write_text("1.0.0\n")
    layout = _paths.layout_for(tmp_path)
    assert not layout.demo
    assert layout.content == tmp_path
    assert layout.data == tmp_path / ".artifacts"
    assert layout.typst_inputs() == [
        "--input", "demolab-content-root=", "--input", "demolab-data-root=/.artifacts",
    ]
    assert _paths.find_lab_root(demo) == demo


def test_demo_directory_alone_does_not_turn_an_ordinary_project_into_engine_checkout(tmp_path):
    demo = tmp_path / ".demo"
    demo.mkdir()
    (demo / "demolab.yaml").write_text("name: Nested\n")
    assert not _paths.layout_for(tmp_path).demo
    assert _paths.find_lab_root(tmp_path) is None
    assert _paths.find_lab_root(demo) == demo


# ── staging ─────────────────────────────────────────────────────────────────
def test_stage_materialises_and_stamps(tmp_path):
    dot = _paths.stage(tmp_path)
    assert (dot / "lib.typ").is_file()
    assert (dot / "style.css").is_file()
    assert (dot / "image-lightbox.js").is_file()
    assert (dot / "VERSION").read_text(encoding="utf-8").strip() == _paths.VERSION


def test_stage_is_idempotent_and_refreshes_on_version_change(tmp_path):
    dot = _paths.stage(tmp_path)
    before = (dot / "lib.typ").stat().st_mtime_ns
    _paths.stage(tmp_path)  # fresh copies (mtimes match) -> no-op
    assert (dot / "lib.typ").stat().st_mtime_ns == before
    (dot / "VERSION").write_text("0.0.1\n")  # stale stamp -> full refresh
    _paths.stage(tmp_path)
    assert (dot / "VERSION").read_text(encoding="utf-8").strip() == _paths.VERSION


def test_stage_refreshes_a_stale_staged_copy(tmp_path):
    # An editable install edits the engine's typ assets without a version bump; a staged
    # copy whose mtime no longer matches the source must be re-copied (`demolab dev`
    # rebuilds read the staged copy, so a stale one would defeat engine hot-reload).
    dot = _paths.stage(tmp_path)
    (dot / "lib.typ").write_text("clobbered")
    _paths.stage(tmp_path)
    assert (dot / "lib.typ").read_text(encoding="utf-8") != "clobbered"


# ── init ────────────────────────────────────────────────────────────────────
def test_init_lays_down_a_lab(fresh_dir):
    assert cli.main(["init"]) == 0
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml", ".gitignore",
                 "demolab.yaml", "HOUSESTYLE.local.md"):
        assert (fresh_dir / name).is_file(), name
    assert (fresh_dir / ".demolab" / "lib.typ").is_file()
    for d in ("writings", "assets"):
        assert (fresh_dir / d).is_dir(), d
        assert {p.name for p in (fresh_dir / d).iterdir()} == {".gitkeep"}, (
            f"{d} must remain a stub; example content belongs only in the internal demo"
        )
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


# ── root templates ──────────────────────────────────────────────────────────
def test_root_templates_reference_package_world():
    root = _paths.SCAFFOLD / "root"
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml", "gitignore"):
        text = (root / name).read_text(encoding="utf-8")
        assert "demolab-engine" not in text, f"{name} references the dead vendored-engine layout"
    assert "demolab-cli" in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert ".demolab/" in (root / "gitignore").read_text(encoding="utf-8")


def test_agent_instructions_use_project_environment():
    text = (_paths.SCAFFOLD / "root" / "AGENTS.md").read_text(encoding="utf-8")
    assert "uv run demolab docs" in text
    assert "uvx demolab-cli docs" not in text
