"""Fixed publication pins, isolation from preview, and self-contained video output."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from demolab_cli import _paths, data_sources
from demolab_cli.test_engine_build import _assemble, _build, _build_result, _pdf_text

TYPST_REQUIRED = pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")


@TYPST_REQUIRED
@pytest.mark.parametrize("setting", [[], {"runs": {}}, {"sources": []},
    {"sources": {"unknown": {}}}, {"sources": {"exp": []}},
    {"sources": {"exp": {"../exp": "runs/old"}}},
    *[{"sources": {"exp": {"exp": path}}} for path in
      (None, 3, [], "", "/outside", "../outside", "C:/outside", "runs\\old", "runs/../old")]])
def test_invalid_build_settings(tmp_path, setting):
    (tmp_path / "demolab.yaml").write_text(json.dumps({"build": setting}))
    with pytest.raises(_paths.LayoutError):
        data_sources.load_build_sources(_paths.layout_for(tmp_path), ["exp"])


def test_directory_inventory_rejects_missing_runtime_and_escaping_paths(tmp_path):
    layout = _paths.layout_for(tmp_path)
    for path in (tmp_path, tmp_path.parent, layout.runtime, tmp_path / "absent"):
        with pytest.raises(_paths.LayoutError):
            data_sources.directory_files(path, layout)


def test_directory_inventory_rejects_symlinks_and_special_files(tmp_path):
    layout = _paths.layout_for(tmp_path)
    run = tmp_path / "runs"
    run.mkdir()
    link = run / "link"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(_paths.LayoutError, match="symlink"):
        data_sources.directory_files(run, layout)
    with pytest.raises(_paths.LayoutError, match="symlink"):
        data_sources.directory_files(link, layout)
    link.unlink()
    if hasattr(os, "mkfifo"):
        os.mkfifo(run / "pipe")
        with pytest.raises(_paths.LayoutError, match="special files"):
            data_sources.directory_files(run, layout)


@pytest.fixture
def pinned_lab(tmp_path):
    _assemble(tmp_path, demo=False)
    layout = _paths.layout_for(tmp_path)
    for name, value in [("old", 11), ("new", 22)]:
        directory = tmp_path / "runs" / name / "presentation"
        directory.mkdir(parents=True)
        (directory / "numbers.json").write_text(json.dumps({"value": value}))
        (directory / "chart.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><text x="0" y="30">{value}</text></svg>')
        # Byte-level packaging fixture, not a playable video or a browser test.
        (directory / "movie.mp4").write_bytes(f"video from {name}".encode())
        (directory / "private.txt").write_text("must not be published")
    for article, keys in [("exp", ["exp"]), ("gallery", ["exp", "other"]),
                          ("compare", ["legacy.exp", "current.exp"])]:
        (layout.writings / f"{article}.typ").write_text(
            '#import "/.demolab/lib.typ": *\n'
            f'#let meta = (title: "{article}", created_at: "2026-08-27")\n'
            f'#let data-file = data-file.with(article: "{article}")\n'
            '#let body = [\n'
            '  #for key in (' + ', '.join(json.dumps(key) for key in keys) + ',) {\n'
            '    let r = json(data-file(key + "/numbers.json"))\n'
            '    [Result: #r.value.]\n'
            '    figure(image(data-file(key + "/chart.svg")), caption: [Result])\n'
            '    video(data-file(key + "/movie.mp4"), caption: [Recorded run])\n'
            '  }\n]\n')
    config = {"name": "Fixed inputs", "build": {"sources": {
        "exp": {"exp": "runs/old/presentation"},
        "gallery": {"exp": "runs/new/presentation", "other": "runs/old/presentation"},
        "compare": {"legacy.exp": "runs/old/presentation", "current.exp": "runs/new/presentation"}}}}
    layout.config.write_text(json.dumps(config))
    return layout, config


@TYPST_REQUIRED
def test_fixed_builds_scope_every_target_export_videos_and_ignore_preview(pinned_lab):
    layout, config = pinned_lab
    preview = layout.runtime / "preview"
    preview.mkdir(parents=True)
    (preview / "input.json").write_text("invalid local preview state")
    (preview / "state.json").write_text("invalid local preview state")
    inputs = {p: p.read_bytes() for p in (layout.root / "runs").rglob("*") if p.is_file()}
    _build(layout.root)
    site = layout.runtime / "site"
    assert "Result: 11." in (site / "exp.html").read_text()
    for article in ("gallery", "compare"):
        page = (site / f"{article}.html").read_text()
        assert "Result: 11." in page and "Result: 22." in page
        assert "__preview" not in page
    assert "Result: 11." in _pdf_text(site / "pdfs/exp.pdf")
    assert "Result: 22." in _pdf_text(site / "pdfs/book.pdf")
    for article, expected in [("exp", [b"video from old"]),
                              ("compare", [b"video from old", b"video from new"])]:
        urls = re.findall(r'<video src="([^"]+)"', (site / f"{article}.html").read_text())
        assert len(urls) == len(expected)
        assert all(url.startswith("_demolab-data/") for url in urls)
        assert [(site / url).read_bytes() for url in urls] == expected
    assert len(list((site / "_demolab-data").iterdir())) == 2
    assert not list(site.rglob("private.txt")) and not list(site.rglob("numbers.json"))
    assert inputs == {p: p.read_bytes() for p in inputs}
    unchanged = (site / "compare.html").read_bytes()
    config["build"]["sources"]["exp"]["exp"] = "runs/new/presentation"
    layout.config.write_text(json.dumps(config))
    _build(layout.root)
    assert "Result: 22." in (site / "exp.html").read_text()
    assert (site / "compare.html").read_bytes() == unchanged
    # Standalone PDF builds use the same pins, not a stale bundle input snapshot.
    config["build"]["sources"]["exp"]["exp"] = "runs/old/presentation"
    layout.config.write_text(json.dumps(config))
    _build(layout.root, "exp")
    assert "Result: 11." in _pdf_text(layout.runtime / "pdfs/exp.pdf")
    assert "Result: 22." in (site / "exp.html").read_text()


@TYPST_REQUIRED
def test_removing_pins_does_not_reuse_old_generated_mapping(pinned_lab):
    layout, config = pinned_lab
    _build(layout.root)
    for key in ("exp", "other", "legacy.exp", "current.exp"):
        destination = layout.data / key
        shutil.copytree(layout.root / "runs/new/presentation", destination)
        (destination / "numbers.json").write_text('{"value": 99}')
    del config["build"]
    layout.config.write_text(json.dumps(config))
    _build(layout.root)
    assert "Result: 99." in (layout.runtime / "site/exp.html").read_text()


@TYPST_REQUIRED
def test_pins_reach_deck_pdfs_and_deck_failure_preserves_publication(pinned_lab):
    layout, _ = pinned_lab
    deck = layout.writings / "talk.slide.typ"
    deck.write_text('#import "/.demolab/lib.typ": *\n'
                    '#let meta = (title: "Talk", created_at: "2026-08-27")\n'
                    '#let data-file = data-file.with(article: "exp")\n'
                    '#let r = json(data-file("exp/numbers.json"))\nDeck result: #r.value.\n')
    _build(layout.root)
    assert "Deck result: 11." in _pdf_text(layout.runtime / "site/pdfs/talk.pdf")
    outputs = {p: p.read_bytes() for base in (layout.runtime / "site", layout.runtime / "pdfs")
               for p in base.rglob("*") if p.is_file()}
    deck.write_text(deck.read_text() + "\n#(1 / 0)\n")
    result = _build_result(layout.root)
    assert result.returncode != 0 and "data-backed build deck" in result.stderr
    assert outputs == {p: p.read_bytes() for p in outputs}


@TYPST_REQUIRED
@pytest.mark.parametrize("damage", ["directory", "numbers.json", "chart.svg", "movie.mp4", "key", "compile"])
def test_invalid_pins_preserve_previous_site_and_pdfs(pinned_lab, damage):
    layout, config = pinned_lab
    _build(layout.root)
    outputs = {p: p.read_bytes() for base in (layout.runtime / "site", layout.runtime / "pdfs")
               for p in base.rglob("*") if p.is_file()}
    if damage == "directory":
        config["build"]["sources"]["exp"]["exp"] = "runs/missing/presentation"
    elif damage == "key":
        config["build"]["sources"]["exp"] = {}
    elif damage == "compile":
        article = layout.writings / "exp.typ"
        article.write_text(article.read_text() + "\n#let broken = 1 / 0\n")
    else:
        (layout.root / "runs/old/presentation" / damage).unlink()
    layout.config.write_text(json.dumps(config))
    result = _build_result(layout.root)
    assert result.returncode != 0
    assert "stubbing" not in result.stdout
    assert outputs == {p: p.read_bytes() for p in outputs}
    result = subprocess.run([sys.executable, "-m", "demolab_cli.build", "exp"],
                            env={**os.environ, "DEMOLAB_ROOT": str(layout.root)}, capture_output=True, text=True)
    assert result.returncode != 0
    assert outputs == {p: p.read_bytes() for p in outputs}


@TYPST_REQUIRED
def test_preview_ignores_build_pins_and_packages_selected_videos(pinned_lab):
    layout, config = pinned_lab
    config["build"] = {"not-valid": True}
    layout.config.write_text(json.dumps(config))
    runtime = layout.runtime / "preview"
    runtime.mkdir(parents=True)
    (runtime / "input.json").write_text(json.dumps({
        article: {key: "/runs/new/presentation" for key in keys}
        for article, keys in [("exp", ["exp"]), ("gallery", ["exp", "other"]),
                              ("compare", ["legacy.exp", "current.exp"])]}))
    result = subprocess.run([sys.executable, "-m", "demolab_cli.build", "--preview"],
                            env={**os.environ, "DEMOLAB_ROOT": str(layout.root)}, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    page = (runtime / "site/exp.html").read_text()
    assert "Result: 22." in page and "Result: 11." not in page
    url = re.search(r'<video src="([^"]+)"', page).group(1)
    assert (runtime / "site" / url).read_bytes() == b"video from new"
    assert not (layout.runtime / "site").exists()


def test_media_namespace_cannot_collide_with_static_assets(tmp_path):
    layout = _paths.layout_for(tmp_path)
    source = tmp_path / "runs"
    source.mkdir()
    (source / "movie.mp4").write_bytes(b"video")
    (layout.assets / "_demolab-data").mkdir(parents=True)
    with pytest.raises(_paths.LayoutError, match="reserved"):
        data_sources.inventory(layout, {"exp": {"exp": "/runs"}})
