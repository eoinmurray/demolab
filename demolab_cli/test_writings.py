"""Configurable source roots, recursive discovery, and live watcher regression tests."""
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from demolab_cli import _paths, build, devserver


def configured_layout(tmp_path, monkeypatch, value="articles"):
    layout = _paths.layout_for(tmp_path)
    layout.config.write_text("# configuration is mocked in this unit test\n")
    monkeypatch.setattr(_paths, "_writings_setting", lambda *args: (value, None))
    return layout


def writing(path, *, deck=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('#let meta = (title: "Test", created_at: "2026-08-27")\n'
                    + ("Deck body.\n" if deck else "#let body = [Article body.]\n"))
    return path


def symlink(link, target):
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError:
        pytest.skip("symlinks are unavailable on this host")


def test_missing_config_keeps_default_without_invoking_typst(tmp_path, monkeypatch):
    def unexpected(*args):
        raise AssertionError("default without a config must not need Typst")
    monkeypatch.setattr(_paths, "_writings_setting", unexpected)
    layout = _paths.layout_for(tmp_path)
    assert layout.writings == tmp_path / "writings"
    assert list(layout.source_files()) == []


@pytest.mark.parametrize("value", [None, True, 42, [], {}, "", " ", ".", "..", "../outside",
                                  "/absolute", "C:/outside", "C:outside", "articles\\nested", "a\x00b"])
def test_invalid_writings_setting(tmp_path, monkeypatch, value):
    layout = configured_layout(tmp_path, monkeypatch, value)
    with pytest.raises(_paths.LayoutError, match="relative directory"):
        _ = layout.writings


@pytest.mark.parametrize("value", [".demolab", ".demolab/site", "articles/.demolab"])
def test_runtime_cannot_be_a_source_root(tmp_path, monkeypatch, value):
    layout = configured_layout(tmp_path, monkeypatch, value)
    with pytest.raises(_paths.LayoutError, match="generated .demolab"):
        _ = layout.writings


def test_missing_or_file_source_root_fails_clearly(tmp_path, monkeypatch):
    layout = configured_layout(tmp_path, monkeypatch)
    with pytest.raises(_paths.LayoutError, match="does not exist"):
        _ = layout.writings
    (tmp_path / "articles").write_text("not a directory")
    with pytest.raises(_paths.LayoutError, match="not a directory"):
        _ = layout.writings


def test_discovery_keeps_ids_independent_of_folders_and_ignores_helpers(tmp_path, monkeypatch):
    layout = configured_layout(tmp_path, monkeypatch)
    monkeypatch.setattr(build, "LAYOUT", layout)
    z = writing(tmp_path / "articles" / "first" / "z.typ")
    a = writing(tmp_path / "articles" / "last" / "deep" / "a.typ")
    deck = writing(tmp_path / "articles" / "talks" / "talk.slide.typ", deck=True)
    (a.parent / "helper.typ").write_text("#let greeting = [Hello]\n")
    (a.parent / "comment.typ").write_text("// #let meta = ()\n// #let body = []\n")
    (a.parent / "data.json").write_text("{}")
    writing(tmp_path / "articles" / ".hidden" / "hidden.typ")
    writing(tmp_path / "articles" / ".demolab" / "generated.typ")
    entries, decks = build.discover()
    assert list(entries) == ["a", "z"]
    assert entries == {"a": a, "z": z}
    assert decks == {"talk": deck}


@pytest.mark.parametrize("second", ["intro.typ", "intro.slide.typ", "INTRO.typ"])
def test_duplicate_ids_fail_with_both_sources(tmp_path, monkeypatch, second):
    layout = configured_layout(tmp_path, monkeypatch)
    monkeypatch.setattr(build, "LAYOUT", layout)
    first = writing(tmp_path / "articles" / "one" / "intro.typ")
    other = writing(tmp_path / "articles" / "two" / second, deck=second.endswith(".slide.typ"))
    with pytest.raises(_paths.LayoutError, match="duplicate writing ID") as error:
        build.discover()
    assert str(first) in str(error.value) and str(other) in str(error.value)


def test_failed_deck_cannot_be_reused_by_a_later_skip_decks_build(tmp_path, monkeypatch):
    source = writing(tmp_path / "nested" / "talk.slide.typ", deck=True)
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    output = output_dir / "talk.pdf"
    output.write_bytes(b"stale PDF")
    monkeypatch.setattr(build, "DECKS", output_dir)
    def failed_compile(*args, **kwargs):
        assert not output.exists()
        output.write_bytes(b"partial PDF")
        return SimpleNamespace(returncode=1, stdout="", stderr="error: broken helper")
    monkeypatch.setattr(build.subprocess, "run", failed_compile)
    assert build.compile_decks({"talk": source}) == {}
    assert not output.exists()


@pytest.mark.parametrize("kind", ["file", "directory", "root", "runtime"])
def test_escaping_and_runtime_symlinks_are_rejected(tmp_path, monkeypatch, kind):
    root = tmp_path / "lab"
    root.mkdir()
    layout = configured_layout(root, monkeypatch)
    outside = tmp_path / "outside"
    target = writing(outside / "article.typ")
    if kind == "root":
        symlink(root / "articles", outside)
        with pytest.raises(_paths.LayoutError, match="escapes"):
            _ = layout.writings
        return
    articles = root / "articles"
    articles.mkdir()
    if kind == "runtime":
        target = writing(layout.runtime / "generated.typ")
    elif kind == "directory":
        target = outside
    symlink(articles / "linked.typ", target)
    with pytest.raises(_paths.LayoutError, match="escapes|generated .demolab"):
        list(layout.source_files())


def test_internal_directory_symlinks_are_not_followed(tmp_path, monkeypatch):
    layout = configured_layout(tmp_path, monkeypatch)
    article = writing(tmp_path / "articles" / "real" / "note.typ")
    symlink(article.parent / "cycle", article.parent)
    symlink(tmp_path / "articles" / "alias", article.parent)
    assert list(layout.source_files()) == [article]


def test_yaml_evaluation_is_cached_by_contents_including_errors(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    (tmp_path / "articles").mkdir()
    calls = []
    def run(*args, **kwargs):
        calls.append(args)
        bad = layout.config.read_text() == "broken"
        return SimpleNamespace(returncode=int(bad), stdout=json.dumps("articles"),
                               stderr="invalid YAML" if bad else "")
    monkeypatch.setattr(_paths.subprocess, "run", run)
    _paths._writings_setting.cache_clear()
    layout.config.write_text("writings: articles\n")
    assert layout.writings == tmp_path / "articles"
    assert layout.writings == tmp_path / "articles"
    assert len(calls) == 1
    layout.config.write_text("broken")
    for _ in range(2):
        with pytest.raises(_paths.LayoutError, match="invalid YAML"):
            _ = layout.writings
    assert len(calls) == 2
    layout.config.write_text("writings: articles # repaired\n")
    assert layout.writings == tmp_path / "articles"
    assert len(calls) == 3
    _paths._writings_setting.cache_clear()


@pytest.mark.skipif(shutil.which("typst") is None, reason="Typst YAML parser is required")
@pytest.mark.parametrize("contents, value", [
    ("name: Default\n", "writings"),
    ("", "writings"),
    ('"writings": "articles/research" # comment\n', "articles/research"),
    ("{writings: 'articles with spaces'}\n", "articles with spaces"),
    ("source: &source articles\nwritings: *source\n", "articles"),
])
def test_real_yaml_parser(tmp_path, contents, value):
    layout = _paths.layout_for(tmp_path)
    (tmp_path / value).mkdir(parents=True)
    layout.config.write_text(contents)
    assert layout.writings == tmp_path / value


@pytest.mark.skipif(shutil.which("typst") is None, reason="Typst YAML parser is required")
def test_malformed_yaml_retains_parser_diagnostic(tmp_path):
    layout = _paths.layout_for(tmp_path)
    layout.config.write_text("writings: [\n")
    with pytest.raises(_paths.LayoutError, match="error:"):
        _ = layout.writings


def test_watcher_changes_source_roots_and_recovers_from_invalid_config(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    first = writing(tmp_path / "first" / "nested" / "one.typ")
    second = writing(tmp_path / "second" / "nested" / "two.typ")
    helper = second.parent / "helper.json"
    helper.write_text("{}")
    monkeypatch.setattr(_paths, "_writings_setting", lambda root, config, contents:
                        (None, "invalid YAML") if contents == "broken" else (contents.strip(), None))
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "WATCH_DIRS", [])
    monkeypatch.setattr(devserver, "WATCH_FILES", [layout.config, layout.landing])
    layout.config.write_text("first")
    first_snapshot = devserver.snapshot()
    assert str(first) in first_snapshot and str(second) not in first_snapshot
    layout.config.write_text("second")
    second_snapshot = devserver.snapshot()
    assert str(second) in second_snapshot and str(first) not in second_snapshot
    assert str(helper) in second_snapshot
    assert devserver.deck_affecting({str(helper)})
    assert devserver.deck_affecting({str(second.parent / "helper.typ")})
    layout.config.write_text("broken")
    assert "<writings-error>" in devserver.snapshot()
    assert str(layout.config) in devserver.snapshot()
    layout.config.write_text("second")
    assert "<writings-error>" not in devserver.snapshot()
    second.unlink()
    assert str(second) not in devserver.snapshot()
    assert str(helper) in devserver.snapshot()


def test_watcher_detects_invalid_symlink_and_recovery(tmp_path, monkeypatch):
    root = tmp_path / "lab"
    root.mkdir()
    layout = _paths.layout_for(root)
    layout.writings.mkdir()
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "WATCH_DIRS", [])
    monkeypatch.setattr(devserver, "WATCH_FILES", [])
    before = devserver.snapshot()
    outside = writing(tmp_path / "outside.typ")
    link = layout.writings / "bad.typ"
    symlink(link, outside)
    assert "<writings-error>" in devserver.snapshot()
    link.unlink()
    assert devserver.snapshot() == before


@pytest.mark.parametrize("edit_during_build", [1, 2])
def test_watcher_does_not_swallow_edits_during_build(monkeypatch, edit_during_build):
    state = {"version": 0, "builds": 0, "sleeps": 0}
    monkeypatch.setattr(devserver, "snapshot", lambda: {"source.typ": state["version"]})
    monkeypatch.setattr(devserver, "deck_affecting", lambda changed: True)
    monkeypatch.setattr(devserver, "broadcast", lambda *args: None)
    def run_build(**kwargs):
        state["builds"] += 1
        if state["builds"] == edit_during_build:
            state["version"] += 1
        if state["builds"] > edit_during_build:
            raise KeyboardInterrupt
        return True, "built"
    def sleep(seconds):
        state["sleeps"] += 1
        if state["sleeps"] == 1 and edit_during_build == 2:
            state["version"] += 1  # trigger the ordinary rebuild before the in-build edit
        if state["sleeps"] > 8:
            raise KeyboardInterrupt  # bounded failure: the final build count catches a lost edit
    monkeypatch.setattr(devserver, "build", run_build)
    monkeypatch.setattr(devserver.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        devserver.watch_loop()
    assert state["builds"] == edit_during_build + 1
