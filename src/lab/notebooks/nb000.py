import json
import shutil
from pathlib import Path

import sh

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "lab" / "cli.py"
ARTIFACTS = ROOT / "artifacts" / "cli"
PUBLIC = ROOT / "docs" / "public" / "notebooks" / "nb000"

ASSETS = (("lif", "lif.png"), ("net", "net.png"))

RATE_FIELDS = {
    "lif": ("firing_rate_hz",),
    "net": ("mean_firing_rate_hz", "min_firing_rate_hz", "max_firing_rate_hz"),
}


def run_cli(*args: str) -> None:
    sh.uv.run(
        "--with", "numpy",
        "--with", "matplotlib",
        "python", str(CLI), *args,
        _fg=True,
    )


def collect_numbers() -> dict:
    numbers = {}
    for command, fields in RATE_FIELDS.items():
        config = json.loads((ARTIFACTS / command / "config.json").read_text())
        output = json.loads((ARTIFACTS / command / "output.json").read_text())
        numbers[command] = {
            "config": config,
            **{f: output[f] for f in fields},
        }
    return numbers


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    run_cli("lif")
    run_cli("net")
    for command, name in ASSETS:
        src = ARTIFACTS / command / name
        dst = PUBLIC / name
        shutil.copy(src, dst)
        print(f"copied {name} -> {dst}")

    numbers_path = PUBLIC / "numbers.json"
    numbers_path.write_text(json.dumps(collect_numbers(), indent=2) + "\n")
    print(f"wrote {numbers_path}")


if __name__ == "__main__":
    main()
