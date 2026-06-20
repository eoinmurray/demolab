# Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Dependencies are pinned in the root `pyproject.toml` / `uv.lock`; run scripts with `uv run python <script>` (e.g. `uv run python src/clis/neuron_cli/cli.py lif`). Use `uv sync` after pulling.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.

# Project layout

See `README.md` for the CLI ↔ notebook contract, the artifacts directory layout, and the procedure for adding a new notebook.

# Getting started

When the user asks **"how do I get started"** (or "help me set up", "onboard me", "walk me through this repo"), follow `GETTING_STARTED.md` as an **interactive** runbook: set up the toolchain, run the demo notebook so they see the loop work, then guide them through scaffolding their own first notebook, and help them publish. Drive it one step at a time — run the commands, verify each works, and confirm before moving on; don't dump the whole guide at once.

# Migrating existing code

When the user asks to **"migrate my code"** (or "import my repo", "bring my existing code in"), follow `MIGRATING.md`: inventory their existing repo, bring experiments across **one at a time**, and **wrap rather than rewrite** — the new CLI command imports and calls their existing functions, then publishes via a notebook runner + post per the contract in `CONTRIBUTORS.md`. Merge their dependencies into the root `pyproject.toml`. Verify each run end to end.

# Updating the framework

When the user asks to **"update demolab"** (or "update from upstream", "pull the latest demolab features"), follow the runbook in `UPDATE.md`. Updating is **not** a file copy: upstream demolab is a reference/menu of features (its `CHANGELOG.md`), and the job is to review what's new, let the user pick features, and reimplement the chosen ones *in this repo's own conventions* using upstream only as reference — never overwriting the user's work. Read `UPDATE.md` and follow its steps.
