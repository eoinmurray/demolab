# Runbook: Update demolab

> Refresh the demolab **engine** to the latest release while leaving everything that's *yours* —
> branding, content, deps — untouched.

## When to use
When a newer demolab engine is out and you want its fixes and features without disturbing your own
lab. **The model: the engine is the `demolab-cli` package; your lab is content.** Updating is a
normal dependency bump — no vendor-copy, no reconcile ritual. Three zones:

- **The package** (pure upstream — nothing of the user's lives in it): build code, Typst
  templates, runbooks, guides, scaffold + demo. Updated wholesale by `uv`.
- **Machine-managed staging** (`.demolab/` at the lab root, gitignored): the CLI refreshes it
  automatically the first time any build runs on a new engine version. Never hand-edit it.
- **Never touch** (100% the user's): `demolab.yaml`, `HOUSESTYLE.local.md`, `writings/`,
  `tools/`, `experiments/`, `artifacts/`, `pyproject.toml`, the root stubs (`AGENTS.md`,
  `README.md`, CI).

Branding (the wordmark + PDF titles) lives in the root `demolab.yaml`, *outside* the package, so
updating the engine can't touch the user's identity — that's the point.

## What it does

1. **Check versions.** `demolab version` prints the installed engine; the newest release is on
   <https://pypi.org/project/demolab-cli/>. (Or just proceed — step 3 is a no-op when already
   current.)

2. **Read what's coming.** Show the user the changelog entries between their version and the
   latest: the Changelog link on the PyPI page before updating, or `demolab docs CHANGELOG
   --print` after. **If the major version differs, stop and get explicit confirmation** — a
   major release may need edits to *their* content (the tool ↔ experiment contract, the `meta`
   schema, or import paths); its changelog entry says exactly what.

3. **Bump the dependency.**
   ```sh
   uv lock --upgrade-package demolab-cli && uv sync
   ```

4. **Rebuild.** `demolab build` — the CLI notices the version change, refreshes `.demolab/`,
   and prints a one-line notice pointing at the changelog. `demolab test` for good measure.

5. **Check the override surface.** If the release added a new branding key (its changelog entry
   lists them), mention it — the engine defaults every key, so nothing breaks, but the user may
   want to set it in `demolab.yaml`.

6. **Refresh opted-in CI templates** (only if `.github/workflows/deploy.yml`/`preview.yml`
   exist): rerun `demolab deploy-setup` to take the updated templates, then diff before
   committing.

7. **Commit** the `pyproject.toml`/`uv.lock` change, describing what was pulled.

Notes: reproducibility is the lockfile's job — `uv.lock` pins the exact engine version, so a
fresh clone of the lab rebuilds with the same engine until *you* bump it. If something ever
needs customising *inside* the engine, that's a missing config knob — set what `demolab.yaml`
offers, or propose the knob upstream (`demolab docs SUPPORT`).

## Migrating a pre-1.0 lab (vendored `demolab-engine/`)

Labs created before 1.0 carry the engine as a committed `demolab-engine/` directory and a
launcher wired into `pyproject.toml`. One-time migration, in order:

1. `pyproject.toml`: add `demolab-cli>=1.0` to `[project.dependencies]`; delete the
   `[project.scripts]` demolab entry and any `[tool.hatch.build.targets.wheel]` /
   `force-include` blocks (a lab is content, not a package — adding `[tool.uv] package = false`
   is the clean end state; model it on a fresh `demolab init` elsewhere).
2. Delete the vendored engine: `git rm -r demolab-engine` (and a root `demolab.py` if present).
3. Point the writings at the staged lib — in every `writings/*.typ`:
   `"/demolab-engine/build/lib.typ"` → `"/.demolab/lib.typ"`.
4. Append `.demolab/` to `.gitignore`.
5. `uv sync`, then `demolab build && demolab test` — green means the migration is done; commit.
6. If `.github/workflows/deploy.yml` exists, rerun `demolab deploy-setup` (the old template
   called the vendored build script, which no longer exists).

---

## Agent contract
- **Triggers** — `UPDATE`, "update demolab", "pull the latest demolab", "get the newest engine",
  "upgrade demolab".
- **Gates** — step 2 is a hard stop gate: if the **major** version differs, stop and get
  explicit confirmation before bumping. A pre-1.0 lab (a `demolab-engine/` dir exists) routes
  to the migration section, which is itself gated on the user's go-ahead.
- **Report & apply** — the bump (step 3) is safe to drive; the migration section is
  diff-and-approve territory — show the pyproject edits before applying, and never touch the
  user's deps beyond adding `demolab-cli`.
