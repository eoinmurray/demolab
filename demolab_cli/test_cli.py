"""The `demolab` CLI (cli.py) replaces the Taskfile; these guard its wiring.

No subprocesses are spawned — the handlers shell out to uv/typst, which the test env may not have.
Instead we assert the two things that silently rot: the command catalog and the dispatch table must
stay in step, and the argument parser must accept every command (with the right args for `dev`).
"""
import io
from contextlib import redirect_stdout
from pathlib import Path

from demolab_cli import cli


def _catalog_names() -> set[str]:
    return {name for _, cmds in cli.GROUPS for name, _ in cmds}


def test_catalog_and_handlers_match():
    # Every advertised command has a handler, and every handler is advertised — no orphans either way.
    assert _catalog_names() == set(cli.HANDLERS), (
        f"catalog vs handlers drifted:\n"
        f"  catalog-only: {sorted(_catalog_names() - set(cli.HANDLERS))}\n"
        f"  handler-only: {sorted(set(cli.HANDLERS) - _catalog_names())}"
    )


def test_every_command_parses():
    parser = cli._build_parser()
    for name in cli.HANDLERS:
        assert parser.parse_args([name]).command == name


def test_dev_arguments():
    parser = cli._build_parser()
    dev = parser.parse_args(["dev", "3010"])
    assert dev.port == 3010
    bare_dev = parser.parse_args(["dev"])
    assert bare_dev.port is None


def test_build_accepts_optional_entry():
    parser = cli._build_parser()
    assert parser.parse_args(["build"]).entry is None
    assert parser.parse_args(["build", "exp007"]).entry == "exp007"


def test_no_command_prints_catalog():
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert cli.main([]) == 0
    out = buf.getvalue()
    for name in cli.HANDLERS:
        assert name in out, f"catalog output is missing {name!r}"


def test_clean_removes_generated_and_legacy_site_but_preserves_legacy_pdfs(
    tmp_path: Path, monkeypatch,
):
    for rel in (".demolab/bundle", ".demolab/site", ".demolab/pdfs", "artifacts/site"):
        path = tmp_path / rel
        path.mkdir(parents=True)
        (path / "generated.txt").write_text("remove")
    legacy_pdf = tmp_path / "artifacts" / "pdfs" / "deliverable.pdf"
    legacy_pdf.parent.mkdir(parents=True)
    legacy_pdf.write_bytes(b"preserve")
    evidence = tmp_path / ".artifacts" / "exp001" / "numbers.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}")
    monkeypatch.setattr(cli._paths, "require_lab_root", lambda: tmp_path)

    assert cli.cmd_clean(cli._build_parser().parse_args(["clean"])) == 0

    assert not (tmp_path / ".demolab").exists()
    assert not (tmp_path / "artifacts" / "site").exists()
    assert legacy_pdf.read_bytes() == b"preserve"
    assert evidence.read_text() == "{}"
