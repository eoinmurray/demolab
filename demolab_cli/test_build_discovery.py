"""Ordinary builds resolve discovery once, without preview controls or state."""
import json
import os
import shutil
import sys

import pytest

from demolab_cli import _paths, data_sources, preview
from demolab_cli.test_engine_build import _assemble, _build_result, _pdf_text

TYPST_REQUIRED = pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")


@pytest.fixture
def discovered_lab(tmp_path):
    _assemble(tmp_path, demo=False)
    layout = _paths.layout_for(tmp_path)
    for name, value in [("old", 11), ("new", 22), ("compute", 33), ("analyse", 44)]:
        directory = tmp_path / "runs" / name / "export"
        directory.mkdir(parents=True)
        (directory / "numbers.json").write_text(json.dumps({"value": value}))
        (directory / "chart.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><text x="0" y="30">{value}</text></svg>')
        (directory / "movie.mp4").write_bytes(f"video from {name}".encode())
    # This synthetic adapter, not Demolab, owns the storage-specific stage checks.
    # Run names and file times deliberately disagree with the authoritative timestamps.
    records = [
        dict(id="exp022-r999-present", experiment="exp022", stage="present",
             created_at="2026-08-25T10:00:00Z", presentation="old/export"),
        dict(id="exp022-r001-present", experiment="exp022", stage="present",
             created_at="2026-08-26T12:00:00+02:00", presentation="new/export"),
        *[dict(id=f"exp022-r1000-{stage}", experiment="exp022", stage=stage,
               created_at="2026-08-27T10:00:00Z", presentation=f"{stage}/export")
          for stage in ("compute", "analyse")],
    ]
    (tmp_path / "catalogue.json").write_text(json.dumps(records))
    os.utime(tmp_path / "runs/old/export", (2_000_000_000, 2_000_000_000))
    (tmp_path / "discover.py").write_text(
        'import json\nfrom pathlib import Path\n'
        'counter = Path(".demolab/discovery-calls")\n'
        'counter.parent.mkdir(exist_ok=True)\n'
        'counter.write_text(str(int(counter.read_text()) + 1 if counter.exists() else 1))\n'
        'records = json.loads(Path("catalogue.json").read_text())\n'
        'print(json.dumps([r for r in records if r["stage"] == "present"]))\n')
    config = {"name": "Latest inputs", "preview": {
        "source": "runs", "discover": [sys.executable, "discover.py"],
        "articles": {"exp022": ["exp022"], "gallery": ["exp022", "absent"],
                     "compare": {"before": ["exp022"], "after": ["exp022"]},
                     "disabled": []}}}
    layout.config.write_text(json.dumps(config))
    for article, keys in [("exp022", ["exp022"]), ("gallery", ["exp022", "absent"]),
                          ("compare", ["before.exp022", "after.exp022"])]:
        (layout.writings / f"{article}.typ").write_text(
            '#import "/.demolab/lib.typ": *\n'
            f'#let meta = (title: "{article}", created_at: "2026-08-27")\n'
            f'#let data-file = data-file.with(article: "{article}")\n'
            '#let body = [\n'
            '  #for key in (' + ', '.join(json.dumps(key) for key in keys) + ',) {\n'
            '    let r = data-json(data-file(key + "/numbers.json"))\n'
            '    if r == none [A required run is unavailable.] else [Result: #r.value.]\n'
            '    figure(data-image(data-file(key + "/chart.svg")), caption: [Result])\n'
            '    video(data-file(key + "/movie.mp4"), caption: [Recorded run])\n'
            '  }\n]\n')
    (layout.writings / "disabled.typ").write_text(
        '#import "/.demolab/lib.typ": *\n'
        '#let meta = (title: "Disabled", created_at: "2026-08-27")\n'
        '#let data-file = data-file.with(article: "disabled")\n'
        '#let body = [Authored: #json(data-file("legacy/numbers.json")).value.]\n')
    (layout.data / "legacy").mkdir(parents=True)
    (layout.data / "legacy/numbers.json").write_text('{"value": 99}')
    return layout, config


def snapshot(layout):
    return {p.relative_to(layout.runtime): p.read_bytes()
            for base in (layout.runtime / "site", layout.runtime / "pdfs")
            for p in base.rglob("*") if p.is_file()}


def build_ok(layout):
    result = _build_result(layout.root)
    assert result.returncode == 0, result.stdout + result.stderr


@TYPST_REQUIRED
def test_latest_static_build_and_next_build_refresh(discovered_lab):
    layout, _ = discovered_lab
    # Even corrupt saved preview state must not be opened, rewritten, or activated.
    runtime = layout.runtime / "preview"
    runtime.mkdir(parents=True)
    (runtime / "state.json").write_text("invalid preview state")
    (runtime / "input.json").write_text("invalid preview input")
    preview_before = {p: p.read_bytes() for p in runtime.iterdir()}
    authored = {p: p.read_bytes() for p in layout.root.rglob("*")
                if p.is_file() and not p.is_relative_to(layout.runtime)}
    build_ok(layout)
    assert (layout.runtime / "discovery-calls").read_text() == "1"
    frozen = json.loads((layout.runtime / "bundle/data-inputs.json").read_text())
    assert frozen["sources"] == {
        "exp022": {"exp022": "/runs/new/export"},
        "gallery": {"exp022": "/runs/new/export", "absent": None},
        "compare": {"before.exp022": "/runs/new/export", "after.exp022": "/runs/new/export"}}
    assert frozen["files"] == sorted('/runs/new/export/' + name for name in ("chart.svg", "movie.mp4", "numbers.json"))
    site = layout.runtime / "site"
    page = (site / "exp022.html").read_text()
    assert "Result: 22." in page and "Result: 11." not in page
    assert "Authored: 99." in (site / "disabled.html").read_text()
    assert "A required run is unavailable." in (site / "gallery.html").read_text()
    assert "Result: 22." in _pdf_text(site / "pdfs/exp022.pdf")
    assert "Result: 22." in _pdf_text(site / "pdfs/book.pdf")
    for html in site.glob("*.html"):
        text = html.read_text()
        assert "__preview" not in text and "EventSource" not in text and "<select" not in text
    assert [p.read_bytes() for p in (site / "_demolab-data").iterdir()] == [b"video from new"]
    assert authored == {p: p.read_bytes() for p in authored}
    assert preview_before == {p: p.read_bytes() for p in preview_before}
    records = json.loads((layout.root / "catalogue.json").read_text())
    records[0]["created_at"] = "2026-08-28T10:00:00Z"
    (layout.root / "catalogue.json").write_text(json.dumps(records))
    # The last build remains fixed until the next explicit build.
    assert "Result: 22." in (site / "exp022.html").read_text()
    build_ok(layout)
    assert (layout.runtime / "discovery-calls").read_text() == "2"
    assert "Result: 11." in (site / "exp022.html").read_text()


@TYPST_REQUIRED
def test_empty_discovery_is_unavailable_not_authored_fallback(discovered_lab):
    layout, _ = discovered_lab
    (layout.root / "catalogue.json").write_text("[]")
    build_ok(layout)
    page = (layout.runtime / "site/exp022.html").read_text()
    assert "A required run is unavailable." in page
    assert "Image pending" in page and "Video pending" in page
    assert "Result:" not in page and "__preview" not in page
    frozen = json.loads((layout.runtime / "bundle/data-inputs.json").read_text())
    assert frozen["sources"]["exp022"] == {"exp022": None}
    assert frozen["files"] == []
    assert "A required run is unavailable." in _pdf_text(layout.runtime / "site/pdfs/exp022.pdf")


@TYPST_REQUIRED
def test_pins_override_whole_articles_but_discovery_still_runs_once(discovered_lab):
    layout, config = discovered_lab
    config["build"] = {"sources": {"exp022": {"exp022": "runs/old/export"}}}
    layout.config.write_text(json.dumps(config))
    build_ok(layout)
    assert (layout.runtime / "discovery-calls").read_text() == "1"
    assert "Result: 11." in (layout.runtime / "site/exp022.html").read_text()
    assert "Result: 22." in (layout.runtime / "site/gallery.html").read_text()
    config["build"]["sources"]["exp022"] = {}
    layout.config.write_text(json.dumps(config))
    before = snapshot(layout)
    result = _build_result(layout.root)
    assert result.returncode != 0 and "no selection" in result.stderr
    assert snapshot(layout) == before  # A missing pin must not silently switch to Latest.


@TYPST_REQUIRED
@pytest.mark.parametrize("damage", ["command", "json", "timestamp", "directory", "numbers.json",
                                   "chart.svg", "movie.mp4", "corrupt-json", "corrupt-image", "symlink"])
def test_discovery_and_selected_input_errors_preserve_publication(discovered_lab, damage):
    layout, config = discovered_lab
    build_ok(layout)
    before = snapshot(layout)
    selected = layout.root / "runs/new/export"
    if damage == "command":
        config["preview"]["discover"] = [sys.executable, "-c", "raise SystemExit('discovery broke')"]
    elif damage == "json":
        config["preview"]["discover"] = [sys.executable, "-c", "print('not JSON')"]
    elif damage == "timestamp":
        records = json.loads((layout.root / "catalogue.json").read_text())
        records[1]["created_at"] = "invalid"
        (layout.root / "catalogue.json").write_text(json.dumps(records))
    elif damage == "directory":
        selected.rename(selected.with_name("moved"))
    elif damage.startswith("corrupt-"):
        (selected / ("numbers.json" if damage == "corrupt-json" else "chart.svg")).write_text("broken")
    elif damage == "symlink":
        (selected / "link").symlink_to(layout.root / "runs/old/export", target_is_directory=True)
    else:
        (selected / damage).unlink()
    layout.config.write_text(json.dumps(config))
    result = _build_result(layout.root)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "stubbing" not in result.stdout
    assert snapshot(layout) == before


@TYPST_REQUIRED
def test_standalone_pdf_and_deck_share_discovered_inputs(discovered_lab):
    import subprocess
    layout, _ = discovered_lab
    (layout.writings / "talk.slide.typ").write_text(
        '#import "/.demolab/lib.typ": *\n'
        '#let meta = (title: "Talk", created_at: "2026-08-27")\n'
        '#let data-file = data-file.with(article: "exp022")\n'
        'Deck: #json(data-file("exp022/numbers.json")).value.\n')
    build_ok(layout)
    assert "Deck: 22." in _pdf_text(layout.runtime / "site/pdfs/talk.pdf")
    site_before = snapshot(layout)
    command = [sys.executable, "-m", "demolab_cli.build", "exp022"]
    result = subprocess.run(command, env={**os.environ, "DEMOLAB_ROOT": str(layout.root)}, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (layout.runtime / "discovery-calls").read_text() == "2"
    assert "Result: 22." in _pdf_text(layout.runtime / "pdfs/exp022.pdf")
    before = snapshot(layout)
    assert {p: data for p, data in before.items() if p.parts[0] == "site"} == {
        p: data for p, data in site_before.items() if p.parts[0] == "site"}
    (layout.root / "runs/new/export/numbers.json").write_text("corrupt")
    result = subprocess.run(command, env={**os.environ, "DEMOLAB_ROOT": str(layout.root)}, capture_output=True, text=True)
    assert result.returncode != 0 and snapshot(layout) == before
    result = _build_result(layout.root)
    assert result.returncode != 0 and "data-backed build deck" in result.stderr
    assert snapshot(layout) == before


def test_automatic_matching_explicit_absence_and_disabled_articles(tmp_path, monkeypatch):
    layout = _paths.layout_for(tmp_path)
    monkeypatch.setattr(data_sources, "load_build_sources", lambda *a: {})
    monkeypatch.setattr(preview, "load_config", lambda _: preview.Config(
        tmp_path, (), {"empty": ["missing"], "disabled": []}))
    calls = []
    def discover(*args):
        calls.append(args)
        return [dict(experiment=article, presentation="/runs/new") for article in ("automatic", "disabled")]
    monkeypatch.setattr(preview, "discover", discover)
    assert data_sources.resolve_build_sources(layout, ["automatic", "empty", "disabled", "ordinary"]) == {
        "automatic": {"automatic": "/runs/new"}, "empty": {"missing": None}}
    assert len(calls) == 1
    with pytest.raises(_paths.LayoutError, match="unknown discovery article IDs"):
        data_sources.resolve_build_sources(layout, ["automatic"])
