#!/usr/bin/env python3
"""demolab — the lab's command runner (the demolab-cli package entry point).

The engine lives in this package (site-packages); a lab is a plain directory of user
content marked by its demolab.yaml. Every command finds the lab by walking up from the
cwd, like git finding its root — so it works from any subdirectory. `demolab init` starts
a new lab; `demolab docs` lists the runbooks + guides that ship in the package (agents
read them by path). Run `demolab` with no arguments for the command list.

The CLI itself is pure stdlib. Engine scripts (build/dev/slides) run on the current
interpreter; the commands that need the lab's third-party deps (run/playground/test) and
`install` go through `uv`, which guarantees the venv is present.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from demolab_cli import _paths
from demolab_cli.overlay import overlay

# name -> one-line help, grouped for the catalog. The catalog printer and the argparse
# subcommands both read this, so the two can't drift.
GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("start here", [
        ("init", "✨ Start a new lab in the current directory (root files + structure + git init)"),
        ("docs", "📚 List the runbooks + guides; `demolab docs <NAME>` prints one's path (--print to cat it)"),
    ]),
    ("setup", [
        ("install", "🛠  Install Python dependencies (uv sync)"),
        ("version", "🔖 Print the demolab engine version"),
    ]),
    ("scaffolding", [
        ("scaffold", "🏗  (Re)lay the working-tree structure (writings/ experiments/ tools/ artifacts/ + config) — non-destructive"),
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


def _run(*cmd: str, cwd: Path, env: dict[str, str] | None = None) -> int:
    """Run a subprocess from the lab root, streaming its stdio. Returns the child's exit code.
    Ctrl-C in a long-running child (the dev server) reaches it directly; we swallow the resulting
    KeyboardInterrupt here so the CLI exits quietly instead of dumping a traceback."""
    try:
        return subprocess.run(list(cmd), cwd=cwd, env=env).returncode
    except KeyboardInterrupt:
        return 130


def _mod(name: str, *args: str, cwd: Path, env: dict[str, str] | None = None) -> int:
    """Run one of the engine modules on the current interpreter (no uv needed — they import
    nothing third-party). DEMOLAB_ROOT pins the child to the lab we resolved here, so the
    module doesn't have to repeat the walk-up."""
    env = {**(env or os.environ), "DEMOLAB_ROOT": (env or os.environ).get("DEMOLAB_ROOT") or str(cwd)}
    return _run(sys.executable, "-m", f"demolab_cli.{name}", *args, cwd=cwd, env=env)


# ── start here ─────────────────────────────────────────────────────────────
_ROOT_TEMPLATES = ("AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml")


def _slug(name: str) -> str:
    """A directory name as a valid Python project name (lowercase, dash-separated)."""
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "my-lab"


def cmd_init(args: argparse.Namespace) -> int:
    target = Path.cwd()
    if (target / "demolab_cli" / "VERSION").is_file():
        sys.exit("demolab init: this is the demolab-cli source repo — it is not a lab to initialise.")
    existing = _paths.find_lab_root(target)
    if existing is not None and not args.force:
        sys.exit(f"demolab init: already inside a lab ({existing}) — use `demolab scaffold` to repair "
                 "its structure, or --force to lay a new lab over this directory anyway.")
    # A lab is born in an EMPTY directory — never sprayed over existing content (imagine
    # running this in $HOME). Version-control droppings don't count as content.
    stray = sorted(p.name for p in target.iterdir() if p.name not in (".git", ".DS_Store"))
    if stray and not args.force:
        shown = ", ".join(stray[:5]) + (f", … ({len(stray)} entries)" if len(stray) > 5 else "")
        sys.exit(f"demolab init: this directory isn't empty ({shown}).\n"
                 "  Start your lab in a fresh directory (mkdir my-lab && cd my-lab), or rerun "
                 "with --force to lay the lab over what's here.")
    root_src = _paths.SCAFFOLD / "root"
    # Root framework files. The pyproject template's project name becomes the directory's.
    for name in _ROOT_TEMPLATES:
        text = (root_src / name).read_text(encoding="utf-8")
        if name == "pyproject.toml":
            text = text.replace("my-lab", _slug(target.name))
        (target / name).write_text(text, encoding="utf-8")
    # Stored without the dot so packaging tools never treat it as an ignore file for the wheel.
    shutil.copy2(root_src / "gitignore", target / ".gitignore")
    ci_src = root_src / "github" / "workflows" / "tests.yml"
    ci_dst = target / ".github" / "workflows" / "tests.yml"
    ci_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ci_src, ci_dst)
    # The content structure (demolab.yaml — the lab marker — HOUSESTYLE.local.md, empty dirs).
    overlay(_paths.SCAFFOLD / "skeleton", target, keep_existing=True)
    _paths.stage(target)
    _git_init(target)
    print(f"✓ Your lab is ready. (demolab {_paths.VERSION})\n")
    print("  In one terminal tab, the live preview:")
    print("      uv run demolab dev")
    print("\n  In another, your coding agent — paste:")
    print('      "Run `uv run demolab docs GETTING-STARTED` and follow it strictly, step by step."')
    return 0


