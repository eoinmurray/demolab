# Updating the lab framework from upstream

A runbook for pulling the latest framework into a repo created from the **demolab** template. Any coding agent can follow it; a human can run the same commands by hand. It's deliberately tool-agnostic — there's nothing Claude- or editor-specific here.

This repo mixes two kinds of files:

- **Framework** — the shared machinery maintained upstream (the Astro publishing engine, the contracts, CI, this runbook). You don't edit these; upstream pushes improvements to them.
- **Content** — everything you create (your notebooks, posts, simulators, artifacts).

Updating = overwriting **only the framework files** from upstream, leaving every content file untouched. It's one-way (upstream → here); your content is never pushed back upstream.

Upstream: `https://github.com/eoinmurray/demolab.git` (override with the `DEMOLAB_UPSTREAM` env var if set).

## The framework / content boundary

Overwrite from upstream (**framework** — this allowlist is the contract):

```
CHANGELOG.md
UPDATE.md
CLAUDE.md
CONTRIBUTORS.md
src/docs/astro.config.mjs
src/docs/tsconfig.json
src/docs/src/content.config.ts
src/docs/src/layouts/
src/docs/src/components/
src/docs/src/lib/
src/docs/src/config/
src/docs/src/pages/
src/docs/src/styles/
.github/workflows/
```

Never touch (**content** — you own these):

```
src/docs/src/content/      # your posts (notebooks + articles .mdx)
src/docs/public/           # your copied figures/videos + numbers.json
src/notebooks/             # your notebook runners
src/artifacts/             # your run outputs
src/simulators/            # your simulation code (see caveat below)
README.md                  # has your per-repo notebook list
```

## Procedure

1. **Confirm a clean tree.** Run `git status`. If there are uncommitted changes, commit or stash them first — the sync stages files and you don't want it tangled with work in progress.

2. **Fetch upstream** (default ref `main`, or a tag/branch you name):
   ```sh
   git fetch "${DEMOLAB_UPSTREAM:-https://github.com/eoinmurray/demolab.git}" main
   ```

3. **Compare versions.** The framework version is the top `## [x.y.z]` heading in `CHANGELOG.md`.
   - Local: read the top version from `CHANGELOG.md`.
   - Upstream: `git show FETCH_HEAD:CHANGELOG.md` and read its top version.
   - If they're **equal**, the framework is already current — stop; don't run the checkout.
   - If local is **behind**, read the changelog entries strictly between the two versions to see what the update brings. Note every **Manual step** and breaking (major-version) entry — those are the parts the file sync can't do for you. Decide whether to proceed before touching files.

4. **Overwrite only the framework allowlist** from the fetched commit (this includes `CHANGELOG.md`, so the local version advances to match upstream):
   ```sh
   git checkout FETCH_HEAD -- \
     CHANGELOG.md UPDATE.md CLAUDE.md CONTRIBUTORS.md \
     src/docs/astro.config.mjs src/docs/tsconfig.json src/docs/src/content.config.ts \
     src/docs/src/layouts src/docs/src/components src/docs/src/lib \
     src/docs/src/config src/docs/src/pages src/docs/src/styles \
     .github/workflows
   ```
   (Skip any path that doesn't exist upstream rather than failing the whole command.)

5. **Review what changed.** Run `git status` and `git --no-pager diff --staged --stat`, and tie the moved files back to the changelog entries from step 3.

6. **Reconcile dependencies if they changed:**
   - If `src/docs/package.json` differs upstream, `package.json`/`bun.lock` are deliberately *not* auto-overwritten (you may have added deps). Merge the new entries by hand, then `cd src/docs && bun install`.
   - If `pyproject.toml` changed upstream, same: merge new deps by hand, then `uv sync`.

7. **Commit.** Use a message that records the version jump, e.g. `git commit -m "Update lab framework to v0.3.0"`.

## Simulator plumbing caveat

`src/simulators/` is content (your own sims), but each `cli.py` carries a copy of the shared contract helpers `setup_run_dir` and `write_output`. If upstream changed those helpers, port the change into your `cli.py` files by hand — update *only* those two functions, preserving all of your simulation code. Diff the upstream `src/simulators/neuron/cli.py` against yours to see the canonical version. If nothing upstream touched those helpers, leave `src/simulators/` alone.

## Notes

- `git checkout FETCH_HEAD -- <paths>` adds and updates files but does **not** delete files that were removed upstream. If a framework file was deleted upstream, remove it locally by hand.
- `UPDATE.md` is itself framework, so an update can change this procedure. Re-read it after a sync before running another update.
