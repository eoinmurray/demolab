"""Unit tests for build.py's resilience helpers — the pure parsing bits behind stubbing a broken
entry instead of failing the whole site (no compile, no typst)."""
from demolab_cli import build


def test_entry_from_error_parses_the_failing_id():
    err = (
        "error: file not found (searched at /x/.artifacts/exp044/dt_sweep.svg)\n"
        "  ┌─ writings/exp044.typ:50:10\n"
        "while importing `/writings/exp044.typ` at .demolab/bundle/main.typ:32:2"
    )
    sources = {i: build.ROOT / "writings" / f"{i}.typ" for i in ("exp044", "exp000")}
    assert build._entry_from_error(err, sources) == "exp044"
    # only entries we can still drop are candidates
    assert build._entry_from_error(err, {"exp000": sources["exp000"]}) is None
    # an error not attributable to an entry
    assert build._entry_from_error("error: something broke in main.typ", sources) is None


def test_entry_from_error_uses_nested_source_paths():
    sources = {"note": build.ROOT / "articles" / "nested folder" / "note.typ"}
    assert build._entry_from_error(
        "error: missing helper\nwhile importing `/articles/nested folder/note.typ` at main.typ:47:2",
        sources,
    ) == "note"
    assert build._entry_from_error("articles/nested folder/prefix-note.typ:1:1", sources) is None
    assert build._entry_from_error("other/articles/nested folder/note.typ:1:1", sources) is None


def test_error_excerpt_grabs_the_error_block():
    out = (
        "downloading @preview/cmarker\n"
        "warning: bundle export is experimental\n"
        "error: file not found (searched at /x/y.svg)\n"
        "  context line\n"
    )
    excerpt = build._error_excerpt(out)
    assert excerpt.startswith("error: file not found"), excerpt
    assert "context line" in excerpt
    assert "downloading" not in excerpt  # trimmed to the error block
