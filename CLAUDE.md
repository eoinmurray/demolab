# Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Pass dependencies inline with `--with`, e.g. `uv run --with numpy --with matplotlib python src/lab/cli.py lif`.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.
