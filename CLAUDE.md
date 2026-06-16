# Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Dependencies are pinned in the root `pyproject.toml` / `uv.lock`; run scripts with `uv run python <script>` (e.g. `uv run python src/simulators/neuron/cli.py lif`). Use `uv sync` after pulling.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.

# Project layout

See `README.md` for the CLI ↔ notebook contract, the artifacts directory layout, and the procedure for adding a new notebook.

# Updating the framework

When the user asks to **"update demolab"** (or "update the framework", "sync from upstream", "pull the latest demolab"), follow the runbook in `UPDATE.md` to the letter. It is the source of truth: it pulls the latest framework files from upstream, leaves the user's content untouched, and is version-driven via `CHANGELOG.md`. Don't improvise the sync — read `UPDATE.md` and execute its steps.
