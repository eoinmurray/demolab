"""Opt-in, request-local Typst inputs. No discovery or shared selection state."""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path, PureWindowsPath
from urllib.parse import parse_qsl, quote, unquote, urlsplit

from demolab_cli import _paths, data_sources
from demolab_cli.preview import bounded_command

COMPILE_LOCK = threading.RLock()
PREFIX = "/__render/"
RESERVED = {"entry", "entry-source", "has-brand"}


class InputError(ValueError):
    """Invalid URL input or failed isolated rendering."""


@lru_cache(maxsize=16)
def _setting(root: Path, config: Path, contents: str):
    expression = ('{ let c = yaml(' + json.dumps('/' + config.relative_to(root).as_posix())
                  + '); if c == none { (:) } else { c } }')
    proc = subprocess.run([_paths.find_typst(root), "eval", "--root", str(root), expression],
                          capture_output=True, text=True, timeout=10)
    if proc.returncode or not proc.stdout.strip():
        raise InputError(proc.stderr.strip() or "cannot read url_inputs")
    config_value = json.loads(proc.stdout)
    if not isinstance(config_value, dict):
        raise InputError("demolab.yaml must contain a mapping")
    return config_value


def safe_directory(layout, relative: str, *, root: Path | None = None) -> Path:
    if (not isinstance(relative, str) or not relative or relative.startswith("/")
            or "\\" in relative or PureWindowsPath(relative).drive
            or any(ord(c) < 32 for c in relative)
            or any(part in ("", ".", "..") for part in relative.split("/"))):
        raise InputError("path inputs must be relative directories without traversal")
    path = layout.content / relative
    boundary = root or layout.content
    if not path.is_relative_to(boundary) or path.is_relative_to(layout.runtime):
        raise InputError("path input escapes its configured root")
    for item in (path, *path.parents):
        if item == layout.root:
            break
        if item.is_symlink():
            raise InputError("path inputs must not use symlinks")
    if not path.is_dir():
        raise InputError(f"input directory does not exist: {relative}")
    return path


def load_config(layout) -> dict:
    if not layout.config.is_file():
        return {}
    settings = _setting(layout.root, layout.config, layout.config.read_text(encoding="utf-8")).get("url_inputs", {})
    if not isinstance(settings, dict):
        raise InputError("url_inputs must map compiler-input names to type declarations")
    for name, spec in settings.items():
        if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", name)
                or name.startswith("demolab-") or name in RESERVED):
            raise InputError(f"reserved or invalid URL input: {name}")
        if not isinstance(spec, dict) or set(spec) - {"type", "root"}:
            raise InputError(f"url_inputs.{name} accepts only type and root")
        if spec.get("type") not in {"string", "path"}:
            raise InputError(f"url_inputs.{name}.type must be string or path")
        if spec["type"] == "path":
            safe_directory(layout, spec.get("root"))
        elif "root" in spec:
            raise InputError("only path inputs accept a root")
    return settings


def prepare(layout, *, inputs: dict | None = None, article: str = "") -> bool:
    """Run an optional author-owned preparation/validation command before compilation."""
    if not layout.config.is_file():
        return False
    config = _setting(layout.root, layout.config, layout.config.read_text(encoding="utf-8"))
    command = config.get("prepare")
    if command is None:
        return False
    if (not isinstance(command, list) or not command
            or any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in command)):
        raise InputError("prepare must be a nonempty command argument array (no shell)")
    bounded_command(command, cwd=layout.content, timeout=120,
                    env={**os.environ, "DEMOLAB_INPUTS": json.dumps(inputs or {}),
                         "DEMOLAB_ARTICLE": article})
    return True


def resolve_query(layout, query: str) -> tuple[dict, list[Path]]:
    if len(query) > 8192:
        raise InputError("URL inputs exceed 8192 characters")
    if re.search(r"%(?![0-9A-Fa-f]{2})", query):
        raise InputError("invalid percent escape in query string")
    settings = load_config(layout)
    try:
        pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True,
                          max_num_fields=64, encoding="utf-8", errors="strict")
    except (ValueError, UnicodeError) as exc:
        raise InputError("invalid query string") from exc
    inputs, directories = {}, []
    for name, value in pairs:
        if name not in settings:
            raise InputError(f"URL input is not allowed: {name}")
        if name in inputs:
            raise InputError(f"duplicate URL input: {name}")
        if len(value) > 2048 or any(ord(c) < 32 for c in value):
            raise InputError(f"invalid value for {name}")
        if settings[name]["type"] == "path":
            root = safe_directory(layout, settings[name]["root"])
            directory = safe_directory(layout, value, root=root)
            # Validate descendants too: a permitted directory must not hide a symlink.
            data_sources.directory_files(directory, layout)
            directories.append(directory)
            value = layout.typst_path(directory)
        inputs[name] = value
    if not inputs:
        raise InputError("at least one URL input is required")
    return inputs, directories


def article_source(layout, path: str) -> tuple[str, Path]:
    slug = path.strip("/").removesuffix(".html")
    if not slug or "/" in slug or slug in {".", ".."}:
        raise InputError("URL inputs apply only to article pages")
    matches = [p for p in layout.source_files() if p.name == slug + ".typ"]
    if len(matches) != 1:
        raise InputError(f"unknown or ambiguous article: {slug}")
    source = matches[0]
    lines = source.read_text(encoding="utf-8").splitlines()
    if not all(any(line.startswith("#let " + export) for line in lines) for export in ("meta", "body")):
        raise InputError(f"not an article: {slug}")
    return slug, source