def _git_init(target: Path) -> None:
    """git init + first commit, best-effort: skipped inside an existing repo, without git, or
    when a commit can't be made (no identity configured) — init still succeeds."""
    if shutil.which("git") is None:
        print("  (git not found — initialise version control yourself)")
        return
    inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=target,
                            capture_output=True, text=True)
    if inside.returncode == 0 and inside.stdout.strip() == "true":
        print("  (already inside a git repository — not re-initialising)")
        return
    subprocess.run(["git", "init", "--quiet"], cwd=target, check=False)
    subprocess.run(["git", "add", "-A"], cwd=target, check=False)
    commit = subprocess.run(["git", "commit", "--quiet", "-m", "Start my lab with demolab"],
                            cwd=target, capture_output=True, text=True)
    if commit.returncode != 0:
        print("  (git initialised; make the first commit yourself — `git commit` needs your identity)")


def _doc_files() -> dict[str, Path]:
    """Every runbook + guide shipped in the package, by stem, plus the agent manual, the
    CHANGELOG, and the reference-data dirs (the published docs site + the starters — read as
    models, never overlaid by hand)."""
    docs: dict[str, Path] = {}
    for d in (_paths.RUNBOOKS, _paths.GUIDES):
        for p in sorted(d.glob("*.md")):
            docs[p.stem] = p
    docs["AGENT"] = _paths.PACKAGE / "AGENT.md"
    docs["CHANGELOG"] = _paths.PACKAGE / "CHANGELOG.md"
    docs["DEMO"] = _paths.SCAFFOLD / "demo"
    docs["STARTERS"] = _paths.SCAFFOLD / "starters"
    return docs


def _doc_summary(p: Path) -> str:
    """The doc's one-liner: the first blockquote or paragraph after its heading (runbooks
    open with a summary blockquote; guides with a lead paragraph), joined across lines,
    clipped to one sentence, and capped — the menu should be dense, not truncated mid-word."""
    block: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            if block:
                break
            continue
        block.append(line[2:] if line.startswith("> ") else line)
    text = " ".join(s.strip() for s in block)
    text = re.sub(r"\[([^]]*)\]\([^)]*\)", r"\1", text)  # [label](url) -> label
    text = text.replace("`", "")
    # Strip *emphasis* / _emphasis_ pairs only — a lone glob star (*.slide.typ) survives.
    text = re.sub(r"(?<!\S)([*_])(\S(?:[^*_]*?\S)?)\1(?!\S)", r"\2", text).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    if m:
        text = m.group(1)
    return text if len(text) <= 110 else text[:107].rstrip() + "…"


def cmd_docs(args: argparse.Namespace) -> int:
    docs = _doc_files()
    if args.name:
        key = args.name.upper().replace(" ", "-")
        if key not in docs:
            print(f"demolab docs: no runbook or guide named {args.name!r}. Run `demolab docs` for the list.",
                  file=sys.stderr)
            return 2
        if args.print and docs[key].is_file():
            print(docs[key].read_text(encoding="utf-8"))
        else:
            print(docs[key])
        return 0
    # Bare `demolab docs` IS the agent's orientation: the full manual, then the menu —
    # one command, complete operating context, always in step with the installed engine.
    print((_paths.PACKAGE / "AGENT.md").read_text(encoding="utf-8"))
    print("## The menu — runbooks are step-by-step procedures, guides are reference.")
    print("## `demolab docs <NAME>` prints the file's path; read it and follow it.\n")
    for title, base in (("runbooks", _paths.RUNBOOKS), ("guides", _paths.GUIDES)):
        names = [n for n, p in docs.items() if p.parent == base]
        width = max(len(n) for n in names)
        print(f"  {title}")
        for n in names:
            print(f"    {n:<{width}}  {_doc_summary(docs[n])}")
        print()
    print("  reference")
    print("    AGENT      this manual (the text above)")
    print("    CHANGELOG  what changed in each engine version")
    print("    DEMO       the published docs site's source (writeup examples), never copy by hand")
    print("    STARTERS   canonical first-experiment references (e.g. monte-carlo-pi)")
    return 0


# ── setup ──────────────────────────────────────────────────────────────────
def cmd_install(args: argparse.Namespace) -> int:
    return _run("uv", "sync", cwd=_paths.require_lab_root())


def cmd_version(args: argparse.Namespace) -> int:
    print(_paths.VERSION)
    return 0


# ── scaffolding ────────────────────────────────────────────────────────────
def cmd_scaffold(args: argparse.Namespace) -> int:
    # Repair/extend an existing lab, or lay the bare structure into the cwd (writing
    # demolab.yaml makes it a lab). Never clobbers an existing file.
    target = _paths.find_lab_root() or Path.cwd()
    overlay(_paths.SCAFFOLD / "skeleton", target, keep_existing=True)
    print("✓ scaffolded the folder structure. Add a writeup in writings/ and run 'demolab build'.")
    print("  (building a first experiment? ask your agent to follow GETTING-STARTED, or read a")
    print("   reference with 'demolab docs STARTERS' — e.g. monte-carlo-pi.)")
    return 0


