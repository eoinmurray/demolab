"""Unit tests for the dev server's pure logic (no HTTP, no build).

The end-to-end behaviour — hot-add of a new entry, the browser error overlay on a failed
compile — is exercised by hand against `task dev`; these cover the two string transforms the
server leans on, which are easy to break silently.
"""
import devserver


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


def test_deck_affecting_triggers_on_slide_and_data():
    # A deck PDF depends only on its own source and the data assets it embeds.
    assert devserver.deck_affecting({"/repo/writings/ar004.slide.typ"})
    assert devserver.deck_affecting({"/repo/artifacts/data/exp000/lif.svg"})
    # A prose / CSS / lib edit can't change a deck, so decks are skipped.
    assert not devserver.deck_affecting({"/repo/writings/exp000.typ"})
    assert not devserver.deck_affecting({"/repo/demolab-engine/build/lib.typ"})
    assert not devserver.deck_affecting(set())
