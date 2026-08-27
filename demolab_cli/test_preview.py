"""Storage-neutral discovery, isolated article selections, and real preview builds."""
import base64
import dataclasses
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import threading

import pytest

from demolab_cli import _paths, devserver, preview


@pytest.mark.skipif(shutil.which("node") is None, reason="Node required for pure JavaScript unit test")
@pytest.mark.parametrize("choice", ["latest", "run:new", "run:old", "run:missing"])
def test_selector_lists_each_run_once_including_pinned_latest(choice):
    # Execute only the pure options helper, not the browser client or a browser runtime.
    helper = (_paths.TYP / "preview.js").read_text(encoding="utf-8").split("\n(() => {", 1)[0]
    program = helper + '\nconsole.log(JSON.stringify(demolabPreviewOptions([{id:"new"},{id:"old"}], ' + json.dumps(choice) + ')));'
    result = subprocess.run([shutil.which("node"), "-e", program], capture_output=True, encoding="utf-8", check=True)
    data = json.loads(result.stdout)
    assert data["options"][:2] == [["latest", "Latest — new"], ["run:old", "old"]]
    assert len(data["options"]) == (3 if choice == "run:missing" else 2)
    assert data["value"] == ("latest" if choice in ("latest", "run:new") else choice)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node required for pure JavaScript unit test")
def test_empty_selector_is_explicit_and_disabled():
    helper = (_paths.TYP / "preview.js").read_text(encoding="utf-8").split("\n(() => {", 1)[0]
    result = subprocess.run([shutil.which("node"), "-e", helper +
        '\nconsole.log(JSON.stringify(demolabPreviewOptions([], "latest")));'],
        capture_output=True, encoding="utf-8", check=True)
    assert json.loads(result.stdout) == {
        "options": [["latest", "No runs available"]], "value": "latest", "disabled": True}


@pytest.fixture
def lab(tmp_path):
    layout = _paths.layout_for(tmp_path)
    source = tmp_path / "runs"
    source.mkdir()
    (source / "first").mkdir()
    (source / "second").mkdir()
    return layout, preview.Config(source, (sys.executable, "discover.py"), {})


def records():
    return [dict(id="old", experiment="exp", created_at="2026-08-25T10:00:00Z", presentation="first"),
            dict(id="new", experiment="exp", label="New run", created_at="2026-08-26T10:00:00Z", presentation="second")]


def supply(monkeypatch, data):
    monkeypatch.setattr(preview, "bounded_command", lambda *a, **k: json.dumps(data))


def symlink(link, target):
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this host")


def test_normalized_inputs():
    assert preview.normalize_inputs(["exp"]) == [{"key": "exp", "experiment": "exp", "group": ""}]
    assert preview.normalize_inputs({"legacy": ["exp"], "current": ["exp"]}) == [
        {"key": "legacy.exp", "experiment": "exp", "group": "legacy"},
        {"key": "current.exp", "experiment": "exp", "group": "current"}]
    assert preview.normalize_inputs([]) == []


@pytest.mark.parametrize("value", ["exp", ["a", "a"], {"": ["a"]}, {"a": "exp"},
                                       {"a": ["b.c"], "a.b": ["c"]}, ["../a"], [None], {1: ["a"]}])
def test_invalid_inputs(value):
    with pytest.raises(preview.PreviewError):
        preview.normalize_inputs(value)


def test_command_is_verbatim_array_with_cwd_and_source_env(lab):
    layout, config = lab
    script = layout.root / "discover.py"
    script.write_text('import json, os, sys\nprint(json.dumps([os.getcwd(), os.environ["DEMOLAB_PREVIEW_SOURCE"], sys.argv[1:]]))\n')
    command = (*config.command, "spaces ; $(not-a-shell)")
    result = preview.bounded_command(command, cwd=layout.content,
                                    env={**os.environ, "DEMOLAB_PREVIEW_SOURCE": str(config.source)})
    assert json.loads(result) == [str(layout.content), str(config.source), ["spaces ; $(not-a-shell)"]]


