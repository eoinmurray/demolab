"""The `demolab` CLI (cli.py) replaces the Taskfile; these guard its wiring.

No subprocesses are spawned — the handlers shell out to uv/typst, which the test env may not have.
Instead we assert the two things that silently rot: the command catalog and the dispatch table must
stay in step, and the argument parser must accept every command (with the right args for `dev`).
"""
import io
from argparse import Namespace
from contextlib import redirect_stdout

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
    dev = parser.parse_args(["dev", "3010", "--demo", "--landing"])
    assert dev.port == 3010 and dev.demo is True and dev.landing is True
    bare_dev = parser.parse_args(["dev"])
    assert bare_dev.port is None and bare_dev.demo is False and bare_dev.landing is False


def test_demo_landing_passes_live_source_to_devserver(tmp_path, monkeypatch):
    scaffold = tmp_path / "package-scaffold"
    (scaffold / "skeleton").mkdir(parents=True)
    (scaffold / "skeleton" / "demolab.yaml").write_text("name: Test\n")
    (scaffold / "demo" / "site").mkdir(parents=True)
    source = scaffold / "demo" / "site" / "landing.typ"
    source.write_text("#let body = [landing]\n")
    captured = {}

    monkeypatch.setattr(cli._paths, "SCAFFOLD", scaffold)
    monkeypatch.setattr(cli._paths, "require_lab_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "_mod", lambda *args, **kwargs: captured.update(kwargs) or 0)

    assert cli.cmd_dev(Namespace(port=None, demo=True, landing=True)) == 0
    scratch = tmp_path / "temp" / "demo-preview"
    assert (scratch / "landing.typ").read_text() == "#let body = [landing]\n"
    assert captured["env"]["DEMOLAB_LANDING_SOURCE"] == str(source.resolve())


def test_no_command_prints_catalog():
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert cli.main([]) == 0
    out = buf.getvalue()
    for name in cli.HANDLERS:
        assert name in out, f"catalog output is missing {name!r}"
