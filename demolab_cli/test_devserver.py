"""Unit tests for the dev server's pure logic (no HTTP, no build).

The end-to-end behaviour — hot-add of a new entry, the browser error overlay on a failed
compile — is exercised by hand against `task dev`; these cover the two string transforms the
server leans on, which are easy to break silently, plus the loopback bind (sockets only, no
HTTP request, no build) that an IPv4-only server gets wrong on Windows.
"""
import json
import os
import shutil
import socket
import subprocess
import threading
from types import SimpleNamespace

import pytest

from demolab_cli import _paths, devserver


def test_sse_bytes_single_line():
    assert devserver.sse_bytes("reload") == b"data: reload\n\n"


def test_sse_bytes_multiline_frames_each_line():
    # A Typst error is multi-line; EventSource rejoins "data:" lines with "\n", so each source
    # line must get its own "data: " prefix or the browser sees a mangled message.
    out = devserver.sse_bytes("error\nunclosed delimiter\n  at foo.typ:1").decode()
    assert out == "data: error\ndata: unclosed delimiter\ndata:   at foo.typ:1\n\n"


def test_error_event_carries_optional_entry_scope():
    scoped = devserver.error_event("missing figure", "report")
    assert json.loads(scoped.removeprefix("error\n")) == {
        "message": "missing figure", "entry": "report"}
    assert json.loads(devserver.error_event("invalid config").removeprefix("error\n"))["entry"] == ""


def test_error_entry_attributes_compile_and_selection_failures():
    sources = {"report": devserver._build_mod.ROOT / "writings" / "report.typ"}
    diagnostic = "error: broken\nwhile importing `/writings/report.typ`"
    assert devserver.error_entry(diagnostic, sources) == "report"
    data_backed = (
        "error: data-backed build compilation failed:\n"
        "error: missing selected data file\n"
        "while calling `data-file` at writings/run-inputs.typ:74:4\n"
        "while importing `/writings/report.typ` at .demolab/bundle/main.typ:48:2"
    )
    assert devserver.error_entry(data_backed, sources) == "report"
    assert devserver.error_entry("report / results: no available run", sources) == "report"
    assert devserver.error_entry("invalid demolab.yaml", sources) == ""


@pytest.mark.skipif(shutil.which("node") is None, reason="Node required for browser-client test")
def test_reload_client_shows_scoped_error_only_on_matching_route():
    program = """
globalThis.window = {};
globalThis.location = {pathname: '/welcome'};
let appended = 0;
let removed = 0;
let dismiss;
globalThis.document = {
  createElement: (tag) => {
    const element = {style: {}, appendChild: () => {}, setAttribute: () => {},
                     remove: () => { removed += 1; }};
    if (tag === 'button') dismiss = element;
    return element;
  },
  documentElement: {appendChild: () => { appended += 1; }}
};
globalThis.EventSource = function () { globalThis.events = this; };
globalThis.setTimeout = () => {};
""" + devserver.RELOAD_JS + """
events.onmessage({data: SCOPED});
if (appended !== 0) throw new Error('error leaked onto another page');
location.pathname = '/report.html';
events.onmessage({data: SCOPED});
if (appended !== 1) throw new Error('matching page did not show its error');
if (!dismiss || typeof dismiss.onclick !== 'function') throw new Error('error cannot be dismissed');
dismiss.onclick();
if (removed !== 1) throw new Error('dismiss did not remove the error');
events.onmessage({data: 'ok'});
location.pathname = '/welcome';
events.onmessage({data: GLOBAL});
if (appended !== 2) throw new Error('global error was not shown site-wide');
"""
    program = program.replace("SCOPED", json.dumps(devserver.error_event("broken", "report")))
    program = program.replace("GLOBAL", json.dumps(devserver.error_event("bad config")))
    subprocess.run([shutil.which("node"), "-e", program], check=True, capture_output=True, text=True)


def test_preview_build_records_article_scope(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    source = devserver._build_mod.ROOT / "writings" / "report.typ"
    session = SimpleNamespace(runtime=layout.runtime / "preview", lock=threading.RLock(),
                              error_entry="", rebuild=lambda *args: (
                                  False, "error: broken\nwhile importing `/writings/report.typ`"))
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "PREVIEW", session)
    monkeypatch.setattr(devserver.preview, "load_config", lambda _: object())
    monkeypatch.setattr(devserver._build_mod, "discover", lambda: ({"report": source}, {}))
    assert not devserver.build()[0]
    assert session.error_entry == "report"


