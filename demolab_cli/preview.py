"""Development-only discovery protocol and article-scoped selections. No storage conventions."""
from __future__ import annotations

import copy
import json
import os
import secrets
import signal
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path, PureWindowsPath

from demolab_cli import _paths

DISCOVERY_TIMEOUT = 30
OUTPUT_LIMIT = 4 * 1024 * 1024


class PreviewError(ValueError):
    """An actionable configuration, discovery, or selection error."""


def identifier(value, label):
    if (not isinstance(value, str) or not value.strip() or value in (".", "..")
            or any(c in value for c in "/\\\x00") or any(ord(c) < 32 for c in value)):
        raise PreviewError(f"{label} must be a nonempty identifier without slashes or control characters")
    return value


def contained(path: Path, root: Path, runtime: Path) -> Path:
    """Reject escaping paths and symlinks rather than silently broadening Typst's root."""
    absolute = Path(os.path.abspath(path))
    if not absolute.is_relative_to(root) or absolute.is_relative_to(runtime):
        raise PreviewError(f"preview path must stay inside the lab and outside .demolab: {path}")
    for component in (absolute, *absolute.parents):
        if component == root:
            break
        if component.is_symlink():
            raise PreviewError(f"preview paths must not use symlinks: {component}")
    return absolute


@lru_cache(maxsize=16)
def _read_setting(root: Path, config: Path, contents: str):
    # Use the same compiler-owned YAML parser as the writings setting, without a dependency.
    expression = ('{ let c = yaml(' + json.dumps('/' + config.relative_to(root).as_posix())
                  + '); if c == none { none } else { c.at("preview", default: none) } }')
    try:
        result = subprocess.run([_paths.find_typst(root), "eval", "--root", str(root), expression],
                                capture_output=True, text=True, timeout=10)
        if result.returncode or not result.stdout.strip():
            return None, result.stderr.strip() or "cannot read preview configuration"
        return json.loads(result.stdout), None
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)


@dataclass(frozen=True)
class Config:
    source: Path
    command: tuple[str, ...]
    articles: dict


def load_config(layout: _paths.LabLayout) -> Config | None:
    if not layout.config.exists():
        return None
    value, error = _read_setting(layout.root, layout.config, layout.config.read_text(encoding="utf-8"))
    if error:
        raise PreviewError(error)
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {"source", "discover", "articles"}:
        raise PreviewError("preview accepts only source, discover, and articles")
    source = value.get("source")
    if (not isinstance(source, str) or not source.strip() or "\x00" in source
            or "\\" in source or PureWindowsPath(source).drive or source.startswith("/")):
        raise PreviewError("preview.source must be a relative directory")
    source = contained(layout.content / source, layout.root, layout.runtime)
    if not source.is_dir() or source == layout.root or source in layout.runtime.parents:
        raise PreviewError("preview.source must name an existing, non-runtime source directory")
    command = value.get("discover")
    if (not isinstance(command, list) or not command
            or any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in command)):
        raise PreviewError("preview.discover must be a nonempty array of command arguments (no shell)")
    articles = value.get("articles", {})
    if not isinstance(articles, dict):
        raise PreviewError("preview.articles must map article IDs to lists or named groups")
    for article, inputs in articles.items():
        identifier(article, "article ID")
        normalize_inputs(inputs)  # validate even articles not currently discovered
    return Config(source, tuple(command), articles)


def normalize_inputs(value) -> list[dict]:
    groups = {"": value} if isinstance(value, list) else value
    if not isinstance(groups, dict):
        raise PreviewError("each article must contain an experiment list or a mapping of groups to lists")
    result, seen = [], set()
    for group, experiments in groups.items():
        if group:
            identifier(group, "group")
        elif not isinstance(value, list):
            raise PreviewError("group names must not be empty")
        if not isinstance(experiments, list):
            raise PreviewError("each group must contain an experiment list")
        for experiment in experiments:
            identifier(experiment, "experiment")
            key = f"{group}.{experiment}" if group else experiment
            if key in seen:
                raise PreviewError(f"duplicate or ambiguous data key: {key}")
            seen.add(key)
            result.append({"key": key, "experiment": experiment, "group": group})
    return result


