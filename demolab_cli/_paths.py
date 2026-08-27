"""Shared path model: where the package's data lives, where the user's lab is, and the
`.demolab/` staging dir that bridges the two for Typst.

The engine ships in site-packages, but typst `--root` confines all file reads to the lab
tree — so the handful of files Typst must read (lib.typ, imported by user writings; the web
assets + VERSION, read by lib.typ/main.typ) are materialised into a gitignored `.demolab/`
at the lab root, refreshed whenever the installed package version changes. Everything else
is read from the package directly.

The engine checkout keeps authored inputs under .demo/, while Typst's root and
the disposable .demolab/ runtime remain at the checkout root. Ordinary labs
retain their original root-relative content paths.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PureWindowsPath
from typing import Iterator

PACKAGE = Path(__file__).resolve().parent
TYP = PACKAGE / "typ"
SCAFFOLD = PACKAGE / "scaffold"
DEPLOY = PACKAGE / "deploy"
GUIDES = PACKAGE / "guides"
VERSION = (PACKAGE / "VERSION").read_text().strip()

MARKER = "demolab.yaml"

# Everything stage() writes into <lab>/.demolab/ (plus the VERSION stamp).
_STAGED = ("lib.typ", "style.css", "cite-popover.js", "favicon.svg")


class LayoutError(ValueError):
    """An invalid source configuration, suitable for a user-facing diagnostic."""


def find_typst(root: Path) -> str:
    """Prefer the lab-local compiler, then PATH (including typst.exe on Windows)."""
    for name in ("typst.exe", "typst"):
        local = root / ".tools" / "bin" / name
        if local.is_file():
            return str(local)
    return shutil.which("typst") or "typst"


@lru_cache(maxsize=16)
def _writings_setting(root: Path, config: Path, contents: str) -> tuple[object, str | None]:
    """Use Typst's YAML parser; cache successes AND failures until the file changes.

    contents is the cache key, not an expression: authored YAML is never executed as code.
    This is lazy, so init, clean, docs, and importing the engine need no compiler.
    """
    config_path = "/" + config.relative_to(root).as_posix()
    expression = (
        "{ let c = yaml(" + json.dumps(config_path) + "); "
        'if c == none { "writings" } else { c.at("writings", default: "writings") } }'
    )
    try:
        result = subprocess.run(
            [find_typst(root), "eval", "--root", str(root), expression],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        # Some Typst eval versions report expression errors on stderr with status 0.
        if result.returncode or not result.stdout.strip():
            return None, result.stderr.strip() or result.stdout.strip() or "Typst evaluation failed"
        return json.loads(result.stdout), None
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return None, str(exc)


def is_demo_checkout(root: Path) -> bool:
    """Only the engine source checkout uses .demo; ordinary lab markers take precedence."""
    return (not (root / MARKER).is_file()
            and (root / ".demo" / MARKER).is_file()
            and (root / "demolab_cli" / "build.py").is_file()
            and (root / "demolab_cli" / "VERSION").is_file())


@dataclass(frozen=True)
class LabLayout:
    """Read-only input locations and disposable runtime, within one Typst root."""

    root: Path
    content: Path
    demo: bool = False

    @property
    def config(self) -> Path:
        return self.content / MARKER

    @property
    def writings(self) -> Path:
        value: object = "writings"
        if self.config.is_file():
            try:
                contents = self.config.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise LayoutError(f"cannot read {self.config}: {exc}") from exc
            value, error = _writings_setting(self.root, self.config, contents)
            if error:
                raise LayoutError(f"cannot read writings from {self.config}:\n{error}")
        if (not isinstance(value, str) or not value.strip() or "\x00" in value
                or "\\" in value or PureWindowsPath(value).drive
                or value.startswith("/") or ".." in Path(value).parts
                or Path(value) == Path(".")):
            raise LayoutError("demolab.yaml 'writings' must be a relative directory using forward slashes")
        path = self.content / value
        self.validate_source(path)
        if path.exists() and not path.is_dir():
            raise LayoutError(f"writings is not a directory: {path}")
        if not path.exists() and Path(value) != Path("writings"):
            raise LayoutError(f"configured writings directory does not exist: {path}")
        return path

    def validate_source(self, path: Path) -> None:
        """Never discover or watch sources outside authored content or in generated runtime."""
        try:
            resolved = path.resolve()
            relative = resolved.relative_to(self.content.resolve())
        except (OSError, RuntimeError, ValueError) as exc:
            raise LayoutError(f"source path escapes the content directory or cannot be resolved: {path}") from exc
        if (".demolab" in relative.parts or resolved.is_relative_to(self.runtime.resolve())
                or self.runtime.resolve().is_relative_to(resolved)):
            raise LayoutError(f"writings must not include generated .demolab runtime: {path}")

    def source_files(self, directory: Path | None = None) -> Iterator[Path]:
        """Recursively scan visible sources; directory symlinks are checked but not followed."""
        directory = self.writings if directory is None else directory
        self.validate_source(directory)
        if not directory.exists():
            return  # the default writings/ may be absent in an empty lab

        def scan_error(error: OSError) -> None:
            raise LayoutError(f"cannot scan writings: {error}") from error

        for base, dirs, files in os.walk(directory, followlinks=False, onerror=scan_error):
            parent = Path(base)
            kept = []
            for name in sorted(dirs):
                if name.startswith("."):
                    continue
                path = parent / name
                self.validate_source(path)
                if not path.is_symlink():
                    kept.append(name)
            dirs[:] = kept
            for name in sorted(files):
                if name.startswith("."):
                    continue
                path = parent / name
                self.validate_source(path)
                if path.is_file():
                    yield path

    @property
    def assets(self) -> Path:
        return self.content / "assets"

    @property
    def landing(self) -> Path:
        return self.content / "landing.typ"

    @property
    def data(self) -> Path:
        return self.content / "data" if self.demo else self.root / ".artifacts"

    @property
    def runtime(self) -> Path:
        return self.root / ".demolab"

    def typst_path(self, path: Path) -> str:
        relative = path.relative_to(self.root).as_posix()
        return "" if relative == "." else "/" + relative

    def typst_inputs(self) -> list[str]:
        return ["--input", f"demolab-content-root={self.typst_path(self.content)}",
                "--input", f"demolab-data-root={self.typst_path(self.data)}"]


def layout_for(root: Path) -> LabLayout:
    root = root.resolve()
    if root.name == ".demo" and is_demo_checkout(root.parent):
        root = root.parent
    demo = is_demo_checkout(root)
    return LabLayout(root, root / ".demo" if demo else root, demo)


def find_lab_root(start: Path | None = None) -> Path | None:
    """Find an ordinary lab or the engine checkout owning the .demo content."""
    start = (start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if d.name == ".demo" and is_demo_checkout(d.parent):
            return d.parent
        if (d / MARKER).is_file():
            return d
        if is_demo_checkout(d):
            return d
    return None


def require_lab_root() -> Path:
    root = find_lab_root()
    if root is None:
        sys.exit("demolab: not inside a lab (no demolab.yaml found from here upward).\n"
                 "  Start one with `demolab init` in an empty directory.")
    return root


def stage(root: Path) -> Path:
    """Materialise <root>/.demolab/ (idempotent; refreshed on version-stamp mismatch).
    Returns the staging dir."""
    dot = layout_for(root).runtime
    stamp = dot / "VERSION"
    prev = stamp.read_text().strip() if stamp.is_file() else None
    # Freshness is mtime equality, not just the version stamp: with an editable install the
    # source files change without a version bump (copy2 preserves mtimes, so unchanged files
    # compare equal). Without this, `demolab dev` rebuilds on an engine asset edit but keeps
    # serving the stale staged copy.
    def _fresh(name: str) -> bool:
        staged = dot / name
        return staged.is_file() and staged.stat().st_mtime_ns == (TYP / name).stat().st_mtime_ns
    if prev == VERSION and all(_fresh(n) for n in _STAGED):
        return dot
    dot.mkdir(exist_ok=True)
    for name in _STAGED:
        shutil.copy2(TYP / name, dot / name)
    stamp.write_text(VERSION + "\n")
    if prev and prev != VERSION:
        print(f"→ engine {prev} → {VERSION} — run `demolab docs CHANGELOG --print` to see what changed",
              flush=True)
    return dot
