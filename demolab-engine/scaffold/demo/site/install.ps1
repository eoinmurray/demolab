# demolab installer (Windows / PowerShell).
#
#   powershell -ExecutionPolicy ByPass -c "irm https://demolab.eoinmurray.info/install.ps1 | iex"
#
# Installs the toolchain (uv, typst, go-task), makes you a fresh, owned copy of demolab,
# scaffolds the folder structure, and prints how to continue. It does NOT install or launch a
# coding agent -- bring your own and paste the prompt it prints.
#
# Toolchain sources: winget where it exists; without it (locked-down box, no package manager --
# or DEMOLAB_PORTABLE=1 to force this) the task + typst release binaries are downloaded into
# the lab's own .tools\bin, which the build prefers over PATH.
$ErrorActionPreference = "Stop"

# DEMOLAB_REPO lets a fork/mirror (or the test suite) install from elsewhere; defaults to upstream.
$Repo   = if ($env:DEMOLAB_REPO) { $env:DEMOLAB_REPO } else { "https://github.com/eoinmurray/demolab" }
$Dir    = if ($args.Count -ge 1) { $args[0] } else { "demolab" }
$Prompt = "Read AGENTS.md and follow the Getting started runbook to set up my lab."

function Have($cmd) { $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue) }
function Ok($name, $cmd) { if (-not $cmd) { $cmd = $name }; Write-Host ("  [ok]   {0,-8} {1}" -f $name, (Get-Command $cmd -ErrorAction SilentlyContinue).Source) -ForegroundColor Green }
function Adding($name)  { Write-Host ("  [..]   {0,-8} installing..." -f $name) -ForegroundColor Yellow }

$UseWinget = (Have "winget") -and ($env:DEMOLAB_PORTABLE -ne "1")
$Arch      = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
$TypstArch = if ($Arch -eq "arm64") { "aarch64" } else { "x86_64" }
$ZipUrl = @{
  "go-task" = "https://github.com/go-task/task/releases/latest/download/task_windows_$Arch.zip"
  "typst"   = "https://github.com/typst/typst/releases/latest/download/typst-$TypstArch-pc-windows-msvc.zip"
}

# The no-winget fallback: fetch the tool's release zip and put its .exe in the lab's .tools\bin
# (created on demand, prepended to this session's PATH). Must run after the clone so the lab
# directory exists. The build itself prefers .tools\bin over PATH, so typst keeps resolving in
# terminals that never saw this session's PATH.
function Install-Portable($name, $exe) {
  Adding $name
  $bin = Join-Path (Get-Location) ".tools\bin"
  New-Item -ItemType Directory -Force -Path $bin | Out-Null
  $tmp   = [System.IO.Path]::GetTempPath()  # not $env:TEMP -- null on non-Windows pwsh (tests)
  $zip   = Join-Path $tmp "demolab-$exe.zip"
  $stage = Join-Path $tmp "demolab-$exe-unzip"
  Invoke-WebRequest $ZipUrl[$name] -OutFile $zip
  Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
  Expand-Archive $zip -DestinationPath $stage -Force
  Get-ChildItem $stage -Recurse -Filter $exe | Select-Object -First 1 | Copy-Item -Destination $bin
  Remove-Item $zip
  Remove-Item -Recurse -Force $stage
  if (-not ($env:PATH -like "$bin*")) { $env:PATH = "$bin;$env:PATH" }
  Write-Host ("  [ok]   {0,-8} {1}" -f $name, (Join-Path $bin $exe)) -ForegroundColor Green
}
$Portable = $false

if (Test-Path $Dir) { throw "A '$Dir' directory already exists here. Pass another name after the command." }

# --- dependencies that must exist before the clone ---
Write-Host ""
Write-Host "Checking dependencies" -ForegroundColor White

if (-not (Have "git")) { throw "git is required -- install it first, then re-run." }
Ok "git"

if (Have "uv") { Ok "uv" } else { Adding "uv"; Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression }

# --- your own copy (before task/typst: the portable fallback installs into the lab's
# .tools\bin, which needs the tree to exist) ---
Write-Host "Fetching demolab into ./$Dir ..."
git clone --depth 1 $Repo $Dir
Set-Location $Dir
Remove-Item -Recurse -Force .git
# Drop upstream-only deploy workflow.
Remove-Item -Recurse -Force .github/workflows/landing.yml -ErrorAction SilentlyContinue
git init -q; git add -A; git commit -q -m "Start my lab from demolab"

# --- the rest of the toolchain ---
if (Have "task") { Ok "go-task" "task" }
elseif ($UseWinget) { Adding "go-task"; winget install Task.Task --accept-source-agreements --accept-package-agreements }
else { Install-Portable "go-task" "task.exe"; $Portable = $true }

if (Have "typst") { Ok "typst" }
elseif ($UseWinget) { Adding "typst"; winget install Typst.Typst --accept-source-agreements --accept-package-agreements }
else { Install-Portable "typst" "typst.exe"; $Portable = $true }

# --- lay down the bare structure ---
Write-Host "Scaffolding the folder structure..."
task scaffold

Write-Host ""
Write-Host "--------------------------------------------------------------"
Write-Host "demolab is ready in ./$Dir"
Write-Host ""
Write-Host "Next, either:"
Write-Host "  - Open your coding agent in ./$Dir and paste:"
Write-Host "      $Prompt"
Write-Host "  - Or explore by hand:"
Write-Host "      cd $Dir; task add-demo-content; task dev"
Write-Host "--------------------------------------------------------------"
Write-Host ""
if ($Portable) {
  Write-Host "(task + typst live in .tools\bin inside the lab -- already on this terminal's PATH."
  Write-Host " In a new terminal, run this once from the lab root:"
  Write-Host '   $env:PATH = "$(Resolve-Path .tools\bin);$env:PATH"' -NoNewline; Write-Host " )"
} else {
  Write-Host "(If 'task' or 'typst' isn't found, reopen your terminal so PATH refreshes.)"
}
