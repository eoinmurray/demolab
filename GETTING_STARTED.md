# Getting started

This guide is meant to be run **with a coding agent**. Open the repo in Claude Code (or any agent) and say *"how do I get started"* — it will walk you through these steps interactively, running the commands with you and checking each one works. You can also just follow them by hand.

By the end you'll have the demo site running locally, understand the core loop, and have published **your own first notebook**.

> **Agent:** drive this as an interactive session. Run each step's commands yourself, show the user the result, and confirm before moving on. Don't dump the whole guide at them — take it one step at a time.

## 0. Prerequisites

- A fork of this repo, cloned locally (see the README for the fork link).
- [`uv`](https://docs.astral.sh/uv/) for Python and [`bun`](https://bun.sh/) for the site. The toolchain rule: **never** call `python`/`pip`/`npm` directly — always `uv` and `bun` (see `CLAUDE.md`).

> **Agent:** check `uv --version` and `bun --version` first. If either is missing, stop and give the user the one-line install command for their platform before continuing.

## 1. Orient

This repo is a lab notebook system with one opinionated loop:

> a **CLI** runs an experiment and drops a directory of artifacts → a **notebook runner** bundles those artifacts → an **Astro site** publishes a post for each notebook.

You operate it together with your agent. The full contract is in `CONTRIBUTORS.md`; you don't need it yet.

## 2. Install and verify

```sh
uv sync
cd src/docs && bun install && cd ../..
```

> **Agent:** run both, confirm they succeed.

## 3. See the loop work

Run an existing notebook end to end, then start the site and look at the result:

```sh
uv run python src/notebooks/nb000.py
cd src/docs && bun run dev
```

Open <http://localhost:4321/demolab> and click into **nb000**. You're looking at a post generated from the CLI run you just executed — the figure and the numbers in the prose came straight out of `src/artifacts/neuron_cli/` via `src/docs/public/notebooks/nb000/`.

> **Agent:** start the dev server in the background so the session can continue. Point the user at the nb000 post and explain, in one or two sentences, how the artifact they just generated became that page.

## 4. Make it yours — scaffold your first notebook

This is the point of the workflow: go from an idea to a published result in one session.

> **Agent:** ask the user what they'd like to compute or simulate — keep it small (a function to plot, a tiny simulation, a parameter sweep). Then:
>
> 1. **Add a CLI command** for it. Either add a subcommand to an existing CLI under `src/clis/<tool>_cli/cli.py`, or create a new tool directory. Follow "Adding a new notebook" / "Adding a new CLI tool" in `CONTRIBUTORS.md` exactly — write `config.json`, `output.json`, a figure, and pass a `manifest` to `write_output` declaring the headline figure and metrics. Model it on `src/clis/neuron_cli/cli.py`.
> 2. **Create the notebook runner** `src/notebooks/nbNNN.py` (next free number), modeled on `nb000.py` (single tool) or `nb002.py` (mix of tools). Declare its `COMMANDS`.
> 3. **Create the post** `src/docs/content/notebooks/nbNNN.mdx` — frontmatter `title` + `date` (and optional `description`, `collection`, `status`). Inline values from the generated `numbers.json` into a short prose explanation + a parameter table.
> 4. **Run it:** `uv run python src/notebooks/nbNNN.py`, then refresh the site and open the new post with the user.
>
> Keep the first one minimal — the goal is for the user to watch their own idea become a published page, not to build something elaborate.

## 5. Publish it

The site deploys to GitHub Pages automatically on every push to `main` (`.github/workflows/deploy.yml`). Two one-time steps for your fork:

1. **Point the site at your fork.** In `src/docs/astro.config.mjs`, set `site` to `https://<your-username>.github.io` and `base` to `/<your-repo-name>`.
2. **Enable Pages.** On GitHub: *Settings → Pages → Build and deployment → Source: GitHub Actions*.

Then commit and push to `main`. Your notebook goes live at `https://<your-username>.github.io/<your-repo-name>/`.

> **Agent:** make the `astro.config.mjs` edit for the user (ask for their username/repo), then walk them through enabling Pages and pushing. Confirm the Actions run succeeds.

## 6. Where to go next

- `CONTRIBUTORS.md` — the CLI ↔ notebook contract and the procedures for adding notebooks and tools.
- `MIGRATING.md` — bring an existing script or simulation into this structure.
- `UPDATING.md` — pull new feature *ideas* from upstream demolab and have your agent reimplement the ones you want, your way.
