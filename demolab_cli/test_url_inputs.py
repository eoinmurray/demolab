"""URL parameters are explicit compiler inputs, never shared preview selections."""
import json
import shutil
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from demolab_cli import _paths, devserver, url_inputs


@pytest.fixture
def lab(tmp_path):
    if not shutil.which("typst") and not Path(_paths.find_typst(Path.cwd())).is_file():
        pytest.skip("Typst required")
    # Use the checkout compiler when it is not installed globally.
    compiler = _paths.find_typst(Path.cwd())
    (tmp_path / ".tools/bin").mkdir(parents=True)
    (tmp_path / ".tools/bin/typst").symlink_to(compiler)
    (tmp_path / "writings").mkdir()
    for name, value in (("one", 10), ("two", 20)):
        directory = tmp_path / "data" / name
        directory.mkdir(parents=True)
        (directory / "numbers.json").write_text(json.dumps({"value": value}))
        (directory / "plot.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="30">'
            f'<rect width="{value}" height="30" fill="red"/></svg>')
        (directory / "movie.mp4").write_bytes(name.encode())
    (tmp_path / "demolab.yaml").write_text(json.dumps({"pdfs": False, "url_inputs": {
        "basepath": {"type": "path", "root": "data"},
        "other": {"type": "path", "root": "data"},
        "label": {"type": "string"},
    }}))
    (tmp_path / "writings/report.typ").write_text('''
#import "/.demolab/lib.typ": video
#let meta = (title: "Report", created_at: "2026-08-28")
#let base = sys.inputs.at("basepath", default: "/data/one")
#let other = sys.inputs.at("other", default: "/data/one")
#let body = [
  Value: #json(base + "/numbers.json").value
  Other: #json(other + "/numbers.json").value
  #sys.inputs.at("label", default: "default label")
  #image(base + "/plot.svg")
  #video(base + "/movie.mp4")
  #link("report?basepath=data/two")[Other selection]
]
''')
    return _paths.layout_for(tmp_path)


def test_paths_and_strings_are_explicit_inputs(lab):
    values, directories = url_inputs.resolve_query(lab, "basepath=data/one&label=A%20B")
    assert values == {"basepath": "/data/one", "label": "A B"}
    assert directories == [lab.content / "data/one"]


@pytest.mark.parametrize("query", [
    "unknown=1", "demolab-preview-file=anything", "basepath=/etc", "basepath=../data",
    "basepath=data/../data/one", "basepath=data/missing", "basepath=writings",
    "basepath=data/one&basepath=data/two", "label=%00", "basepath=C%3A/foo", "label=" + "x" * 2049,
])
def test_rejects_invalid_inputs(lab, query):
    with pytest.raises((url_inputs.InputError, _paths.LayoutError)):
        url_inputs.resolve_query(lab, query)


def test_rejects_symlink_and_special_descendants(lab):
    (lab.content / "data/alias").symlink_to(lab.content / "data/one", target_is_directory=True)
    with pytest.raises(url_inputs.InputError, match="symlink"):
        url_inputs.resolve_query(lab, "basepath=data/alias")
    (lab.content / "data/one/escape").symlink_to(lab.content / "writings", target_is_directory=True)
    with pytest.raises(_paths.LayoutError, match="symlinks"):
        url_inputs.resolve_query(lab, "basepath=data/one")


def test_two_tabs_have_independent_output_and_no_preview_state(lab):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(url_inputs.render, lab, "/report/", query) for query in (
            "basepath=data/one&label=first", "basepath=data/two&other=data/two&label=second")]
        (first, first_site), (second, second_site) = [f.result() for f in futures]
    assert first_site != second_site
    assert "Value: 10" in first and "Other: 10" in first and "first" in first
    assert "Value: 20" in second and "Other: 20" in second and "second" in second
    assert 'image-lightbox.js" defer></script>' in first
    assert (first_site / "image-lightbox.js").is_file()
    assert "EventSource" not in first and "__preview" not in first
    assert '/__render/' in first and 'href="/report?basepath=data/two"' in first
    assert not (lab.runtime / "preview").exists()
    assert not (lab.runtime / "site").exists()
    assert list(first_site.glob("_demolab-data/*.mp4"))[0].read_bytes() == b"one"
    assert list(second_site.glob("_demolab-data/*.mp4"))[0].read_bytes() == b"two"
    before = (first_site / "report.html").read_bytes()
    (lab.content / "data/two/numbers.json").write_text("bad JSON")
    with pytest.raises(url_inputs.InputError, match="rendering failed"):
        url_inputs.render(lab, "/report.html", "basepath=data/two")
    assert (first_site / "report.html").read_bytes() == before


def test_private_resource_boundary(lab):
    _, site = url_inputs.render(lab, "/report", "basepath=data/one")
    prefix = url_inputs.PREFIX + site.parent.name + "/"
    assert url_inputs.resource(lab, prefix + "favicon.svg") == site / "favicon.svg"
    with pytest.raises(url_inputs.InputError):
        url_inputs.resource(lab, prefix + "../index.json")


def test_reserved_config_and_no_config(lab):
    lab.config.write_text('{"url_inputs":{"demolab-internal":{"type":"string"}}}')
    with pytest.raises(url_inputs.InputError, match="reserved"):
        url_inputs.load_config(lab)
    lab.config.unlink()
    with pytest.raises(url_inputs.InputError, match="not allowed"):
        url_inputs.resolve_query(lab, "basepath=data/one")


