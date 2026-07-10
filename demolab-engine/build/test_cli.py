"""The `demolab` CLI (cli.py) replaces the Taskfile; these guard its wiring.

No subprocesses are spawned — the handlers shell out to uv/typst, which the test env may not have.
Instead we assert the two things that silently rot: the command catalog and the dispatch table must
stay in step, and the argument parser must accept every command (with the right args for `run`/`dev`).
"""
import io
from contextlib import redirect_stdout

import cli


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
        argv = {"run": ["run", "exp000"]}.get(name, [name])
        assert parser.parse_args(argv).command == name


def test_run_and_dev_arguments():
    parser = cli._build_parser()
    assert parser.parse_args(["run", "exp042"]).experiment == "exp042"
    dev = parser.parse_args(["dev", "3010", "--demo", "--landing"])
    assert dev.port == 3010 and dev.demo is True and dev.landing is True
    bare_dev = parser.parse_args(["dev"])
    assert bare_dev.port is None and bare_dev.demo is False and bare_dev.landing is False


def test_no_command_prints_catalog():
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert cli.main([]) == 0
    out = buf.getvalue()
    for name in cli.HANDLERS:
        assert name in out, f"catalog output is missing {name!r}"