@pytest.mark.parametrize(("program", "kwargs", "error"), [
    ('import sys; print("failed", file=sys.stderr); sys.exit(2)', {}, "exited 2.*failed"),
    ('print("x" * 50000)', {"limit": 100}, "exceeds 100"),
    ('import time; time.sleep(10)', {"timeout": 0.05}, "timed out"),
])
def test_bounded_command_errors(tmp_path, program, kwargs, error):
    with pytest.raises(preview.PreviewError, match="(?s)" + error):
        preview.bounded_command((sys.executable, "-c", program), cwd=tmp_path, env=os.environ, **kwargs)


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")
def test_yaml_optional_and_strict(lab):
    layout, config = lab
    assert preview.load_config(layout) is None
    layout.config.write_text("name: ordinary\n")
    assert preview.load_config(layout) is None
    layout.config.write_text("preview:\n  source: runs\n  discover: [python, discover.py]\n  articles:\n    exp: []\n")
    assert preview.load_config(layout) == dataclasses.replace(config, command=("python", "discover.py"), articles={"exp": []})
    layout.config.write_text("preview:\n  source: runs\n  discover: python discover.py\n")
    with pytest.raises(preview.PreviewError, match="array"):
        preview.load_config(layout)
    layout.config.write_text("preview:\n  source: ../outside\n  discover: [python]\n")
    with pytest.raises(preview.PreviewError, match="inside the lab"):
        preview.load_config(layout)


def test_catalogue_order_uses_normalized_timestamps_and_stable_ids(lab, monkeypatch):
    layout, config = lab
    data = records()
    data[0]["created_at"] = "2026-08-26T13:00:00+02:00"
    supply(monkeypatch, data)
    assert [r["id"] for r in preview.discover(config, layout)] == ["old", "new"]
    data[0]["created_at"] = "2026-08-26T10:00:00Z"
    assert [r["id"] for r in preview.discover(config, layout)] == ["old", "new"]


@pytest.mark.parametrize(("field", "value", "error"), [
    ("id", "../run", "run ID"), ("experiment", None, "experiment"),
    ("created_at", "2026-08-25T10:00:00", "timezone"), ("created_at", "invalid", "timestamp"),
    ("presentation", "../runs/first", "relative"), ("presentation", "/tmp", "relative"),
    ("presentation", "C:\\first", "relative"), ("presentation", "absent", "does not exist"),
])
def test_invalid_catalogue(lab, monkeypatch, field, value, error):
    layout, config = lab
    data = records()
    data[0][field] = value
    supply(monkeypatch, data)
    with pytest.raises(preview.PreviewError, match=error):
        preview.discover(config, layout)


def test_duplicate_ids_and_symlinks_rejected(lab, monkeypatch):
    layout, config = lab
    supply(monkeypatch, records() * 2)
    with pytest.raises(preview.PreviewError, match="duplicate"):
        preview.discover(config, layout)
    symlink(config.source / "link", config.source / "first")
    data = records()
    data[0]["presentation"] = "link"
    supply(monkeypatch, data)
    with pytest.raises(preview.PreviewError, match="symlink"):
        preview.discover(config, layout)
    symlink(config.source / "first" / "link", config.source / "second")
    with pytest.raises(preview.PreviewError, match="symlink"):
        preview.validate_directory(config.source / "first", layout)


def test_selection_state_is_article_scoped_transactional_and_recoverable(lab, monkeypatch):
    layout, config = lab
    config = dataclasses.replace(config, articles={"gallery": ["exp"], "disabled": []})
    supply(monkeypatch, records())
    session = preview.Session(layout)
    ids = ["exp", "gallery", "disabled", "unrelated"]
    compile_ok = lambda: (True, "built")
    assert session.rebuild(config, ids, compile_ok)[0]
    assert session.rendered == {"gallery": {"exp": "new"}, "disabled": {}, "exp": {"exp": "new"}}
    session.request(dict(action="select", article="gallery", key="exp", choice="run:old"))
    assert session.rebuild(config, ids, compile_ok)[0]
    assert session.rendered["exp"]["exp"] == "new"
    assert session.rendered["gallery"]["exp"] == "old"
    assert preview.Session(layout).desired == {"gallery": {"exp": "run:old"}}
    saved = (session.runtime / "state.json").read_bytes()
    session.request(dict(action="select", article="gallery", key="exp", choice="published"))
    assert not session.rebuild(config, ids, lambda: (False, "missing figure"))[0]
    assert session.error == "missing figure"
    assert session.rendered["gallery"]["exp"] == "old"
    assert (session.runtime / "state.json").read_bytes() == saved
    assert session.rebuild(config, ids, compile_ok)[0]
    assert json.loads((session.runtime / "input.json").read_text())["gallery"] == {}
    assert session.rendered["gallery"]["exp"] == "Published/default"
    session.request({"action": "reset"})
    assert session.rebuild(config, ids, compile_ok)[0]
    assert session.desired == {}


