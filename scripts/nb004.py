"""nb004 — a Typst publisher.

Same tool + committed bundle as the web entries, but the document is Typst and
the output is a PDF instead of a web page. It shows that publishing is pluggable:
the runner stages the bundle into artifacts/, then a publisher-specific step
(here: `typst compile`) turns it into the final PDF.
"""

import json
import shutil
from pathlib import Path

import sh
import typst

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "core" / "neuron" / "tool.py"
TEMP = ROOT / "temp" / "neuron"            # tool's raw run output (scratch)
ARTIFACTS = ROOT / "artifacts" / "nb004"   # committed bundle (figure + numbers.json)
DOC = ROOT / "entries" / "nb004.typ"       # the writeup
PDF = ROOT / "temp" / "nb004.pdf"          # compiled output (gitignored, regenerated)

COMMANDS = ("lif",)


def run_tool(*args: str) -> None:
    sh.uv.run("python", str(TOOL), *args, _fg=True)


def load_manifest(command: str) -> dict:
    return json.loads((TEMP / command / "manifest.json").read_text())


def collect_numbers() -> dict:
    numbers = {}
    for command in COMMANDS:
        manifest = load_manifest(command)
        config = json.loads((TEMP / command / "config.json").read_text())
        output = json.loads((TEMP / command / "output.json").read_text())
        numbers[command] = {
            "config": config,
            **{f: output[f] for f in manifest["headline_metrics"]},
        }
    return numbers


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    # 1. run the tool(s) and stage the committed bundle (identical to any publisher)
    for command in COMMANDS:
        run_tool(command)
    for command in COMMANDS:
        figure = load_manifest(command)["headline_figure"]
        shutil.copy(TEMP / command / figure, ARTIFACTS / figure)
        print(f"staged {figure} -> {ARTIFACTS / figure}")
    (ARTIFACTS / "numbers.json").write_text(json.dumps(collect_numbers(), indent=2) + "\n")

    # 2. publish: compile the Typst document to a PDF. --root is the repo root so
    #    the document can read the shared bundle at /artifacts/nb004/.
    PDF.parent.mkdir(parents=True, exist_ok=True)
    typst.compile(str(DOC), output=str(PDF), root=str(ROOT))
    print(f"wrote {PDF}")


if __name__ == "__main__":
    main()
