"""`demolab docs` must list every runbook / guide file the package ships.

The trigger grammar — `HELP` runs `demolab docs`, a `NAME` in CAPS routes to one — only
works if the generated menu covers `runbooks/*.md` and `guides/*.md` exactly. The menu is
built from the same globs at runtime, so this mostly guards the plumbing (a doc without a
summary line, a rename that breaks path resolution) — and that every doc resolves by name.
"""
from pathlib import Path

from demolab_cli import _paths
from demolab_cli import cli


def _files(base: Path) -> set[str]:
    return {p.stem for p in base.glob("*.md")}

def test_docs_menu_covers_every_file(capsys):
    assert cli.main(["docs"]) == 0
    menu = capsys.readouterr().out
    for name in _files(_paths.RUNBOOKS) | _files(_paths.GUIDES) | {"CHANGELOG"}:
        assert f"\n    {name} " in menu or f"\n    {name}\n" in menu, f"{name} missing from `demolab docs`"


def test_docs_prints_the_agent_manual(capsys):
    """Bare `demolab docs` is the agent's one-call orientation: the packaged AGENT.md
    manual in full, then the menu."""
    assert cli.main(["docs"]) == 0
    out = capsys.readouterr().out
    manual = (_paths.PACKAGE / "AGENT.md").read_text(encoding="utf-8")
    assert manual in out, "AGENT.md must be printed verbatim by bare `demolab docs`"
    assert "The NAME is the command" in out
    assert out.index(manual[:40]) < out.index("runbooks"), "manual comes before the menu"


def test_every_doc_resolves_by_name(capsys):
    for name in _files(_paths.RUNBOOKS) | _files(_paths.GUIDES) | {"CHANGELOG", "DEMO", "STARTERS"}:
        assert cli.main(["docs", name]) == 0
        path = Path(capsys.readouterr().out.strip())
        assert path.exists(), f"`demolab docs {name}` printed a non-existent path: {path}"


def test_docs_is_case_insensitive(capsys):
    assert cli.main(["docs", "getting-started"]) == 0
    assert Path(capsys.readouterr().out.strip()).name == "GETTING-STARTED.md"


def test_unknown_doc_fails_cleanly(capsys):
    assert cli.main(["docs", "NO-SUCH-DOC"]) == 2
