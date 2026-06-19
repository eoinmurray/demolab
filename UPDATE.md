# Adopting features from upstream

This repo started from the **demolab** template, but it's *yours*. Upstream demolab is a **source of ideas and a reference implementation** — not a canonical framework you have to mirror. You've made your own choices about styling, structure, and which features matter; here, those choices win.

So "updating" is **not** a file copy. It's: see what's new upstream, pick the ideas you want, and have your coding agent implement them *your way*, using the upstream code as reference. Adopt a feature wholesale, adapt it, or skip it — your call, one feature at a time.

This runbook is tool-agnostic: any coding agent can follow it, or a human can do it by hand. Upstream: `https://github.com/eoinmurray/demolab.git` (override with the `DEMOLAB_UPSTREAM` env var).

## The model

- **Upstream is inspiration, not law.** Its `CHANGELOG.md` is a catalog of features, each with a version — read it as a menu.
- **Your repo decides how things are done here.** When you adopt a feature it should read like *your* code — your conventions, your file layout, your components — not a transplant.
- **Nothing is forced or overwritten.** Your agent reads upstream files as reference and writes fresh code into your repo. It never blindly clobbers your work.

## Where upstream features tend to live

Handy when reading the reference — these are *where to look*, not files to copy:

- `src/docs/src/` — the Astro publishing engine (layouts, components, pages, styles, config, content schema)
- `CONTRIBUTORS.md` — the CLI ↔ notebook contracts
- `src/clis/*/cli.py` — the shared run/manifest plumbing (`setup_run_dir`, `write_output`)
- `.github/workflows/` — CI

Purely yours, never sourced from upstream: your notebooks (`src/notebooks/`, `src/docs/content/`), your artifacts (`src/artifacts/`, `src/docs/public/`), and your own CLIs.

## Procedure (your agent runs this)

1. **Find where you last looked.** If your repo records a last-reviewed upstream version (e.g. a `.demolab-upstream` file), read it. Otherwise treat the whole catalog as new.

2. **Fetch upstream as read-only reference** — this never touches your working tree:
   ```sh
   git fetch "${DEMOLAB_UPSTREAM:-https://github.com/eoinmurray/demolab.git}" main
   ```
   Read its catalog with `git show FETCH_HEAD:CHANGELOG.md`, and any reference file the same way, e.g. `git show FETCH_HEAD:src/docs/src/components/EntryList.astro`.

3. **Present the menu.** List the changelog entries newer than your last-reviewed version. Summarize each feature in plain terms — what it does and why — so the user can choose. Ask which they want.

4. **Adopt each chosen feature, your way:**
   - Study the upstream implementation as *reference* — understand the intent, not just the diff.
   - Implement the equivalent in this repo, adapted to its conventions, naming, structure, and styling. Reuse what's already here.
   - If this repo already has its own take on the feature (maybe different, maybe better), reconcile or skip — never overwrite the user's version without asking.
   - Verify it works here (run the dev server / the relevant CLI).

5. **Record what you did.** Update the last-reviewed marker to the upstream version you reviewed, so next time only newer features show. Commit with a message describing which features you adopted and how they differ from upstream. Skipped features stay on the menu.

## Notes

- Adoption can be partial. "I like the idea but not the implementation" is a valid outcome — take the idea.
- Some upstream features won't fit your repo at all. Declining is normal; it's a menu, not a checklist.
- Because nothing is copied wholesale, your repo can diverge from upstream as much as you like and still cherry-pick future ideas.