def test_failed_discovery_retains_automatic_controls_and_missing_run_is_not_replaced(lab, monkeypatch):
    layout, config = lab
    supply(monkeypatch, records())
    session = preview.Session(layout)
    assert session.rebuild(config, ["exp"], lambda: (True, "built"))[0]
    monkeypatch.setattr(preview, "bounded_command", lambda *a, **k: "invalid JSON")
    assert not session.rebuild(config, ["exp"], lambda: pytest.fail("must not compile"))[0]
    assert session.stale and session.inputs["exp"] and len(session.catalogue) == 2
    session.request(dict(action="select", article="exp", key="exp", choice="run:old"))
    supply(monkeypatch, records()[1:])
    assert not session.rebuild(config, ["exp"], lambda: pytest.fail("must not compile"))[0]
    assert "no available run" in session.error
    supply(monkeypatch, [])
    assert not session.rebuild(config, ["exp"], lambda: pytest.fail("must not silently disable"))[0]
    assert session.inputs["exp"]


def test_no_runs_compile_with_explicit_absence_and_recover(lab, monkeypatch):
    layout, config = lab
    config = dataclasses.replace(config, articles={"gallery": ["exp", "other"]})
    session = preview.Session(layout)
    supply(monkeypatch, [])

    def compile_empty():
        assert json.loads((session.runtime / "input.json").read_text()) == {
            "gallery": {"exp": None, "other": None}}
        return True, "empty article built"

    assert session.rebuild(config, ["exp", "gallery"], compile_empty)[0]
    assert not session.error and not session.stale
    assert session.rendered == {"gallery": {"exp": None, "other": None}}
    assert "exp" not in session.inputs  # no inferred attachment before the first run
    supply(monkeypatch, records())
    assert session.rebuild(config, ["exp", "gallery"], lambda: (True, "built"))[0]
    assert session.rendered == {"gallery": {"exp": "new", "other": None}, "exp": {"exp": "new"}}
    # Previously matched automatic inputs stay visible when their runs disappear.
    supply(monkeypatch, [])
    assert session.rebuild(config, ["exp", "gallery"], lambda: (True, "built"))[0]
    assert session.rendered["exp"] == {"exp": None}
    assert session.inputs["exp"]


def test_pending_choice_during_compile_is_not_lost(lab, monkeypatch):
    layout, config = lab
    supply(monkeypatch, records())
    session = preview.Session(layout)

    def during_compile():
        session.request(dict(action="select", article="exp", key="exp", choice="run:old"))
        return True, "built"

    assert session.rebuild(config, ["exp"], during_compile)[0]
    assert session.pending
    assert session.rendered["exp"]["exp"] == "new"
    assert session.desired["exp"]["exp"] == "run:old"
    assert session.rebuild(config, ["exp"], lambda: (True, "built"))[0]
    assert not session.pending
    assert session.rendered["exp"]["exp"] == "old"


def test_article_fragment_is_atomic_and_reset_is_article_scoped(lab, monkeypatch):
    layout, config = lab
    supply(monkeypatch, records())
    config = dataclasses.replace(config, articles={"comparison": {"before": ["exp"], "after": ["exp"]}})
    session = preview.Session(layout)
    assert session.rebuild(config, ["exp", "comparison"], lambda: (True, "built"))[0]
    session.request(dict(action="select", article="exp", key="exp", choice="run:old"))
    session.request(dict(action="article", article="comparison", selections={
        "before.exp": "run:old", "after.exp": "run:new"}))
    assert session.desired["comparison"] == {"before.exp": "run:old", "after.exp": "run:new"}
    before = session.status()["selections"]
    with pytest.raises(preview.PreviewError, match="unavailable"):
        session.request(dict(action="article", article="comparison", selections={
            "before.exp": "latest", "after.exp": "run:missing"}))
    assert session.desired == before
    session.request(dict(action="article", article="comparison", selections={}, reset=True))
    assert session.desired == {"exp": {"exp": "run:old"}, "comparison": {}}
    assert session.rebuild(config, ["exp", "comparison"], lambda: (True, "built"))[0]
    assert session.rendered["comparison"] == {"before.exp": "new", "after.exp": "new"}
    assert session.rendered["exp"]["exp"] == "old"