def test_data_backed_build_without_preview_records_article_scope(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    source = devserver._build_mod.ROOT / "writings" / "report.typ"
    diagnostic = (
        "error: data-backed build compilation failed:\n"
        "error: missing selected data file\n"
        "while importing `/writings/report.typ` at .demolab/bundle/main.typ:48:2"
    )
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "PREVIEW", None)
    monkeypatch.setattr(devserver.preview, "load_config", lambda _: None)
    monkeypatch.setattr(devserver, "_compile", lambda *args: (False, diagnostic))
    monkeypatch.setattr(devserver._build_mod, "discover", lambda: ({"report": source}, {}))
    assert devserver.build() == (False, diagnostic)
    assert devserver._last_build_entry[0] == "report"


def test_global_preview_failure_clears_previous_article_scope(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    session = SimpleNamespace(runtime=layout.runtime / "preview", lock=threading.RLock(),
                              error="", error_entry="report", pending=True)
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "PREVIEW", session)
    monkeypatch.setattr(devserver.preview, "load_config",
                        lambda _: (_ for _ in ()).throw(devserver.preview.PreviewError("bad config")))
    assert devserver.build() == (False, "bad config")
    assert session.error_entry == "" and not session.pending


def test_inject_reload_before_body_close():
    out = devserver.inject_reload("<html><body>hi</body></html>")
    assert "EventSource('/__dev')" in out
    # injected inside the document, immediately before </body>
    assert out.index("<script>") < out.index("</body>")
    assert out.count("</body>") == 1


def test_inject_reload_appends_when_no_body_tag():
    out = devserver.inject_reload("<p>fragment</p>")
    assert out.startswith("<p>fragment</p>")
    assert out.rstrip().endswith("</script>")


def test_benign_disconnects_are_swallowed():
    # Browser disconnects (reset / broken pipe / abort) are harmless and must not be logged as errors.
    for exc in (ConnectionResetError(), BrokenPipeError(), ConnectionAbortedError(), TimeoutError()):
        assert devserver._is_benign_disconnect(exc), exc
    # A real error is not swallowed.
    for exc in (ValueError(), RuntimeError(), KeyError()):
        assert not devserver._is_benign_disconnect(exc), exc


def test_within_blocks_traversal(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "ok.html").write_text("x")
    assert devserver._within(site / "ok.html", site)
    assert devserver._within(site / "sub" / "page.html", site)  # not-yet-existing, still contained
    # `..` that climbs out of the site must be rejected
    assert not devserver._within(site / ".." / "secret.html", site)
    assert not devserver._within(site / ".." / ".." / "etc" / "hosts.html", site)


