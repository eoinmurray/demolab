# Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Pass dependencies inline with `--with`, e.g. `uv run --with numpy --with matplotlib python src/simulator/cli.py lif`.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.

# Project layout

See `README.md` for the CLI ↔ notebook contract, the artifacts directory layout, and the procedure for adding a new notebook.