@pytest.mark.parametrize("selections", [[], None, {"unknown": "latest"}, {"exp": []}, {"exp": "published"}])
def test_article_fragment_validation(lab, selections):
    layout, _ = lab
    session = preview.Session(layout)
    session.inputs = {"exp": preview.normalize_inputs(["exp"])}
    with pytest.raises(preview.PreviewError):
        session.request(dict(action="article", article="exp", selections=selections))
    assert session.desired == {} and not session.pending


def test_corrupt_state_requires_explicit_reset(lab, monkeypatch):
    layout, config = lab
    preview.atomic_json(layout.runtime / "preview/state.json", ["bad state"])
    session = preview.Session(layout)
    supply(monkeypatch, records())
    assert not session.rebuild(config, ["exp"], lambda: pytest.fail("must not compile"))[0]
    assert "cannot read preview state" in session.error
    session.request({"action": "reset"})
    assert session.rebuild(config, ["exp"], lambda: (True, "built"))[0]


def test_source_watch_includes_new_metadata_and_symlinks_without_following_them(lab):
    layout, config = lab
    session = preview.Session(layout)
    session.config = config
    initial = session.watch()
    metadata = config.source / ".metadata"
    metadata.mkdir()
    (metadata / "index.json").write_text("[]")
    link = config.source / "first" / "link"
    symlink(link, layout.runtime)
    (layout.runtime / "generated").mkdir(parents=True)
    signature = session.watch()
    assert signature != initial
    assert str(metadata / "index.json") in signature and str(link) in signature
    assert not any("generated" in path for path in signature)


def test_switching_explicit_article_back_to_automatic_does_not_keep_old_dependency(lab, monkeypatch):
    layout, config = lab
    supply(monkeypatch, records())
    session = preview.Session(layout)
    explicit = dataclasses.replace(config, articles={"gallery": ["exp"]})
    assert session.rebuild(explicit, ["gallery"], lambda: (True, "built"))[0]
    assert session.rebuild(config, ["gallery"], lambda: (True, "built"))[0]
    assert session.inputs == {}


def test_disappeared_saved_run_is_an_error_after_restart(lab, monkeypatch):
    layout, config = lab
    preview.atomic_json(layout.runtime / "preview/state.json",
                        {"version": 1, "selections": {"exp": {"exp": "run:old"}}})
    supply(monkeypatch, [])
    session = preview.Session(layout)
    assert not session.rebuild(config, ["exp"], lambda: pytest.fail("must not compile"))[0]
    assert session.inputs["exp"] and "no available run" in session.error


def test_dev_without_preview_uses_ordinary_worker(lab, monkeypatch):
    layout, _ = lab
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "PREVIEW", None)
    monkeypatch.setattr(devserver, "SITE", layout.runtime / "site")
    monkeypatch.setattr(preview, "load_config", lambda _: None)
    monkeypatch.setattr(preview, "discover", lambda *a: pytest.fail("must not discover"))
    calls = []
    monkeypatch.setattr(devserver, "_compile", lambda skip: calls.append(skip) or (True, "built"))
    assert devserver.build(skip_decks=True) == (True, "built")
    assert calls == [True] and devserver.PREVIEW is None
    assert not (layout.runtime / "preview").exists()


