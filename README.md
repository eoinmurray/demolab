# demolab

A small lab notebook system: a Python CLI runs numerical experiments, each run drops a self-contained directory of artifacts, and an Astro static site publishes a post for each notebook with the figures, the configuration, and the headline numbers.

```
src/
├── simulators/   ← Python CLIs (one tool per subdirectory)
├── notebooks/    ← Per-notebook runners (shell out to the CLIs)
├── artifacts/    ← Per-run CLI outputs
└── docs/         ← Astro site (posts + assets)
```

## Layout

```
src/simulators/neuron/cli.py                              CLI entry point (subcommands: lif, net)
src/notebooks/nbNNN.py                  Notebook runner (shells out to the CLI)

src/artifacts/<tool>/<cmd>/                    Self-contained run directory
    config.json                               argparse args
    output.json                               metrics
    output.log                                timestamped log
    run.sh                                    reproduce: rerun the CLI with same args
    <cmd>.png, <cmd>.csv, …                   data + figures

src/docs/                                   Astro site
    src/content/articles/arNNN.mdx            article (aggregates knowledge from notebooks)
    src/content/notebooks/nbNNN.mdx           post (imports numbers.json)
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
uv run python src/simulators/neuron/cli.py lif
uv run python src/simulators/neuron/cli.py net --n 200 --duration 500
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

Notebook posts live in `src/docs/src/content/notebooks/` and are picked up automatically by the `notebooks` content collection (schema in `src/docs/src/content.config.ts`). MDX is supported (math via remark-math/rehype-katex), so a post can `import` JSON or Astro components.

## CLI tools

Each CLI tool lives in its own directory under `src/simulators/` and writes its run artifacts under `src/artifacts/<tool>/<cmd>/`.

- **`neuron`** — numpy/matplotlib integrate-and-fire neuron and network simulations (`lif`, `net`, `eif`, `enet`).
- **`mujoco_lab`** — MuJoCo physics demos rendered to mp4 (`cartpole`, `double_pendulum`).

## Staying up to date

This repo is a **template** — start your own from it with GitHub's *“Use this template”* button (or `gh repo create --template eoinmurray/demolab`), then make it yours: add notebooks, posts, and simulators.

The shared *framework* (the Astro publishing engine under `src/docs/src/`, the contracts in `CONTRIBUTORS.md`, and CI) keeps improving upstream. To pull the latest framework without disturbing your own content, follow [`UPDATE.md`](UPDATE.md) — a tool-agnostic runbook any coding agent or a human can run (point your agent at it, or run the `git` commands by hand). It overwrites only framework files and leaves your notebooks, posts, and artifacts untouched.

## Contributing

The CLI ↔ notebook manifest contract, the `numbers.json` schema, and the procedures for adding a notebook or a new CLI tool live in [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

## Existing notebooks

- **nb000** — A single LIF neuron's voltage trace under tonic input, then a recurrent network of 200 LIF neurons (raster + population input current). Drives the `lif` and `net` CLI commands.
- **nb001** — Same setup as nb000 but with EIF neurons (`eif`, `enet`).
- **nb002** — A passive MuJoCo cartpole released from a small offset, rendered to mp4 via `mujoco_lab cartpole`.
- **nb003** — Two double pendulums released side-by-side with $10^{-3}$-rad initial perturbation; tip separation crosses 0.1 m around $t \approx 3\,\text{s}$. Drives `mujoco_lab double_pendulum`.
