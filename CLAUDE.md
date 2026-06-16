# Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Dependencies are pinned in the root `pyproject.toml` / `uv.lock`; run scripts with `uv run python <script>` (e.g. `uv run python src/simulators/neuron/cli.py lif`). Use `uv sync` after pulling.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.

# Project layout

See `README.md` for the CLI ↔ notebook contract, the artifacts directory layout, and the procedure for adding a new notebook.

# Updating the framework

When the user asks to **"update demolab"** (or "update from upstream", "pull the latest demolab features"), follow the runbook in `UPDATE.md`. Updating is **not** a file copy: upstream demolab is a reference/menu of features (its `CHANGELOG.md`), and the job is to review what's new, let the user pick features, and reimplement the chosen ones *in this repo's own conventions* using upstream only as reference — never overwriting the user's work. Read `UPDATE.md` and follow its steps.