def bounded_command(command, *, cwd, env, timeout=DISCOVERY_TIMEOUT, limit=OUTPUT_LIMIT):
    """Drain both pipes with hard memory limits; never invoke a shell."""
    try:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=os.name == "posix")
    except OSError as exc:
        raise PreviewError(f"cannot start discovery: {exc}") from exc
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()

    def stop():
        try:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass

    def drain(stream, buffer):
        try:
            while chunk := stream.read(8192):
                remaining = limit - len(buffer)
                buffer.extend(chunk[:max(0, remaining)])
                if len(chunk) > remaining:
                    overflow.set()
                    stop()
                    break
        finally:
            stream.close()

    threads = [threading.Thread(target=drain, args=(stream, buffer), daemon=True)
               for stream, buffer in zip((proc.stdout, proc.stderr), buffers)]
    for thread in threads:
        thread.start()
    try:
        proc.wait(timeout=timeout)
        for thread in threads:
            thread.join(timeout=1)
        if any(thread.is_alive() for thread in threads):
            stop()
            raise PreviewError("discovery left an output pipe open; commands must finish their child processes")
    except subprocess.TimeoutExpired as exc:
        stop()
        proc.wait()
        raise PreviewError(f"discovery timed out after {timeout}s") from exc
    finally:
        for thread in threads:
            thread.join(timeout=1)
    if overflow.is_set():
        raise PreviewError(f"discovery output exceeds {limit} bytes")
    stdout, stderr = (bytes(buffer).decode("utf-8", errors="replace") for buffer in buffers)
    if proc.returncode:
        raise PreviewError(f"discovery exited {proc.returncode}:\n{stderr.strip()}")
    return stdout


def validate_directory(path: Path, layout: _paths.LabLayout):
    contained(path, layout.root, layout.runtime)
    if not path.is_dir():
        raise PreviewError(f"presentation directory does not exist: {path}")
    def inaccessible(error):
        raise PreviewError(f"cannot read presentation directory: {error}")

    for base, dirs, files in os.walk(path, followlinks=False, onerror=inaccessible):
        for name in dirs + files:
            entry = Path(base) / name
            contained(entry, layout.root, layout.runtime)
            if not entry.is_dir() and not entry.is_file():
                raise PreviewError(f"presentation contains a non-regular file: {entry}")