def test_http_preview_api_and_first_build_error_shell(lab, monkeypatch):
    layout, _ = lab
    session = preview.Session(layout)
    session.inputs = {"exp": preview.normalize_inputs(["exp"])}
    monkeypatch.setattr(devserver, "PREVIEW", session)
    monkeypatch.setattr(devserver, "SITE", session.runtime / "site")
    server = devserver.make_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port

    def request(method, path, body=None, **headers):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, response.read().decode()
        finally:
            connection.close()

    try:
        assert request("GET", "/__preview")[0] == 200
        assert request("GET", "/__preview", Host=f"evil.test:{port}")[0] == 403
        status, html = request("GET", "/exp")
        assert status == 200 and '/__preview.js' in html and "EventSource" in html
        headers = {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json", "X-Demolab-Token": session.token}
        assert request("POST", "/__preview", '{"action":"refresh"}')[0] == 403
        assert request("POST", "/__preview", '{"action":"refresh"}', **headers)[0] == 202
        assert session.pending
        assert request("POST", "/__preview", '{"action":"select","article":[],"key":"exp","choice":"latest"}', **headers)[0] == 400
        assert request("POST", "/__preview", '{"action":"select","article":"exp","key":"exp","choice":"/etc/passwd"}', **headers)[0] == 400
        assert request("POST", "/__preview", '{"action":"refresh"}', **{**headers, "Origin": "http://evil.test"})[0] == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")
def test_empty_and_partial_demo_preview_renders_and_recovers(tmp_path):
    from demolab_cli.test_engine_build import _assemble_demo, _build, _pdf_text
    root = tmp_path / "lab"
    _assemble_demo(root)
    layout = _paths.layout_for(root)
    single = layout.content / "writings/benchmark-a.typ"
    single.write_text(single.read_text() + '\n#let body = [#body #if result == none {\n'
                      '  video(data-file("benchmark-a/demo.mp4"), caption: [Pending demonstration])\n'
                      '}]\n')
    config = preview.load_config(layout)
    real_config = dataclasses.replace(config, command=(sys.executable, *config.command[1:]))
    empty_config = dataclasses.replace(config, command=(sys.executable, "-c", "print('[]')"))
    session = preview.Session(layout)
    ids = ["benchmark-a", "benchmark-gallery", "benchmark-comparison", "benchmark-empty"]
    authored = {p: p.read_bytes() for p in layout.content.rglob("*") if p.is_file()}

    def compile_preview():
        result = subprocess.run([sys.executable, "-m", "demolab_cli.build", "--preview", "--no-pdf-copy"],
                                env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr

    def rebuild(config):
        ok, message = session.rebuild(config, ids, compile_preview)
        assert ok, message
        assert not session.error and not session.stale

    def page(name):
        return (session.runtime / "site" / (name + ".html")).read_text()

    # Successful first build, not a stale-site/error-shell fallback. Authored defaults
    # are present but must not leak into the empty preview.
    rebuild(empty_config)
    for name, count in [("benchmark-a", 2), ("benchmark-gallery", 2), ("benchmark-comparison", 4)]:
        html = page(name)
        assert 'class="entry-meta"' in html and "Synthetic demo data" in html
        assert html.count('class="fig-pending"') == count
        assert "Awaiting a run." in html and "<img " not in html
        assert "64% accuracy" not in html and "88% accuracy" not in html
        assert "Awaiting a run." in _pdf_text(session.runtime / "site/pdfs" / (name + ".pdf"))
    assert "Video pending" in page("benchmark-a") and "<video" not in page("benchmark-a")
    assert "Pending demonstration" in page("benchmark-a")
    assert page("benchmark-comparison").count("Comparison pending") == 2
    assert "percentage points" not in page("benchmark-comparison")

    # Independently empty inputs don't hide working inputs in a gallery/comparison.
    catalogue = preview.discover(real_config, layout)
    only_b = [{**run, "presentation": (layout.root / run["presentation"].lstrip("/")).relative_to(config.source).as_posix()}
              for run in catalogue if run["experiment"] == "benchmark-b"]
    partial_config = dataclasses.replace(config, command=(sys.executable, "-c", "print(" + repr(json.dumps(only_b)) + ")"))
    rebuild(partial_config)
    assert "92% accuracy" in page("benchmark-gallery")
    assert page("benchmark-gallery").count('class="fig-pending"') == 1
    assert page("benchmark-comparison").count("Comparison pending") == 1
    assert page("benchmark-comparison").count("0 percentage points") == 1

    # Normal builds ignore the null preview map and still use publication inputs.
    _build(root)
    ordinary_page = (layout.runtime / "site/benchmark-a.html").read_text()
    assert "64% accuracy" in ordinary_page and 'class="fig-pending"' not in ordinary_page
    rebuild(real_config)
    assert "88% accuracy" in page("benchmark-a")
    assert 'class="fig-pending"' not in page("benchmark-a")
    assert "Awaiting a run." not in page("benchmark-gallery")
    assert page("benchmark-comparison").count("0 percentage points") == 2
    assert authored == {p: p.read_bytes() for p in authored}


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")
def test_real_demo_preview_prose_figures_pdfs_and_production_isolation(tmp_path):
    from demolab_cli.test_engine_build import _assemble_demo, _build, _pdf_text
    root = tmp_path / "lab"
    _assemble_demo(root)
    layout = _paths.layout_for(root)
    authored = {p: p.read_bytes() for p in layout.content.rglob("*") if p.is_file()}
    _build(root)
    ordinary = {p: p.read_bytes() for p in (layout.runtime / "site").rglob("*") if p.is_file()}
    config = preview.load_config(layout)
    config = dataclasses.replace(config, command=(sys.executable, *config.command[1:]))
    session = preview.Session(layout)
    ids = ["benchmark-a", "benchmark-gallery", "benchmark-comparison", "benchmark-empty", "welcome", "api"]

    def compile_preview():
        result = subprocess.run([sys.executable, "-m", "demolab_cli.build", "--preview", "--no-pdf-copy"],
                                env={**os.environ, "DEMOLAB_ROOT": str(root)}, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr

    def rebuild():
        ok, message = session.rebuild(config, ids, compile_preview)
        assert ok, message

    def page(name):
        return (session.runtime / "site" / (name + ".html")).read_text()

    rebuild()
    assert session.rendered["benchmark-empty"] == {"benchmark-empty": None}
    assert not any(run["experiment"] == "benchmark-empty" for run in session.catalogue)
    assert page("benchmark-empty").count('class="fig-pending"') == 2
    assert "Awaiting a run." in page("benchmark-empty")
    assert "Image pending" in page("benchmark-empty") and "Video pending" in page("benchmark-empty")
    assert "88% accuracy" in page("benchmark-a")
    assert "88% accuracy" in page("benchmark-gallery") and "92% accuracy" in page("benchmark-gallery")
    assert page("benchmark-comparison").count("0 percentage points") == 2
    assert "88% accuracy" in _pdf_text(session.runtime / "site/pdfs/benchmark-a.pdf")
    unchanged = {name: page(name) for name in ("benchmark-a", "benchmark-gallery")}
    session.request(dict(action="select", article="benchmark-comparison", key="baseline.benchmark-a", choice="run:benchmark-a-run-001"))
    rebuild()
    assert "24 percentage points" in page("benchmark-comparison")
    figures = re.findall(r'<img src="data:image/svg\+xml;base64,([^"]+)"', page("benchmark-comparison"))
    assert [base64.b64decode(f) for f in figures] == [
        (layout.data / run / "accuracy.svg").read_bytes()
        for run in ("benchmark-a-run-001", "benchmark-a-run-002", "benchmark-b-run-002", "benchmark-b-run-002")]
    assert "24 percentage points" in _pdf_text(session.runtime / "site/pdfs/benchmark-comparison.pdf")
    assert unchanged == {name: page(name) for name in unchanged}
    assert ordinary == {p: p.read_bytes() for p in ordinary}
    assert authored == {p: p.read_bytes() for p in authored}

    saved = (session.runtime / "state.json").read_bytes()
    good_page = page("benchmark-comparison")
    figure = layout.data / "benchmark-a-run-001/accuracy.svg"
    figure.unlink()
    ok, error = session.rebuild(config, ids, compile_preview)
    assert not ok and "preview compilation failed" in error and "accuracy.svg" in error
    assert page("benchmark-comparison") == good_page
    assert (session.runtime / "state.json").read_bytes() == saved
    figure.write_bytes(authored[figure])
    session.request(dict(action="select", article="benchmark-a", key="benchmark-a", choice="published"))
    rebuild()
    assert "64% accuracy" in page("benchmark-a")
    assert "88% accuracy" in page("benchmark-gallery")
    # Production discovers independently of local choices and rejects invalid discovery config.
    layout.config.write_text(layout.config.read_text().replace("discover: [python, scripts/discover_runs.py]", "discover: invalid"))
    from demolab_cli.test_engine_build import _build_result
    result = _build_result(root)
    assert result.returncode != 0 and "build discovery failed" in result.stderr
    assert ordinary == {p: p.read_bytes() for p in ordinary}
    assert "__preview" not in page("benchmark-a")  # controls are HTTP-injected, never published
