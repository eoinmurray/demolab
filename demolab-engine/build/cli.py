#!/usr/bin/env python3
"""demolab — the lab's command runner. Replaces the go-task Taskfile so the toolchain is just
uv (Python) and typst (publishing); no third tool to install, and none of go-task's winget /
PATH-restart friction on Windows.

Run it either way (both cross-platform, both need only uv on PATH):

    uv run demolab-engine/build/cli.py <command> [args]     # works from a fresh clone
    demolab <command> [args]                                # if the console script is wired up

This module is pure standard library, so it launches even before `uv sync` has run — that is what
lets `demolab install` bootstrap the environment. Engine build scripts (build/dev/slides) and the
file-shuffling commands (scaffold/clean/…) are stdlib too and run against the current interpreter;
the commands that need the project's third-party deps (run/playground/test) and `install` itself go
through `uv` so the venv is guaranteed present.

The repo root is derived from this file's location, not the cwd, so every command works from any
subdirectory — the way `task` always ran from the Taskfile's directory.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# demolab-engine/build/cli.py -> parents[2] is the repo checkout.
REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "demolab-engine" / "build"
SCAFFOLD = REPO / "demolab-engine" / "scaffold"
DEPLOY = REPO / "demolab-engine" / "deploy"

# name -> one-line help, grouped exactly like the old Taskfile sections. The catalog printer and the
# argparse subcommands both read this, so the two can't drift.
GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("setup", [
        ("install", "🛠  Install Python dependencies (uv)"),
        ("version", "🔖 Print the demolab engine version (demolab-engine/VERSION)"),
    ]),
    ("scaffolding", [
        ("scaffold", "🏗  Lay down the working-tree structure (writings/ experiments/ tools/ artifacts/ + config) — non-destructive"),
        ("add-demo-content", "🏗  Overlay the worked demo (experiments + writeups + artifacts) onto the scaffolded structure"),
        ("clear-demo-content", "🧹 Remove the shipped demo content (paths in demolab-engine/scaffold/demo-manifest.json)"),
        ("deploy-setup", "🚀 Opt in to GitHub Pages — copy the deploy + preview workflows into .github/workflows/"),
    ]),
    ("the loop", [
        ("run", "▶  Run an experiment end-to-end, e.g. `demolab run exp000`"),
        ("new", "✨ How to start a new experiment (hint — ask your coding agent)"),
    ]),
    ("publishing", [
        ("dev", "🔥 Serve the site with hot-reload + in-browser build errors (--demo serves the shipped demo, add --landing for its landing page; PORT overrides the auto-picked 3000)"),
        ("build", "📦 Build the whole bundle → artifacts/site/ (web) + artifacts/pdfs/ (PDFs + book)"),
        ("slides", "🎞  Compile standalone Typst decks (writings/*.typ with no meta+body) to artifacts/pdfs/"),
        ("playground", "🎛  Launch the interactive Streamlit demo (http://localhost:8501)"),
    ]),
    ("quality & housekeeping", [
        ("test", "🧪 Run the Python test suite (pytest)"),
        ("clean", "🧹 Delete regenerable build output (temp/, artifacts/site/)"),
    ]),
]


def _utf8_stdio() -> None:
    # Windows captures stdout as CP1252 by default (e.g. inside a PowerShell background job or an
    # agent harness pipe); the emoji in the catalog and the ✓/→ status lines would crash it. Force
    # UTF-8 defensively — the same fix build.py's dev server needed.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _run(*cmd: str, env: dict[str, str] | None = None) -> int:
    """Run a subprocess from the repo root, streaming its stdio. Returns the child's exit code.
    Ctrl-C in a long-running child (the dev server) reaches it directly; we swallow the resulting
    KeyboardInterrupt here so the CLI exits quietly instead of dumping a traceback."""
    try:
        return subprocess.run(list(cmd), cwd=REPO, env=env).returncode
    except KeyboardInterrupt:
        return 130


def _py(script: Path, *args: str) -> int:
    """Run one of the stdlib engine scripts on the current interpreter (no uv needed — they import
    nothing third-party; CI builds the site with a bare `python3` for exactly this reason)."""
    return _run(sys.executable, str(script), *args)


# ── setup ──────────────────────────────────────────────────────────────────
def cmd_install(args: argparse.Namespace) -> int:
    return _run("uv", "sync")


def cmd_version(args: argparse.Namespace) -> int:
    print((REPO / "demolab-engine" / "VERSION").read_text().strip())
    return 0


# ── scaffolding ────────────────────────────────────────────────────────────
def _overlay(src: Path, keep_existing: bool = False, exclude: tuple[str, ...] = ()) -> int:
    # overlay.py copies src/** into its cwd; running it with cwd=REPO lands the tree at the root.
    cmd = [str(src)]
    if keep_existing:
        cmd.append("--keep-existing")
    if exclude:
        cmd += ["--exclude", *exclude]
    return _py(BUILD / "overlay.py", *cmd)


def cmd_scaffold(args: argparse.Namespace) -> int:
    code = _overlay(SCAFFOLD / "skeleton", keep_existing=True)
    if code == 0:
        print("✓ scaffolded the folder structure. Add a writeup in writings/ and run 'demolab build'.")
        print("  (want a worked example instead? run 'demolab add-demo-content')")
    return code


def cmd_add_demo_content(args: argparse.Namespace) -> int:
    # The old task declared `deps: [scaffold]`; reproduce that — scaffold first (idempotent), then
    # overlay the demo on top, skipping its prebuilt site/.
    code = cmd_scaffold(args)
    if code != 0:
        return code
    code = _overlay(SCAFFOLD / "demo", exclude=("site",))
    if code == 0:
        print("✓ added the demo content. Run 'demolab build' to publish it, or 'demolab clear-demo-content' to remove it.")
    return code


def cmd_clear_demo_content(args: argparse.Namespace) -> int:
    manifest = json.loads((SCAFFOLD / "demo-manifest.json").read_text())
    paths = manifest["paths"]
    for rel in paths:
        target = REPO / rel
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        else:
            target.unlink(missing_ok=True)
    print(f"✓ removed {len(paths)} demo paths")
    return 0


def cmd_deploy_setup(args: argparse.Namespace) -> int:
    dst = REPO / ".github" / "workflows"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(DEPLOY / "deploy.yml", dst / "deploy.yml")
    shutil.copy(DEPLOY / "preview.yml", dst / "preview.yml")
    print("✓ wrote .github/workflows/deploy.yml   (production: build main → gh-pages branch)")
    print("✓ wrote .github/workflows/preview.yml  (per-PR previews under pr-preview/pr-N/)")
    print("  Last steps (GitHub-UI clicks, can't be scripted):")
    print("    1. Settings → Pages → Source: Deploy from a branch → gh-pages / (root)")
    print("       (the first push to main creates the gh-pages branch)")
    print("    2. Settings → General → Pull Requests: enable 'Automatically delete head branches'")
    print("    3. (recommended) Settings → Branches: protect main")
    print("  Then commit + push — main deploys the site; each PR gets its own preview URL.")
    return 0


# ── the loop ───────────────────────────────────────────────────────────────
def cmd_run(args: argparse.Namespace) -> int:
    # Experiment runners import the project deps (numpy, mujoco, …), so this one goes through uv.
    return _run("uv", "run", "python", f"experiments/{args.experiment}.py")


def cmd_new(args: argparse.Namespace) -> int:
    print("Experiments aren't scaffolded from a template — ask your coding agent.")
    print("It models a *working* skeleton on an existing pair:")
    print("  experiments/expNNN.py  — a runner with real COMMANDS that stages artifacts/data/expNNN/")
    print("  writings/expNNN.typ    — a #let meta + #let body that read that bundle via json()/image()")
    print()
    print('Try: "scaffold a new experiment expNNN that computes <thing>"')
    print("See AGENTS.md (entry point) and demolab-engine/guides/RULES.md (how to add one).")
    return 0


# ── publishing ─────────────────────────────────────────────────────────────
def cmd_dev(args: argparse.Namespace) -> int:
    server = BUILD / "devserver.py"
    port_args = [str(args.port)] if args.port else []
    if not args.demo:
        if args.landing:
            print("--landing only applies to --demo. For your own lab, create a landing.typ at the",
                  file=sys.stderr)
            print("repo root and `demolab dev` renders it (and hot-reloads it).", file=sys.stderr)
            return 2
        return _py(server, *port_args)
    # --demo: serve the shipped demo through the live engine. The demo's landing page lives under
    # site/ (kept out of user labs), so it only renders as the homepage when copied to the content
    # root — which is what --landing does for the session, mirroring the Pages deploy (landing.yml).
    env = {**os.environ, "DEMOLAB_ROOT": str(SCAFFOLD / "demo")}
    landing_dst = SCAFFOLD / "demo" / "landing.typ"
    created = False
    if args.landing:
        if landing_dst.exists():
            print(f"→ {landing_dst.relative_to(REPO)} already present — serving it as-is (leaving it in place)")
        else:
            shutil.copy(SCAFFOLD / "demo" / "site" / "landing.typ", landing_dst)
            created = True
            print("→ previewing the upstream landing page (copied site/landing.typ to the demo root)")
    print("→ reading + serving from demolab-engine/scaffold/demo")
    try:
        return _run(sys.executable, str(server), *port_args, env=env)
    finally:
        # Only remove what we created — never a landing.typ the user had already put there.
        if created:
            landing_dst.unlink(missing_ok=True)
            print(f"✓ removed the temporary {landing_dst.relative_to(REPO)}")


def cmd_build(args: argparse.Namespace) -> int:
    return _py(BUILD / "build.py")


def cmd_slides(args: argparse.Namespace) -> int:
    return _py(BUILD / "slides.py")


def cmd_playground(args: argparse.Namespace) -> int:
    return _run("uv", "run", "streamlit", "run", "experiments/playground.py")


# ── quality & housekeeping ─────────────────────────────────────────────────
def cmd_test(args: argparse.Namespace) -> int:
    return _run("uv", "run", "pytest")


def cmd_clean(args: argparse.Namespace) -> int:
    for rel in ("temp", "artifacts/site"):
        shutil.rmtree(REPO / rel, ignore_errors=True)
    print("✓ removed temp/ and artifacts/site/")
    return 0


HANDLERS = {
    "install": cmd_install,
    "version": cmd_version,
    "scaffold": cmd_scaffold,
    "add-demo-content": cmd_add_demo_content,
    "clear-demo-content": cmd_clear_demo_content,
    "deploy-setup": cmd_deploy_setup,
    "run": cmd_run,
    "new": cmd_new,
    "dev": cmd_dev,
    "build": cmd_build,
    "slides": cmd_slides,
    "playground": cmd_playground,
    "test": cmd_test,
    "clean": cmd_clean,
}


def _print_catalog() -> None:
    print("demolab — lab command runner. Usage: demolab <command> [args]\n")
    width = max(len(name) for _, cmds in GROUPS for name, _ in cmds)
    for title, cmds in GROUPS:
        print(f"  {title}")
        for name, desc in cmds:
            print(f"    {name:<{width}}  {desc}")
        print()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="demolab", add_help=True,
                                description="The lab's command runner (replaces the go-task Taskfile).")
    sub = p.add_subparsers(dest="command", metavar="<command>")
    help_by_name = {name: desc for _, cmds in GROUPS for name, desc in cmds}
    for name in HANDLERS:
        sp = sub.add_parser(name, help=help_by_name[name])
        if name == "run":
            sp.add_argument("experiment", help="experiment id, e.g. exp000 (runs experiments/exp000.py)")
        elif name == "dev":
            sp.add_argument("port", nargs="?", type=int, help="port to serve on (default: first free from 3000)")
            sp.add_argument("--demo", action="store_true", help="serve the shipped demo instead of the repo root")
            sp.add_argument("--landing", action="store_true",
                            help="with --demo: preview the upstream landing page (copies site/landing.typ "
                                 "into the demo root for the session, removed on exit)")
    return p


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        _print_catalog()
        return 0
    return HANDLERS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
