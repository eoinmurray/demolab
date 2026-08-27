"""Unit tests for the dev server's pure logic (no HTTP, no build).

The end-to-end behaviour — hot-add of a new entry, the browser error overlay on a failed
compile — is exercised by hand against `task dev`; these cover the two string transforms the
server leans on, which are easy to break silently, plus the loopback bind (sockets only, no
HTTP request, no build) that an IPv4-only server gets wrong on Windows.
"""
import os
import socket
import threading
from types import SimpleNamespace

from demolab_cli import _paths, devserver


def test_sse_bytes_single_line():
    assert devserver.sse_bytes("reload") == b"data: reload\n\n"


def test_sse_bytes_multiline_frames_each_line():
    # A Typst error is multi-line; EventSource rejoins "data:" lines with "\n", so each source
    # line must get its own "data: " prefix or the browser sees a mangled message.
    out = devserver.sse_bytes("error\nunclosed delimiter\n  at foo.typ:1").decode()
    assert out == "data: error\ndata: unclosed delimiter\ndata:   at foo.typ:1\n\n"


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
    assert devserver.build() == (True, "built")
    assert "--no-pdf-copy" in captured["cmd"]


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