def cmd_deploy_setup(args: argparse.Namespace) -> int:
    lab = _paths.require_lab_root()
    dst = lab / ".github" / "workflows"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(_paths.DEPLOY / "deploy.yml", dst / "deploy.yml")
    shutil.copy(_paths.DEPLOY / "preview.yml", dst / "preview.yml")
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
    return _run("uv", "run", "python", f"experiments/{args.experiment}.py",
                cwd=_paths.require_lab_root())


def cmd_new(args: argparse.Namespace) -> int:
    print("Experiments aren't scaffolded from a template — ask your coding agent.")
    print("It models a *working* skeleton on an existing pair:")
    print("  experiments/expNNN.py  — a runner with real COMMANDS that stages artifacts/data/expNNN/")
    print("  writings/expNNN.typ    — a #let meta + #let body that read that bundle via json()/image()")
    print()
    print('Try: "scaffold a new experiment expNNN that computes <thing>"')
    print("See AGENTS.md (entry point) and `demolab docs RULES` (how to add one).")
    return 0


# ── publishing ─────────────────────────────────────────────────────────────
def cmd_dev(args: argparse.Namespace) -> int:
    port_args = [str(args.port)] if args.port else []
    if not args.demo:
        if args.landing:
            print("--landing only applies to --demo. For your own lab, create a landing.typ at the",
                  file=sys.stderr)
            print("lab root and `demolab dev` renders it (and hot-reloads it).", file=sys.stderr)
            return 2
        return _mod("devserver", *port_args, cwd=_paths.require_lab_root())
    # --demo: materialise the shipped demo as a disposable lab under temp/ and serve that.
    # (The demo ships in site-packages, which Typst can't read from and we never write into.)
    lab = _paths.require_lab_root()
    scratch = lab / "temp" / "demo-preview"
    shutil.rmtree(scratch, ignore_errors=True)
    overlay(_paths.SCAFFOLD / "skeleton", scratch)
    overlay(_paths.SCAFFOLD / "demo", scratch, exclude=("site", "temp"))
    if args.landing:
        shutil.copy(_paths.SCAFFOLD / "demo" / "site" / "landing.typ", scratch / "landing.typ")
        print("→ previewing the upstream landing page too (site/landing.typ)")
    print(f"→ serving the shipped demo from a scratch copy ({scratch.relative_to(lab)})")
    env = {**os.environ, "DEMOLAB_ROOT": str(scratch)}
    return _mod("devserver", *port_args, cwd=scratch, env=env)


def cmd_build(args: argparse.Namespace) -> int:
    return _mod("build", cwd=_paths.require_lab_root())


def cmd_slides(args: argparse.Namespace) -> int:
    return _mod("slides", cwd=_paths.require_lab_root())


def cmd_playground(args: argparse.Namespace) -> int:
    return _run("uv", "run", "streamlit", "run", "experiments/playground.py",
                cwd=_paths.require_lab_root())


# ── quality & housekeeping ─────────────────────────────────────────────────
def cmd_test(args: argparse.Namespace) -> int:
    code = _run("uv", "run", "pytest", cwd=_paths.require_lab_root())
    if code == 5:  # pytest: no tests collected — a fresh lab has none yet; not a failure
        print("no tests collected yet (add some under tools/ or experiments/)")
        return 0
    return code


def cmd_clean(args: argparse.Namespace) -> int:
    lab = _paths.require_lab_root()
    for rel in ("temp", "artifacts/site"):
        shutil.rmtree(lab / rel, ignore_errors=True)
    print("✓ removed temp/ and artifacts/site/")
    return 0


HANDLERS = {
    "init": cmd_init,
    "docs": cmd_docs,
    "install": cmd_install,
    "version": cmd_version,
    "scaffold": cmd_scaffold,
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
    if _paths.find_lab_root() is None:
        print("  (you're not inside a lab — start one with `demolab init` in an empty directory)")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="demolab", add_help=True,
                                description="The lab's command runner (the demolab-cli package).")
    sub = p.add_subparsers(dest="command", metavar="<command>")
    help_by_name = {name: desc for _, cmds in GROUPS for name, desc in cmds}
    for name in HANDLERS:
        sp = sub.add_parser(name, help=help_by_name[name])
        if name == "init":
            sp.add_argument("--force", action="store_true",
                            help="init into a non-empty directory / inside an existing lab (overwrites colliding root files)")
        elif name == "docs":
            sp.add_argument("name", nargs="?", help="runbook or guide name, e.g. GETTING-STARTED, RULES, CHANGELOG")
            sp.add_argument("--print", action="store_true", help="print the document instead of its path")
        elif name == "run":
            sp.add_argument("experiment", help="experiment id, e.g. exp000 (runs experiments/exp000.py)")
        elif name == "dev":
            sp.add_argument("port", nargs="?", type=int, help="port to serve on (default: first free from 3000)")
            sp.add_argument("--demo", action="store_true", help="serve the shipped demo instead of your lab")
            sp.add_argument("--landing", action="store_true",
                            help="with --demo: preview the upstream landing page too")
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
