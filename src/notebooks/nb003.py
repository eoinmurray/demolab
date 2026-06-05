import json
import shutil
from pathlib import Path

import sh

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
PUBLIC = ROOT / "docs" / "public" / "notebooks" / "nb003"

COMMANDS = (
    ("mujoco_lab", "double_pendulum", ("mujoco", "imageio[ffmpeg]", "numpy")),
)


def run_cli(tool: str, command: str, deps: tuple[str, ...]) -> None:
    cli = ROOT / "simulators" / tool / "cli.py"
    with_args: list[str] = []
    for dep in deps:
        with_args += ["--with", dep]
    sh.uv.run(*with_args, "python", str(cli), command, _fg=True)


def artifact_dir(tool: str, command: str) -> Path:
    return ARTIFACTS / tool / command


def load_manifest(tool: str, command: str) -> dict:
    return json.loads((artifact_dir(tool, command) / "manifest.json").read_text())


def collect_numbers() -> dict:
    numbers: dict = {}
    for tool, command, _ in COMMANDS:
        manifest = load_manifest(tool, command)
        config = json.loads((artifact_dir(tool, command) / "config.json").read_text())
        output = json.loads((artifact_dir(tool, command) / "output.json").read_text())
        numbers[command] = {
            "config": config,
            **{f: output[f] for f in manifest.get("headline_metrics", [])},
        }
    return numbers


def copy_headline_assets() -> None:
    for tool, command, _ in COMMANDS:
        manifest = load_manifest(tool, command)
        src_dir = artifact_dir(tool, command)
        for field in ("headline_figure", "headline_video"):
            name = manifest.get(field)
            if not name:
                continue
            src = src_dir / name
            dst = PUBLIC / name
            shutil.copy(src, dst)
            print(f"copied {name} -> {dst}")


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for tool, command, deps in COMMANDS:
        run_cli(tool, command, deps)
    copy_headline_assets()
    numbers_path = PUBLIC / "numbers.json"
    numbers_path.write_text(json.dumps(collect_numbers(), indent=2) + "\n")
    print(f"wrote {numbers_path}")


if __name__ == "__main__":
    main()
