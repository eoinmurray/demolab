# demolab

A small lab notebook system: a Python CLI runs numerical experiments, each run drops a self-contained directory of artifacts, and an Astro static site publishes a post for each notebook with the figures, the configuration, and the headline numbers.

```
src/
├── clis/         ← Python CLIs (one tool per subdirectory)
├── notebooks/    ← Per-notebook runners (shell out to the CLIs)
├── artifacts/    ← Per-run CLI outputs (.gitignored)
└── docs/         ← Astro site (posts + assets)
```

## New here? Start with your agent

This repo is built to be operated by a human **and** a coding agent (Claude Code, Cursor, aider, …). The fastest way in is to fork it, open it in your agent, and say:

- **"how do I get started"** → it runs the interactive [`GETTING_STARTED.md`](GETTING_STARTED.md) flow: sets up the toolchain, runs the demo, and helps you publish your own first notebook.
- **"migrate my code"** → it follows [`MIGRATING.md`](MIGRATING.md) to import an existing repo — bringing your experiments across one at a time, wrapping your code rather than rewriting it.

Both guides are plain runbooks — you can also follow them by hand.

## Layout

```
src/clis/neuron_cli/cli.py                  CLI entry point (subcommands: lif, net)
src/notebooks/nbNNN.py                        Notebook runner (shells out to the CLI)

src/artifacts/<tool>/<cmd>/                   Self-contained run directory
    config.json                               argparse args
    output.json                               metrics
    output.log                                timestamped log
    run.sh                                    reproduce: rerun the CLI with same args
    <cmd>.png, <cmd>.csv, …                   data + figures

src/docs/                                     Astro site
    src/docs/content/articles/arNNN.mdx            article (aggregates knowledge from notebooks)
    src/docs/content/notebooks/nbNNN.mdx           post (imports numbers.json)
    public/notebooks/nbNNN/                   PNGs + numbers.json
```

## Running

All Python dependencies (`numpy`, `matplotlib`, `mujoco`, `imageio[ffmpeg]`, `sh`) are pinned in the root `pyproject.toml` / `uv.lock`. First time on a clone:

```sh
uv sync
```

Then every CLI and notebook runner is invoked with `uv run python …` (the project's `.venv`, locked versions).

Run a single CLI command:

```sh
uv run python src/clis/neuron_cli/cli.py lif
uv run python src/clis/neuron_cli/cli.py net --n 200 --duration 500
```

Run a whole notebook (CLI commands + asset copy + `numbers.json`):

```sh
uv run python src/notebooks/nb000.py
```

Reproduce a specific past run:

```sh
src/artifacts/<tool>/lif/run.sh
```

## The docs site

```sh
cd src/docs
bun install        # first time only
bun run dev        # http://localhost:4321 (or pass -- --port 3001)
bun run build      # static output in dist/
```

Notebook posts live in `src/docs/content/notebooks/` and are picked up automatically by the `notebooks` content collection (schema in `src/docs/src/content.config.ts`). MDX is supported (math via remark-math/rehype-katex), so a post can `import` JSON or Astro components.

## CLI tools

Each CLI tool lives in its own directory under `src/clis/` and writes its run artifacts under `src/artifacts/<tool>/<cmd>/`.

- **`neuron`** — numpy/matplotlib integrate-and-fire neuron and network simulations (`lif`, `net`, `eif`, `enet`).
- **`mujoco_cli`** — MuJoCo physics demos rendered to mp4 (`cartpole`, `double_pendulum`).

## Staying up to date

This repo is a **template** — start your own by forking this repo on GitHub (or `gh repo create --template eoinmurray/demolab`), then make it yours: add notebooks, posts, and CLIs.

Upstream demolab keeps gaining features, but it's a **source of ideas**, not a framework you mirror. To bring one into your repo, follow [`UPDATE.md`](UPDATE.md): your coding agent reviews what's new upstream (its `CHANGELOG.md` is the menu) and implements the features you pick *your way* — adapted to your own conventions, using the upstream code only as reference. Nothing is overwritten; you adopt, adapt, or skip per feature, so your repo can diverge freely and still cherry-pick later ideas.

## Contributing

The CLI ↔ notebook manifest contract, the `numbers.json` schema, and the procedures for adding a notebook or a new CLI tool live in [`CONTRIBUTORS.md`](CONTRIBUTORS.md).
