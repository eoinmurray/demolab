"""Tests for the install scripts (demolab-engine/scaffold/demo/site/install.sh, install.ps1).

The install.sh bug that shipped — a Unicode ellipsis glued to `$DIR`, which a byte-oriented
`/bin/sh` swallowed into the variable name and crashed under `set -u` — would have been caught
here two ways: the pure-ASCII guard, and actually running the script end-to-end.

The end-to-end run clones from a LOCAL repo via the DEMOLAB_REPO override, so it's offline and
fast; the toolchain-install branches are skipped because uv/typst/task are already present.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "demolab-engine" / "scaffold" / "demo" / "site"
SH = SITE / "install.sh"
PS1 = SITE / "install.ps1"

pytestmark = pytest.mark.skipif(not SH.exists(), reason="demo/site installers absent")


def _is_ascii(p: Path) -> bool:
    return all(b < 128 for b in p.read_bytes())


def test_scripts_are_pure_ascii():
    # A non-ASCII byte next to a shell `$var` is exactly what crashed install.sh under set -u.
    assert _is_ascii(SH), "install.sh must be pure ASCII"
    assert _is_ascii(PS1), "install.ps1 must be pure ASCII"


@pytest.mark.skipif(shutil.which("sh") is None, reason="no sh")
def test_install_sh_syntax():
    subprocess.run(["sh", "-n", str(SH)], check=True)


@pytest.mark.skipif(
    not all(shutil.which(t) for t in ("sh", "git", "task")), reason="needs sh + git + task"
)
def test_install_sh_end_to_end(tmp_path):
    # Run the real script against a local clone of this repo. Exercises every line that always
    # runs (clone, prune, scaffold, the heredoc) under `set -u` — the regression path.
    result = subprocess.run(
        ["sh", str(SH), "mylab"],
        cwd=tmp_path,
        env={**os.environ, "DEMOLAB_REPO": str(REPO)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"install.sh failed:\n{result.stderr}"
    assert "demolab is ready" in result.stdout, "script reached the end (past the old crash point)"
    # Dependencies are reported visibly (not silently skipped when already present).
    assert "Checking dependencies" in result.stdout
    for dep in ("git", "uv", "go-task", "typst"):
        assert dep in result.stdout, f"{dep} not reported in the dependency check"

    lab = tmp_path / "mylab"
    assert (lab / "demolab-engine").is_dir(), "engine present"
    assert (lab / "writings").is_dir(), "structure scaffolded"
    assert (lab / "demolab.yaml").exists(), "config scaffolded"
    assert not (lab / ".github" / "workflows" / "landing.yml").exists(), "upstream Pages workflow pruned"


@pytest.mark.skipif(
    sys.platform != "win32"
    or not (shutil.which("powershell") or shutil.which("pwsh"))
    or not all(shutil.which(t) for t in ("git", "uv")),
    reason="Windows + PowerShell + git + uv only",
)
def test_install_ps1_end_to_end_portable(tmp_path):
    # The path a locked-down Windows box takes (the field report that drove 0.5.3):
    # DEMOLAB_PORTABLE=1 forces the no-winget fallback even where winget exists (CI runners),
    # so task + typst come from release zips into the lab's .tools\bin. Slow (downloads two
    # zips and syncs the project env for `task scaffold`) but it is the only honest check of
    # the installer on the platform it targets.
    shell = shutil.which("powershell") or shutil.which("pwsh")
    env = {
        **os.environ,
        "DEMOLAB_REPO": str(REPO),
        "DEMOLAB_PORTABLE": "1",
        # the script commits the degitted tree; CI runners have no git identity configured
        "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    result = subprocess.run(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1), "mylab"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=900,
    )
    assert result.returncode == 0, f"install.ps1 failed:\n{result.stdout}\n{result.stderr}"
    assert "demolab is ready" in result.stdout, "script reached the end"
    lab = tmp_path / "mylab"
    assert (lab / ".tools" / "bin" / "task.exe").exists(), "portable go-task installed"
    assert (lab / ".tools" / "bin" / "typst.exe").exists(), "portable typst installed"
    assert (lab / "writings").is_dir(), "structure scaffolded (task resolved from .tools/bin)"
    assert (lab / "demolab.yaml").exists(), "config scaffolded"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="no pwsh (PowerShell) to parse .ps1")
def test_install_ps1_parses():
    # Parse-only — the full run is Windows-only (above). Parsing catches syntax and obvious errors.
    script = (
        "$e=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{PS1}', [ref]$null, [ref]$e) > $null; "
        "if ($e) { exit 1 }"
    )
    subprocess.run(["pwsh", "-NoProfile", "-Command", script], check=True)
