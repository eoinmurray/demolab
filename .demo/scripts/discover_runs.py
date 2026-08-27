"""Demo-owned storage convention: metadata and measurements share numbers.json."""
import json
import os
from pathlib import Path

source = Path(os.environ["DEMOLAB_PREVIEW_SOURCE"])
runs = []
for directory in sorted(source.iterdir()):
    if directory.name.startswith(".") or not directory.is_dir() or directory.is_symlink():
        continue
    record = json.loads((directory / "numbers.json").read_text(encoding="utf-8"))
    runs.append({
        "id": record["run_id"],
        "experiment": record["data_key"],
        "label": record["label"],
        "created_at": record["created_at"],
        "presentation": directory.name,
    })
print(json.dumps(runs))
