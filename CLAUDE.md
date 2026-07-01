# Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Dependencies are pinned in the root `pyproject.toml` / `uv.lock`; run scripts with `uv run python <script>` (e.g. `uv run python src/tools/neuron/tool.py lif`). Use `uv sync` after pulling.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.

# Repo layout — the framework/content firewall

Two zones. Keep them straight:

- **Framework** (demolab itself — never deleted when clearing demo content): this file, `README.md`, `CONTRIBUTORS.md`, `CHANGELOG.md`, the Astro engine under `src/docs/src/`, and build config. The operating manual lives *here*, so onboarding survives any deletion of example content.
- **Example / user content** (100% the user's — freely deletable and replaceable): `src/tools/*`, `src/notebooks/*`, `src/docs/content/*`, `src/artifacts/*`, `src/docs/public/notebooks/*`.

The contract for `src/tools` ↔ `src/notebooks` ↔ posts, the `numbers.json` schema, and how to add a tool/notebook are in `CONTRIBUTORS.md`.

The four runbooks below are the source of truth for operating the system. Each fires on the trigger phrases in its heading. Drive them **interactively**: run each step's commands yourself, show the result, confirm before moving on — don't dump a whole runbook at the user at once.

# Runbook: Getting started

Triggers: **"how do I get started"**, "help me set up", "onboard me", "walk me through this repo". Goal: demo running locally, the user understands the loop, and they've published their *own* first notebook.

0. **Prereqs.** Check `uv --version` and `bun --version`. If either is missing, give the one-line install for their platform and stop.
1. **Install.** `uv sync`, then `cd src/docs && bun install`.
2. **See the loop work.** `uv run python src/notebooks/nb000.py`, then start `bun run dev` in the background. Open the nb000 post at <http://localhost:3000> and explain in a sentence or two how the artifact under `src/artifacts/neuron/` became that page.
3. **Brand it.** Set `PUBLIC_SITE_NAME` (header wordmark) and `PUBLIC_SITE_REPO_URL` (header link) via `src/docs/.env` or their defaults in `src/docs/src/layouts/Base.astro`. Per-page `<title>`s live in `src/docs/src/pages/*.astro` if the browser-tab title matters.
4. **Scaffold their first notebook** (the point of the whole thing). Ask what they want to compute — keep it small. Then, following `CONTRIBUTORS.md`:
   - Add a tool command in `src/tools/<tool>/tool.py` (new dir or a subcommand on an existing tool), modeled on `src/tools/neuron/tool.py` — copy `setup_run_dir`/`write_output`, write `config.json`/`output.json`/a figure, pass a `manifest` with the headline figure + metrics.
   - Create the runner `src/notebooks/nbNNN.py` (model `nb000.py` for one tool, `nb002.py` for a mix); declare `COMMANDS`.
   - Create the post `src/docs/content/notebooks/nbNNN.mdx` (frontmatter `title` + `date`; optional `description`/`collection`/`status`), inlining values from the generated `numbers.json`.
   - Run `uv run python src/notebooks/nbNNN.py` and open the new post with the user.
5. **Clear the shipped demo** — *only after step 4 works*, so a real example existed as a template. Remove the shipped set by id, and nothing else: tools `src/tools/{neuron,mujoco,playground}`; runners `src/notebooks/nb000.py`–`nb003.py` and posts `src/docs/content/notebooks/nb00*.mdx`; articles `src/docs/content/articles/{ar000,ar003,ar008}.mdx`; runs under `src/artifacts/`; copied assets under `src/docs/public/notebooks/`. **Never** delete the user's new notebook or anything in the framework zone.
6. **Publish.** In `src/docs/astro.config.mjs` set `site` to `https://<user>.github.io` and `base` to `/<repo>`. Enable Pages (*Settings → Pages → Source: GitHub Actions*). Commit and push `main`; confirm the Actions run succeeds.

# Runbook: Migrating existing code

Triggers: **"migrate my code"**, "import my repo", "bring my existing code in". Three principles the whole flow follows: **one experiment at a time**, **wrap don't rewrite** (the new `tool.py` is a thin adapter that imports and calls their functions — never reimplement their science), and **one environment** (their deps fold into the root `pyproject.toml`). Get one experiment publishing end to end before touching the next.

1. **Inventory.** Read their repo (local path or clone). List candidate experiments — each script/function that ends in a figure or a few numbers. With the user, pick the single simplest to migrate first.
2. **Bring their code in.** Installable package → `uv add <name>` (PyPI, or git/local-path dep) + `uv sync`, then `import` it. Loose scripts → copy only the modules the experiment needs next to `tool.py` or into a shared `src/<pkg>/`.
3. **Merge deps.** `uv add` only what the chosen experiment actually needs (never `pip install`); surface version conflicts and resolve with the user.
4. **Wrap as a tool command.** Create `src/tools/<tool>/tool.py` modeled on `neuron/tool.py`: copy `setup_run_dir`/`write_output` verbatim (adjust `ARTIFACTS_DIR` + logger), add an `argparse` subcommand for the experiment's params, and in the handler call `setup_run_dir` → **their function** → save the figure → `write_output` with a manifest. Keep it thin; if you're porting their math, stop and import instead. Verify `src/artifacts/<tool>/<cmd>/` has the full set.
5. **Runner + post.** As in Getting started steps 4. Confirm the published figure and numbers match their original code's output.
6. **Repeat** for the next experiment; stop when the ones that matter are done.

Notes: thread a `--seed` through anything random (see `neuron`'s `net` command); bring and run their relevant tests with `uv run`.

# Runbook: Embedding as a docs subfolder

Triggers: **"embed demolab as a docs site"**, "use this as a wiki subfolder", "drop this into my project as docs". The tree is path-portable (every tool/notebook resolves paths relative to its own file). Only *serving* and *deploying* need attention, and **serve config is env-driven — never edit source for it.**

1. **Place it.** Copy demolab degitted (no `.git`) into the host project, e.g. `wiki/`. Delete the copy's bundled `.github/workflows/deploy.yml` (it assumes demolab is the repo root).
2. **Run from inside the subfolder** so `uv`/`bun` resolve demolab's manifests: `cd wiki && uv sync && cd src/docs && bun install && bun run dev`.
3. **Configure serve + brand via env vars only:** `PUBLIC_SITE_URL` (origin), `PUBLIC_BASE_PATH` (`/<repo>` for a project Pages site), `PUBLIC_SITE_NAME`, `PUBLIC_SITE_REPO_URL`. Local dev → `wiki/src/docs/.env`; deploys → the workflow env.
4. **Deploy from the HOST repo.** Copy `.github/workflows/deploy-wiki.yml.example` into the *host* repo's `.github/workflows/`, set the `env` values (`WIKI_DOCS`, `PUBLIC_SITE_URL`, `PUBLIC_BASE_PATH`), and enable Pages on the host (*Settings → Pages → Source: GitHub Actions*). It rebuilds only when `wiki/**` changes. Push host `main`.

Notes: one Pages site per repo — if the host already uses Pages, deploy the wiki from a dedicated repo. Per-page `<title>`s still say "demolab" (literal strings); change them if it matters.

# Runbook: Updating the framework

Triggers: **"update demolab"**, "update from upstream", "pull the latest demolab features". Updating is **not** a file copy. Upstream demolab is a **menu of ideas and a reference implementation**, not a canonical framework to mirror — adopt, adapt, or skip each feature, one at a time, reimplemented *in this repo's own conventions*. Never overwrite the user's work.

1. **Find where you last looked.** Read a last-reviewed marker if present (e.g. `.demolab-upstream`); otherwise treat the whole catalog as new.
2. **Fetch upstream read-only** (never touches the working tree): `git fetch "${DEMOLAB_UPSTREAM:-https://github.com/eoinmurray/demolab.git}" main`. Read its catalog with `git show FETCH_HEAD:CHANGELOG.md`, and any reference file the same way (e.g. `git show FETCH_HEAD:src/docs/src/components/EntryList.astro`).
3. **Present the menu.** List changelog entries newer than the last-reviewed version, summarize each in plain terms, and ask which the user wants.
4. **Adopt each chosen feature, this repo's way.** Study the upstream code as *reference* (intent, not diff), implement the equivalent in this repo's conventions/naming/structure, reuse what's already here. If this repo already has its own take, reconcile or skip — never clobber without asking. Verify (run the dev server / the relevant tool).
5. **Record.** Update the last-reviewed marker, commit describing which features were adopted and how they differ, and leave skipped ones on the menu.

Where upstream features tend to live (for reference, not copying): `src/docs/src/` (engine), `CONTRIBUTORS.md` (contracts), `src/tools/*/tool.py` (the `setup_run_dir`/`write_output` plumbing), `.github/workflows/` (CI). Purely the user's, never sourced upstream: `src/notebooks/`, `src/docs/content/`, `src/artifacts/`, `src/docs/public/`, and their own tools.