def test_html_file_for_path_accepts_bare_trailing_slash_and_explicit_urls(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    page = site / "report.v2.html"
    page.write_text("report")
    (site / "index.html").write_text("home")
    section = site / "section"
    section.mkdir()
    section_index = section / "index.html"
    section_index.write_text("section")

    assert devserver.html_file_for_path("/report.v2", site) == page
    assert devserver.html_file_for_path("/report.v2/", site) == page
    assert devserver.html_file_for_path("/report.v2.html", site) == page
    assert devserver.html_file_for_path("/", site) == site / "index.html"
    assert devserver.html_file_for_path("/section/", site) == section_index
    assert devserver.html_file_for_path("/missing", site) == site / "missing"
    assert devserver.html_file_for_path("/missing/", site) == site / "missing" / "index.html"


def test_make_server_accepts_both_loopbacks():
    # The banner says http://localhost, but Windows resolves `localhost` to the IPv6 ::1 first
    # — an IPv4-only bind makes that URL dead there while 127.0.0.1 works. make_server must
    # therefore accept connections on BOTH loopbacks (dual-stack), not just 127.0.0.1.
    server = devserver.make_server(0)  # port 0 → OS assigns a free one
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
        if server.address_family == socket.AF_INET6:  # IPv4-only fallback hosts skip this leg
            with socket.create_connection(("::1", port), timeout=2):
                pass
    finally:
        server.shutdown()
        server.server_close()


def test_deck_affecting_triggers_on_slide_and_data(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    # Decks can import ordinary Typst helpers as well as their own data assets.
    assert devserver.deck_affecting({"/repo/writings/ar004.slide.typ"})
    assert devserver.deck_affecting({str(layout.data / "exp000/lif.svg")})
    assert devserver.deck_affecting({str(layout.assets / "chart.svg")})
    assert devserver.deck_affecting({str(layout.config)})
    assert devserver.deck_affecting({"/repo/writings/exp000.typ"})
    assert devserver.deck_affecting({"/pkg/demolab_cli/typ/lib.typ"})
    assert not devserver.deck_affecting({"/pkg/demolab_cli/typ/style.css"})
    assert not devserver.deck_affecting(set())


def test_dev_build_does_not_copy_preview_pdfs_to_publication_dir(monkeypatch):
    captured = {}

    def run(cmd, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="built\n", stderr="")

    monkeypatch.setattr(devserver.subprocess, "run", run)
    assert devserver._compile() == (True, "built")
    assert "--no-pdf-copy" in captured["cmd"]
    assert "--preview" not in captured["cmd"]


def test_demo_watch_inputs_include_alternatives_but_exclude_runtime(tmp_path, monkeypatch):
    # Parser integration is tested separately; this watcher test also runs without Typst.
    monkeypatch.setattr(_paths, "_writings_setting", lambda *args: ("writings", None))
    layout = _paths.LabLayout(tmp_path, tmp_path / ".demo", demo=True)
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "WATCH_DIRS", [])
    monkeypatch.setattr(devserver, "WATCH_FILES", [layout.config, layout.landing])
    paths = [layout.writings / "benchmark-a.typ", layout.data / "benchmark-a-run-001/numbers.json",
             layout.data / "benchmark-a-run-002/numbers.json",
             layout.assets / "example.txt", layout.config, layout.landing]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("initial")
    initial = devserver.snapshot()
    assert set(initial) == {str(path) for path in paths}
    generated = layout.runtime / "site" / "benchmark-a.html"
    generated.parent.mkdir(parents=True)
    generated.write_text("generated")
    assert devserver.snapshot() == initial
    alternative = paths[2]
    alternative.write_text("updated alternative")
    os.utime(alternative, ns=(initial[str(alternative)] + 1_000_000_000,) * 2)
    assert devserver.snapshot()[str(alternative)] != initial[str(alternative)]
    assert devserver.deck_affecting({str(alternative)})
    added = layout.writings / "new.typ"
    added.write_text("new article")
    assert str(added) in devserver.snapshot()
    added.unlink()
    assert str(added) not in devserver.snapshot()


def test_project_dependencies_outside_writings_trigger_snapshot(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    monkeypatch.setattr(devserver, "LAYOUT", layout)
    monkeypatch.setattr(devserver, "WATCH_DIRS", [])
    monkeypatch.setattr(devserver, "WATCH_FILES", [layout.config, layout.landing])
    layout.config.write_text("name: Test\n")
    helper = tmp_path / "experiments" / "graph.py"
    helper.parent.mkdir()
    helper.write_text("VERSION = 1\n")
    before = devserver.snapshot()
    assert str(helper) in before
    helper.write_text("VERSION = 2\n")
    os.utime(helper, ns=(before[str(helper)] + 1_000_000_000,) * 2)
    assert devserver.snapshot()[str(helper)] != before[str(helper)]


def test_project_watch_excludes_generated_and_cache_trees(tmp_path):
    layout = _paths.layout_for(tmp_path)
    included = [tmp_path / ".artifacts" / "exp" / "figure.svg",
                tmp_path / ".pingstore" / "runs" / "exp001-r001-present" / "run.json",
                tmp_path / "writings" / "helper.typ"]
    excluded = [tmp_path / ".demolab" / "site" / "page.html",
                tmp_path / ".git" / "index", tmp_path / ".venv" / "module.py",
                tmp_path / "experiments" / "__pycache__" / "graph.pyc",
                tmp_path / ".pingstore" / "runs" / ".exp001-r002.tmp" / "run.json",
                tmp_path / "output" / "generated.json"]
    for path in included + excluded:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    watched = set(devserver.project_watch_files(layout))
    assert set(included) <= watched
    assert not set(excluded) & watched