def test_http_request_and_resource_isolation(lab, monkeypatch):
    monkeypatch.setattr(devserver, "LAYOUT", lab)
    monkeypatch.setattr(devserver, "SITE", lab.runtime / "site")
    monkeypatch.setattr(devserver, "PREVIEW", None)
    server = devserver.make_server(0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base + "/report?basepath=data/one") as response:
            page = response.read().decode()
            assert response.headers["Cache-Control"] == "no-store"
        assert "Value: 10" in page and "__dev" not in page
        import re
        video = re.search(r'src="([^"]+\.mp4)"', page).group(1)
        assert video.startswith("/__render/")
        with urllib.request.urlopen(base + video) as response:
            assert response.read() == b"one"
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(base + "/report?basepath=../data/one")
        assert exc.value.code == 400
        request = urllib.request.Request(base + "/report?basepath=data/one",
                                         headers={"Sec-Fetch-Site": "cross-site"})
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == 403
    finally:
        server.shutdown()
        server.server_close()


def test_resource_rewrite_preserves_svg_case_and_self_closing_markup(tmp_path):
    (tmp_path / "plot.svg").write_text("svg")
    markup = '<svg viewBox="0 0 10 10"><clipPath id="c"/></svg><img src="plot.svg"/>'
    parser = url_inputs.ResourceURLs(tmp_path, "/__render/view-test/")
    parser.feed(markup)
    assert "".join(parser.parts) == markup.replace('src="plot.svg"', 'src="/__render/view-test/plot.svg"')


def test_ordinary_query_strings_still_work_without_url_inputs(lab, monkeypatch):
    lab.config.write_text('{"pdfs":false}')
    site = lab.runtime / "site"
    site.mkdir(parents=True)
    (site / "report.html").write_text("<html><body>Ordinary article</body></html>")
    monkeypatch.setattr(devserver, "LAYOUT", lab)
    monkeypatch.setattr(devserver, "SITE", site)
    monkeypatch.setattr(devserver, "PREVIEW", None)
    server = devserver.make_server(0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{server.server_port}/report?unrelated=value"
        ) as response:
            assert response.status == 200
            assert b"Ordinary article" in response.read()
        assert not (lab.runtime / "url-inputs").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_prepare_receives_normalized_inputs_and_can_reject_request(lab):
    config = json.loads(lab.config.read_text())
    command = ('import os,json; from pathlib import Path; '
               'Path("prepared.json").write_text(json.dumps([os.environ["DEMOLAB_ARTICLE"], '
               'json.loads(os.environ["DEMOLAB_INPUTS"])]))')
    config["prepare"] = [sys.executable, "-c", command]
    lab.config.write_text(json.dumps(config))
    url_inputs.render(lab, "/report", "basepath=data/two")
    assert json.loads((lab.root / "prepared.json").read_text()) == ["report", {"basepath": "/data/two"}]
    config["prepare"] = [sys.executable, "-c", "raise SystemExit('invalid selected input')"]
    lab.config.write_text(json.dumps(config))
    before = set((lab.runtime / "url-inputs").iterdir())
    with pytest.raises(ValueError, match="invalid selected input"):
        url_inputs.render(lab, "/report", "basepath=data/one")
    assert set((lab.runtime / "url-inputs").iterdir()) == before


def test_user_defaults_and_attachments_work_in_static_and_url_renders(lab):
    (lab.writings / "report.typ").write_text('''
#import "/.demolab/lib.typ": video
#let base = sys.inputs.at("basepath", default: "/data/one")
#let meta = (title: "Report", created_at: "2026-08-28", assets: ("clip.mp4": base + "/movie.mp4"))
#let body = [Value: #json(base + "/numbers.json").value #video("clip.mp4")]
''')
    config = json.loads(lab.config.read_text())
    config["prepare"] = [sys.executable, "-c", "pass"]
    lab.config.write_text(json.dumps(config))
    command = [sys.executable, "-m", "demolab_cli.build", "--no-pdf-copy"]
    env = {**os.environ, "DEMOLAB_ROOT": str(lab.root)}
    result = subprocess.run(command, cwd=lab.root, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    page = lab.runtime / "site/report.html"
    original = page.read_bytes()
    assert b"Value: 10" in original
    assert (lab.runtime / "site/clip.mp4").read_bytes() == b"one"
    changed, site = url_inputs.render(lab, "/report", "basepath=data/two")
    assert "Value: 20" in changed
    assert (site / "clip.mp4").read_bytes() == b"two"
    assert page.read_bytes() == original
    # A prepared ordinary build also fails closed instead of publishing an error stub.
    (lab.content / "data/one/numbers.json").write_text("broken")
    result = subprocess.run(command, cwd=lab.root, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert page.read_bytes() == original


def test_pdf_link_is_request_scoped(lab):
    config = json.loads(lab.config.read_text())
    config["pdfs"] = True
    lab.config.write_text(json.dumps(config))
    page, site = url_inputs.render(lab, "/report.html", "basepath=data/one")
    assert (site / "pdfs/report.pdf").is_file()
    assert f'/__render/{site.parent.name}/pdfs/report.pdf' in page
