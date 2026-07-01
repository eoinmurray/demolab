"""Shared runner utilities.

`stage(nb_id, commands)` is the whole runner contract in one call: run each
`(tool, command)`, copy its headline figure/video into the committed record at
`artifacts/<nb_id>/`, and write an aggregated `numbers.json`. A runner becomes a
one-liner that declares which commands it bundles.

Layout this assumes (see README):
- tools live in   core/<tool>/tool.py
- raw run output  temp/<tool>/<command>/   (scratch, gitignored)
- committed record artifacts/<nb_id>/       (figures + numbers.json)
"""

import json
import shutil
from pathlib import Path

import sh

ROOT = Path(__file__).resolve().parents[2]   # repo root (scripts/helpers/ -> ../..)
CORE = ROOT / "core"
TEMP = ROOT / "temp"
ARTIFACTS = ROOT / "artifacts"


def _run_tool(tool: str, command: str) -> None:
    sh.uv.run("python", str(CORE / tool / "tool.py"), command, _fg=True)


def _manifest(tool: str, command: str) -> dict:
    return json.loads((TEMP / tool / command / "manifest.json").read_text())


def stage(nb_id: str, commands: list[tuple[str, str]]) -> Path:
    """Run each (tool, command), stage its headline asset + metrics into
    artifacts/<nb_id>/, and write numbers.json. Returns that directory."""
    out = ARTIFACTS / nb_id
    out.mkdir(parents=True, exist_ok=True)

    for tool, command in commands:
        _run_tool(tool, command)

    numbers: dict = {}
    for tool, command in commands:
        manifest = _manifest(tool, command)
        run_dir = TEMP / tool / command
        for field in ("headline_figure", "headline_video"):
            name = manifest.get(field)
            if name:
                shutil.copy(run_dir / name, out / name)
                print(f"staged {name} -> {out / name}")
        config = json.loads((run_dir / "config.json").read_text())
        output = json.loads((run_dir / "output.json").read_text())
        numbers[command] = {
            "config": config,
            **{f: output[f] for f in manifest["headline_metrics"]},
        }

    (out / "numbers.json").write_text(json.dumps(numbers, indent=2) + "\n")
    print(f"wrote {out / 'numbers.json'}")
    return out
