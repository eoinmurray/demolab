"""Publication input resolution and public video paths, independent of run storage formats."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path, PureWindowsPath

from demolab_cli import _paths, preview

VIDEO_SUFFIXES = {".mp4", ".webm", ".ogg", ".ogv", ".mov", ".m4v"}
MEDIA_PREFIX = "_demolab-data"


def identifier(value, label):
    if (not isinstance(value, str) or not value.strip() or value in (".", "..")
            or any(c in value for c in "/\\") or any(ord(c) < 32 for c in value)):
        raise _paths.LayoutError(f"{label} must be a nonempty identifier without slashes or control characters")


def directory_files(directory: Path, layout: _paths.LabLayout) -> list[Path]:
    """Validate containment and regular files without following symlinks."""
    directory = Path(os.path.abspath(directory))
    if (not directory.is_relative_to(layout.root) or directory.is_relative_to(layout.runtime)
            or layout.runtime.is_relative_to(directory)):
        raise _paths.LayoutError(f"data source must stay inside the lab and outside .demolab: {directory}")
    for path in (directory, *directory.parents):
        if path == layout.root:
            break
        if path.is_symlink():
            raise _paths.LayoutError(f"data sources must not use symlinks: {path}")
    if not directory.is_dir():
        raise _paths.LayoutError(f"data source directory does not exist: {directory}")

    def scan_error(error):
        raise _paths.LayoutError(f"cannot read data source: {error}") from error

    files = []
    for base, dirs, names in os.walk(directory, followlinks=False, onerror=scan_error):
        for name in dirs + names:
            path = Path(base) / name
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise _paths.LayoutError(f"data sources require regular files, not symlinks or special files: {path}")
        files.extend(Path(base) / name for name in names)
    return sorted(files)


def load_build_sources(layout: _paths.LabLayout, article_ids) -> dict:
    """Read only build.sources; never invoke discovery or load local preview state."""
    if not layout.config.is_file():
        return {}
    expression = ('{ let c = yaml(' + json.dumps(layout.typst_path(layout.config))
                  + '); if c == none { none } else { c.at("build", default: none) } }')
    try:
        result = subprocess.run([_paths.find_typst(layout.root), "eval", "--root", str(layout.root), expression],
                                capture_output=True, text=True, encoding="utf-8", timeout=10)
        if result.returncode or not result.stdout.strip():
            raise ValueError(result.stderr.strip() or "Typst evaluation failed")
        setting = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise _paths.LayoutError(f"cannot read build configuration: {exc}") from exc
    if setting is None:
        return {}
    if not isinstance(setting, dict) or set(setting) - {"sources"}:
        raise _paths.LayoutError("build accepts only sources")
    sources = setting.get("sources", {})
    if not isinstance(sources, dict):
        raise _paths.LayoutError("build.sources must map article IDs to data-key/directory mappings")
    normalized = {}
    for article, inputs in sources.items():
        identifier(article, "build article ID")
        if article not in article_ids:
            raise _paths.LayoutError(f"unknown build article ID: {article}")
        if not isinstance(inputs, dict):
            raise _paths.LayoutError(f"build.sources.{article} must map data keys to directories")
        normalized[article] = {}
        for key, relative in inputs.items():
            identifier(key, "build data key")
            if (not isinstance(relative, str) or not relative.strip()
                    or any(ord(c) < 32 for c in relative) or "\\" in relative
                    or PureWindowsPath(relative).drive or relative.startswith("/")
                    or any(part in ("", ".", "..") for part in relative.split("/"))):
                raise _paths.LayoutError(f"{article} / {key}: build source must be a safe relative directory")
            normalized[article][key] = layout.typst_path(layout.content / relative)
    return normalized


def resolve_build_sources(layout: _paths.LabLayout, article_ids) -> dict:
    """Resolve Latest once per build, with explicit pins overriding whole articles.

    Reuse discovery's storage-neutral catalogue, never a preview Session or its saved
    choices. The discovery command is responsible for returning eligible presentation
    runs; its normalized created_at ordering determines Latest.
    """
    sources = load_build_sources(layout, article_ids)
    try:
        config = preview.load_config(layout)
        if config is None:
            return sources
        unknown = set(config.articles) - set(article_ids)
        if unknown:
            raise preview.PreviewError("unknown discovery article IDs: " + ", ".join(sorted(unknown)))
        catalogue = preview.discover(config, layout)
        latest = {}
        for run in catalogue:
            latest.setdefault(run["experiment"], run["presentation"])
        for article in article_ids:
            if article in sources:
                continue
            declared = config.articles.get(article, [article] if article in latest else [])
            inputs = preview.normalize_inputs(declared)
            if inputs:
                sources[article] = {item["key"]: latest.get(item["experiment"]) for item in inputs}
    except (preview.PreviewError, OSError) as exc:
        raise _paths.LayoutError(f"build discovery failed: {exc}") from exc
    return sources


def inventory(layout: _paths.LabLayout, sources: dict) -> dict:
    """Freeze paths once for all compiler targets. Export videos, not other run payloads."""
    directories = sorted({path for inputs in sources.values() for path in inputs.values() if path is not None})
    files = sorted({layout.typst_path(file) for path in directories
                    for file in directory_files(layout.root / path.lstrip("/"), layout)})
    media = {path: MEDIA_PREFIX + "/" + hashlib.sha256(path.encode("utf-8")).hexdigest() + Path(path).suffix.lower()
             for path in files if Path(path).suffix.lower() in VIDEO_SUFFIXES}
    if media and (layout.assets / MEDIA_PREFIX).exists():
        raise _paths.LayoutError(f"assets/{MEDIA_PREFIX} is reserved for run-backed videos")
    return {"sources": sources, "files": files, "directories": directories, "media": media}
