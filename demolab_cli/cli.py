#!/usr/bin/env python3
"""demolab — the lab's command runner (the demolab-cli package entry point).

The engine lives in this package (site-packages); a lab is a plain directory of user
content marked by its demolab.yaml. Every command finds the lab by walking up from the
cwd, like git finding its root — so it works from any subdirectory. `demolab init` starts
a new presentation; `demolab docs` lists the authoring guides that ship in the package.
Run `demolab` with no arguments for the command list. The CLI is pure stdlib Python;
Typst performs the rendering.
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
        ("init", "✨ Start a presentation in the current directory"),
        ("docs", "📚 List the authoring guides; `demolab docs <NAME>` prints one"),
        ("version", "🔖 Print the demolab engine version"),
        ("deploy-setup", "🚀 Opt in to GitHub Pages — copy the deploy + preview workflows into .github/workflows/"),
    ]),
    ("publishing", [
        ("dev", "🔥 Serve the site with hot-reload + in-browser build errors (PORT overrides the auto-picked 3000)"),
        ("build", "📦 Build the publication → artifacts/site/ (web) + optional artifacts/pdfs/"),
        ("clean", "🧹 Delete regenerable build output (.demolab/bundle/, artifacts/site/)"),
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
        sys.exit(f"demolab init: already inside a presentation ({existing}); use --force "
                 "to lay a new presentation over this directory anyway.")
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
    # The content structure (demolab.yaml — the lab marker — HOUSESTYLE.local.md, empty dirs).
    overlay(_paths.SCAFFOLD / "skeleton", target, keep_existing=True)
    _paths.stage(target)
    _git_init(target)
    print(f"✓ Your presentation is ready. (demolab {_paths.VERSION})\n")
    print("  In one terminal tab, the live preview:")
    print("      uv run demolab dev")
    print("\n  Add a .typ file under writings/; see `uv run demolab docs AUTHORING`.")
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
    commit = subprocess.run(["git", "commit", "--quiet", "-m", "Start my presentation with demolab"],
                            cwd=target, capture_output=True, text=True)
    if commit.returncode != 0:
        print("  (git initialised; make the first commit yourself — `git commit` needs your identity)")


def _doc_files() -> dict[str, Path]:
    """Every guide shipped in the package, plus the manual and changelog."""
    docs: dict[str, Path] = {}
    for p in sorted(_paths.GUIDES.glob("*.md")):
        docs[p.stem] = p
    docs["AGENT"] = _paths.PACKAGE / "AGENT.md"
    docs["CHANGELOG"] = _paths.PACKAGE / "CHANGELOG.md"
    return docs


def _doc_summary(p: Path) -> str:
    """The doc's one-liner: the first paragraph after its heading, joined across lines,
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
            print(f"demolab docs: no guide named {args.name!r}. Run `demolab docs` for the list.",
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
    print("## Guides")
    print("## `demolab docs <NAME>` prints a guide's path.\n")
    names = [n for n, p in docs.items() if p.parent == _paths.GUIDES]
    width = max(len(n) for n in names)
    for n in names:
        print(f"    {n:<{width}}  {_doc_summary(docs[n])}")
    print()
    print("  reference")
    print("    AGENT      this manual (the text above)")
    print("    CHANGELOG  what changed in each engine version")
    return 0


# ── setup ──────────────────────────────────────────────────────────────────
def cmd_version(args: argparse.Namespace) -> int:
    print(_paths.VERSION)
    return 0


# ── scaffolding ────────────────────────────────────────────────────────────
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
# ── publishing ─────────────────────────────────────────────────────────────
def cmd_dev(args: argparse.Namespace) -> int:
    port_args = [str(args.port)] if args.port else []
    return _mod("devserver", *port_args, cwd=_paths.require_lab_root())


def cmd_build(args: argparse.Namespace) -> int:
    entry_args = [args.entry] if args.entry else []
    return _mod("build", *entry_args, cwd=_paths.require_lab_root())


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
    for rel in (".demolab/bundle", "artifacts/site"):
        shutil.rmtree(lab / rel, ignore_errors=True)
    print("✓ removed .demolab/bundle/ and artifacts/site/")
    return 0


HANDLERS = {
    "init": cmd_init,
    "docs": cmd_docs,
    "version": cmd_version,
    "deploy-setup": cmd_deploy_setup,
    "dev": cmd_dev,
    "build": cmd_build,
    "clean": cmd_clean,
}


def _print_catalog() -> None:
    print("demolab — presentation command runner. Usage: demolab <command> [args]\n")
    width = max(len(name) for _, cmds in GROUPS for name, _ in cmds)
    for title, cmds in GROUPS:
        print(f"  {title}")
        for name, desc in cmds:
            print(f"    {name:<{width}}  {desc}")
        print()
    if _paths.find_lab_root() is None:
        print("  (you're not inside a presentation — start one with `demolab init`)")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="demolab", add_help=True,
                                description="The presentation command runner (demolab-cli).")
    sub = p.add_subparsers(dest="command", metavar="<command>")
    help_by_name = {name: desc for _, cmds in GROUPS for name, desc in cmds}
    for name in HANDLERS:
        sp = sub.add_parser(name, help=help_by_name[name])
        if name == "init":
            sp.add_argument("--force", action="store_true",
                            help="init into a non-empty directory / inside an existing lab (overwrites colliding root files)")
        elif name == "docs":
            sp.add_argument("name", nargs="?", help="guide name, e.g. AUTHORING, RULES, CHANGELOG")
            sp.add_argument("--print", action="store_true", help="print the document instead of its path")
        elif name == "dev":
            sp.add_argument("port", nargs="?", type=int, help="port to serve on (default: first free from 3000)")
        elif name == "build":
            sp.add_argument("entry", nargs="?",
                            help="build only this entry PDF; omit for the complete publication")
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