def discover(config: Config, layout: _paths.LabLayout) -> list[dict]:
    output = bounded_command(config.command, cwd=layout.content,
                             env={**os.environ, "DEMOLAB_PREVIEW_SOURCE": str(config.source)})
    try:
        records = json.loads(output)
    except ValueError as exc:
        raise PreviewError(f"discovery must return a JSON array: {exc}") from exc
    if not isinstance(records, list):
        raise PreviewError("discovery must return a JSON array")
    seen, result = set(), []
    for record in records:
        if not isinstance(record, dict):
            raise PreviewError("each discovered run must be a JSON object")
        run_id = identifier(record.get("id"), "run ID")
        experiment = identifier(record.get("experiment"), "experiment")
        if run_id in seen:
            raise PreviewError(f"duplicate run ID: {run_id}")
        seen.add(run_id)
        label = record.get("label", run_id)
        if not isinstance(label, str) or not label.strip():
            raise PreviewError(f"run {run_id}: label must be a nonempty string")
        try:
            timestamp = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
            if timestamp.utcoffset() is None:
                raise ValueError("timezone required")
            timestamp = timestamp.astimezone(timezone.utc).isoformat()
        except (KeyError, ValueError, TypeError, AttributeError, OverflowError) as exc:
            raise PreviewError(f"run {run_id}: created_at must be an ISO timestamp with a timezone") from exc
        relative = record.get("presentation")
        if (not isinstance(relative, str) or not relative or "\x00" in relative
                or "\\" in relative or PureWindowsPath(relative).drive
                or relative.startswith("/") or ".." in Path(relative).parts):
            raise PreviewError(f"run {run_id}: presentation must be relative to preview.source")
        directory = contained(config.source / relative, layout.root, layout.runtime)
        if not directory.is_dir():
            raise PreviewError(f"run {run_id}: presentation directory does not exist: {directory}")
        result.append({"id": run_id, "experiment": experiment, "label": label,
                       "created_at": timestamp,
                       "presentation": layout.typst_path(directory)})
    return sorted(result, key=lambda run: (run["created_at"], run["id"]), reverse=True)


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class Session:
    """One server's accepted state and pending choices; compilation runs only on its worker."""

    def __init__(self, layout):
        self.layout = layout
        self.runtime = layout.runtime / "preview"
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.config = None
        self.catalogue = []
        self.inputs = {}
        self.accepted = {}
        self.rendered = {}
        self.error = ""
        self.stale = False
        self.busy = False
        self.pending = False
        self.revision = 0
        self.state_error = ""
        try:
            path = self.runtime / "state.json"
            if path.exists():
                state = json.loads(path.read_text(encoding="utf-8"))
                selections = state["selections"]
                if state.get("version") != 1 or not isinstance(selections, dict):
                    raise ValueError("unsupported state format")
                for article, choices in selections.items():
                    identifier(article, "saved article")
                    if not isinstance(choices, dict):
                        raise ValueError("invalid saved selections")
                    for key, choice in choices.items():
                        identifier(key, "saved data key")
                        if not isinstance(choice, str) or not (choice in ("latest", "published") or choice.startswith("run:")):
                            raise ValueError("invalid saved choice")
                self.accepted = selections
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.state_error = f"cannot read preview state: {exc}; use Reset selections to recover"
        self.desired = copy.deepcopy(self.accepted)

    def request(self, data):
        with self.lock:
            action = data.get("action")
            if action == "reset":
                self.desired = {}
                self.state_error = ""
            elif action == "article":
                article = identifier(data.get("article"), "article ID")
                selections = data.get("selections")
                if article not in self.inputs or not isinstance(selections, dict):
                    raise PreviewError("unknown article or invalid selections")
                inputs = {item["key"]: item for item in self.inputs[article]}
                for key, choice in selections.items():
                    if key not in inputs or not isinstance(choice, str):
                        raise PreviewError("unknown data key")
                    allowed = {"latest"} | {"run:" + run["id"] for run in self.catalogue
                                             if run["experiment"] == inputs[key]["experiment"]}
                    if choice not in allowed:
                        raise PreviewError(f"{key}: unavailable run {choice.removeprefix('run:')}")
                # Validate the whole fragment before changing any input. Other articles stay put.
                self.desired[article] = dict(selections)
                if data.get("reset") is True:
                    self.state_error = ""
            elif action == "select":
                article, key, choice = (data.get(field) for field in ("article", "key", "choice"))
                identifier(article, "article ID")
                identifier(key, "data key")
                item = next((item for item in self.inputs.get(article, []) if item["key"] == key), None)
                if item is None or not isinstance(choice, str):
                    raise PreviewError("unknown article or data key")
                allowed = {"latest", "published"} | {"run:" + run["id"] for run in self.catalogue
                                                         if run["experiment"] == item["experiment"]}
                if choice not in allowed:
                    raise PreviewError("unknown run for this input")
                self.desired.setdefault(article, {})[key] = choice
            elif action != "refresh":
                raise PreviewError("unknown preview action")
            self.pending = True
            self.revision += 1

    def status(self):
        with self.lock:
            return copy.deepcopy({"token": self.token, "articles": self.inputs, "runs": self.catalogue,
                                  "selections": self.desired, "rendered": self.rendered,
                                  "error": self.error or self.state_error, "stale": self.stale,
                                  "busy": self.busy or self.pending, "revision": self.revision})

    def watch(self):
        """Only authored inputs; never watch our generated catalogue/state/output."""
        signature = {}
        if self.config:
            for base, dirs, files in os.walk(self.config.source, followlinks=False):
                for name in dirs + files:
                    path = Path(base) / name
                    try:
                        stat = path.lstat()
                        signature[str(path)] = (stat.st_mtime_ns, stat.st_size)
                    except OSError:
                        pass
                dirs[:] = [name for name in dirs if not (Path(base) / name).is_symlink()]
            for arg in self.config.command:
                path = self.layout.content / arg
                try:
                    if path.is_file():
                        signature[str(path)] = path.stat().st_mtime_ns
                except OSError:
                    pass
        return signature

    def rebuild(self, config, article_ids, compile_preview):
        with self.lock:
            self.busy, self.pending = True, False
            self.config = config
            choices = copy.deepcopy(self.desired)
            requested_revision = self.revision
            # Explicit inputs remain visible even if discovery fails on first use.
            previous_inputs = self.inputs
            self.inputs = {article: normalize_inputs(value) for article, value in config.articles.items()
                           if article in article_ids}
            for article in article_ids:
                if article not in config.articles and (previous_inputs.get(article) == normalize_inputs([article])
                        or article in choices.get(article, {})
                        or any(r["experiment"] == article for r in self.catalogue)):
                    self.inputs[article] = normalize_inputs([article])
        try:
            unknown = set(config.articles) - set(article_ids)
            if unknown:
                raise PreviewError("unknown preview article IDs: " + ", ".join(sorted(unknown)))
            try:
                catalogue = discover(config, self.layout)
            except Exception:
                self.stale = True
                raise
            with self.lock:
                self.catalogue, self.stale = catalogue, False
                for article in article_ids:
                    if article not in config.articles and any(r["experiment"] == article for r in catalogue):
                        self.inputs[article] = normalize_inputs([article])
                inputs = copy.deepcopy(self.inputs)
            if self.state_error:
                raise PreviewError(self.state_error)
            mapping, rendered = {}, {}
            for article, items in inputs.items():
                mapping[article], rendered[article] = {}, {}
                for item in items:
                    key = item["key"]
                    choice = choices.get(article, {}).get(key, "latest")
                    if choice == "published":
                        rendered[article][key] = "Published/default"
                        continue
                    available = [r for r in catalogue if r["experiment"] == item["experiment"]]
                    if choice == "latest" and not available:
                        # Explicit absence, not an omitted override: never read publication
                        # defaults for an input whose preview has no runs yet.
                        mapping[article][key] = None
                        rendered[article][key] = None
                        continue
                    selected = (available[0] if available else None) if choice == "latest" else next(
                        (r for r in available if "run:" + r["id"] == choice), None)
                    if selected is None:
                        raise PreviewError(f"{article} / {key}: no available run for {choice}; choose another run or Reset to default")
                    directory = self.layout.root / selected["presentation"].lstrip("/")
                    validate_directory(directory, self.layout)
                    mapping[article][key] = selected["presentation"]
                    rendered[article][key] = selected["id"]
            atomic_json(self.runtime / "input.json", mapping)
            ok, message = compile_preview()
            if not ok:
                raise PreviewError(message)
            atomic_json(self.runtime / "state.json", {"version": 1, "selections": choices})
            with self.lock:
                self.accepted, self.rendered = choices, rendered
                self.error = ""
                # Requests arriving during compilation remain queued for the next build.
                if self.revision == requested_revision:
                    self.desired = copy.deepcopy(choices)
            return True, message
        except (PreviewError, OSError, ValueError) as exc:
            with self.lock:
                self.error = str(exc)
            return False, str(exc)
        finally:
            with self.lock:
                self.busy = False