class ResourceURLs(HTMLParser):
    """Keep rendered assets in their request namespace, normal navigation at the lab root."""
    def __init__(self, site: Path, prefix: str):
        super().__init__(convert_charrefs=False)
        self.site, self.prefix, self.parts = site, prefix, []

    def handle_starttag(self, tag, attrs):
        original = self.get_starttag_text()
        for key, value in attrs:
            old_value = value
            if value and key in {"src", "href", "poster"}:
                parsed = urlsplit(value)
                if not parsed.scheme and not parsed.netloc and not value.startswith(("#", "/", "?")):
                    relative = unquote(parsed.path)
                    path = (self.site / relative).resolve()
                    if path.is_relative_to(self.site.resolve()) and path.is_file() and path.suffix != ".html":
                        value = self.prefix + quote(relative, safe="/")
                        if parsed.query:
                            value += "?" + parsed.query
                        if parsed.fragment:
                            value += "#" + parsed.fragment
                    else:
                        value = "/" + value
            if value != old_value:
                pattern = r"(\s" + re.escape(key) + r"\s*=\s*)(?:\"[^\"]*\"|'[^']*'|[^\s>]+)"
                original = re.sub(pattern, lambda match: match[1] + '"' + html.escape(value, quote=True) + '"',
                                  original, count=1, flags=re.I)
        self.parts.append(original)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        self.parts.append("</" + tag + ">")
    def handle_data(self, data):
        self.parts.append(data)
    def handle_entityref(self, name):
        self.parts.append("&" + name + ";")
    def handle_charref(self, name):
        self.parts.append("&#" + name + ";")
    def handle_comment(self, data):
        self.parts.append("<!--" + data + "-->")
    def handle_decl(self, decl):
        self.parts.append("<!" + decl + ">")


def render(layout, path: str, query: str, *, timeout: int = 120) -> tuple[str, Path]:
    """Compile one article into a fresh immutable namespace; never touch publication output."""
    inputs, directories = resolve_query(layout, query)
    slug, source = article_source(layout, path)
    # Serialize with normal dev compilation to protect the shared staged engine helpers.
    with COMPILE_LOCK:
        prepare(layout, inputs=inputs, article=slug)
        _paths.stage(layout.root)
        parent = layout.runtime / "url-inputs"
        parent.mkdir(parents=True, exist_ok=True)
        runtime = Path(tempfile.mkdtemp(prefix="view-", dir=parent))
        site = runtime / "site"
        try:
            selected = {"request": {str(i): layout.typst_path(p) for i, p in enumerate(directories)}}
            inventory = data_sources.inventory(layout, selected)
            # These are assets only; generic URL inputs have no engine-owned source mapping.
            inventory["sources"] = {}
            (runtime / "data-inputs.json").write_text(json.dumps(inventory), encoding="utf-8")
            manifest = {"id": slug, "source": layout.typst_path(source),
                        "has_config": layout.config.is_file(),
                        "assets": [p.relative_to(layout.assets).as_posix()
                                   for p in sorted(layout.assets.rglob("*")) if p.is_file()],
                        "media": inventory["media"]}
            (runtime / "index.json").write_text(json.dumps(manifest), encoding="utf-8")
            main = runtime / "main.typ"
            shutil.copy2(_paths.TYP / "url-entry.typ", main)
            args = [_paths.find_typst(layout.root), "compile", "--format", "bundle",
                    "--features", "bundle,html", "--root", str(layout.root),
                    "--creation-timestamp", os.environ.get("SOURCE_DATE_EPOCH", "946684800"),
                    *layout.typst_inputs(), "--input", "demolab-url-render=true",
                    "--input", "demolab-dev=true",
                    "--input", "demolab-url-article=" + slug,
                    "--input", "demolab-url-root=" + layout.typst_path(runtime),
                    "--input", "demolab-data-inputs=" + layout.typst_path(runtime / "data-inputs.json")]
            for key, value in sorted(inputs.items()):
                args += ["--input", key + "=" + value]
            proc = subprocess.run([*args, str(main), str(site) + "/"],
                                  capture_output=True, text=True, timeout=timeout)
            if proc.returncode:
                raise InputError("article rendering failed:\n" + proc.stdout + proc.stderr)
            page = site / (slug + ".html")
            rewrite = ResourceURLs(site, PREFIX + runtime.name + "/")
            rewrite.feed(page.read_text(encoding="utf-8"))
            rewrite.close()
            return "".join(rewrite.parts), site
        except Exception:
            shutil.rmtree(runtime)
            raise


def resource(layout, path: str) -> Path:
    tail = path.removeprefix(PREFIX)
    token, sep, relative = tail.partition("/")
    if not sep or not re.fullmatch(r"view-[a-z0-9_]+", token):
        raise InputError("invalid rendering resource")
    site = layout.runtime / "url-inputs" / token / "site"
    result = (site / relative).resolve()
    if not result.is_relative_to(site.resolve()) or not result.is_file():
        raise InputError("rendering resource does not exist")
    return result
