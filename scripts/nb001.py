import json
import shutil
from pathlib import Path

import sh

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "core" / "neuron" / "tool.py"
TEMP = ROOT / "temp" / "neuron"
ARTIFACTS = ROOT / "artifacts" / "nb001"

COMMANDS = ("eif", "enet")


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
    for command in COMMANDS:
        run_tool(command)
    for command in COMMANDS:
        figure = load_manifest(command)["headline_figure"]
        src = TEMP / command / figure
        dst = ARTIFACTS / figure
        shutil.copy(src, dst)
        print(f"copied {figure} -> {dst}")

    numbers_path = ARTIFACTS / "numbers.json"
    numbers_path.write_text(json.dumps(collect_numbers(), indent=2) + "\n")
    print(f"wrote {numbers_path}")


if __name__ == "__main__":
    main()
