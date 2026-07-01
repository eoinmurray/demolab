import json
import shutil
from pathlib import Path

import sh

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "neuron" / "tool.py"
ARTIFACTS = ROOT / "artifacts" / "neuron"
PUBLIC = ROOT / "docs" / "public" / "notebooks" / "nb000"

COMMANDS = ("lif", "net")


def run_tool(*args: str) -> None:
    sh.uv.run("python", str(TOOL), *args, _fg=True)


def load_manifest(command: str) -> dict:
    return json.loads((ARTIFACTS / command / "manifest.json").read_text())


def collect_numbers() -> dict:
    numbers = {}
    for command in COMMANDS:
        manifest = load_manifest(command)
        config = json.loads((ARTIFACTS / command / "config.json").read_text())
        output = json.loads((ARTIFACTS / command / "output.json").read_text())
        numbers[command] = {
            "config": config,
            **{f: output[f] for f in manifest["headline_metrics"]},
        }
    return numbers


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for command in COMMANDS:
        run_tool(command)
    for command in COMMANDS:
        figure = load_manifest(command)["headline_figure"]
        src = ARTIFACTS / command / figure
        dst = PUBLIC / figure
        shutil.copy(src, dst)
        print(f"copied {figure} -> {dst}")

    numbers_path = PUBLIC / "numbers.json"
    numbers_path.write_text(json.dumps(collect_numbers(), indent=2) + "\n")
    print(f"wrote {numbers_path}")


if __name__ == "__main__":
    main()
