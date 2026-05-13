# demolab

A small lab notebook system: a Python CLI runs numerical experiments, each run drops a self-contained directory of artifacts, and an Astro static site publishes a post for each notebook with the figures, the configuration, and the headline numbers.

```
src/
├── lab/          ← Python: CLI + notebook runners
├── artifacts/    ← Per-run CLI outputs
└── docs/         ← Astro site (posts + assets)
```

## Layout

```
src/lab/cli.py                              CLI entry point (subcommands: lif, net)
src/lab/notebooks/nbNNN.py                  Notebook runner (shells out to the CLI)

src/artifacts/cli/<cmd>/                    Self-contained run directory
    config.json                               argparse args
    output.json                               metrics
    output.log                                timestamped log
    run.sh                                    reproduce: rerun the CLI with same args
    <cmd>.png, <cmd>.csv, …                   data + figures

src/docs/                                   Astro site
    src/content/notebooks/nbNNN.mdx           post (imports numbers.json)
    public/notebooks/nbNNN/                   PNGs + numbers.json
    src/components/ParameterTable.astro       reusable table component
```

## Running

The CLI needs `numpy` and `matplotlib`; the notebook runner additionally needs `sh`. Everything is invoked through `uv run` so no global env is required.

Run a single CLI command:

```sh
uv run --with numpy --with matplotlib python src/lab/cli.py lif
uv run --with numpy --with matplotlib python src/lab/cli.py net --n 200 --duration 500
```

Run a whole notebook (CLI commands + asset copy + `numbers.json`):

```sh
uv run --with sh python src/lab/notebooks/nb000.py
```

Reproduce a specific past run:

```sh
src/artifacts/cli/lif/run.sh
```

## The docs site

```sh
cd src/docs
bun install        # first time only
bun run dev        # http://localhost:4321 (or pass -- --port 3001)
bun run build      # static output in dist/
```

Notebook posts live in `src/docs/src/content/notebooks/` and are picked up automatically by the `notebooks` content collection (schema in `src/docs/src/content.config.ts`). MDX is supported (math via remark-math/rehype-katex), so a post can `import` JSON or Astro components.

## The CLI ↔ notebook contract

Each CLI subcommand `<cmd>` writes a fixed set of files into `src/artifacts/cli/<cmd>/`, overwriting the previous run:

| File | Schema |
|------|--------|
| `config.json` | flat object of argparse args |
| `output.json` | flat object of metrics, command-specific field names |
| `manifest.json` | `{ headline_figure: str, headline_metrics: [str, …] }` — declares what the docs site should surface |
| `output.log` | timestamped log lines |
| `run.sh` | executable shell script that re-invokes the CLI with the same args |
| `<cmd>.png` | the canonical figure for the command (by convention; the authoritative pointer is `manifest.headline_figure`) |
| `<cmd>.csv`, … | any additional data |

`write_output` in `cli.py` validates the manifest against the run: every key in `headline_metrics` must exist in `output.json`, and `headline_figure` must exist on disk, or the run fails before `manifest.json` is written.

The notebook runner relies on this contract:

- Subcommand name maps 1:1 to the directory name under `src/artifacts/cli/`.
- The runner reads `manifest.json` to discover the headline figure and metrics — it does **not** hardcode metric field names. Adding a new surfaced metric is a one-file change in `cli.py` (extend the command's `headline_metrics` list).
- The runner only chooses *which commands* a notebook bundles (`COMMANDS` in `nb000.py`).

The runner aggregates each command's `config.json` + the metric fields into a single `numbers.json` in `src/docs/public/notebooks/nbNNN/`:

```json
{
  "lif": {
    "config": { "current": 2.5, "duration": 100.0, "dt": 0.1, ... },
    "firing_rate_hz": 90.0
  },
  "net": {
    "config": { "n": 200, "duration": 500.0, ... },
    "mean_firing_rate_hz": 104.2,
    "min_firing_rate_hz": 56.0,
    "max_firing_rate_hz": 148.0
  }
}
```

The post then imports this file and renders prose + figures + parameter tables.

## Adding a new notebook

1. Add a CLI subcommand (or reuse existing ones) in `src/lab/cli.py`. Pass a `manifest` to `write_output` declaring the headline figure and metrics.
2. Create `src/lab/notebooks/nbNNN.py` modeled on `nb000.py`. Declare `COMMANDS = (...)` for the commands you want; the runner reads each command's `manifest.json` to know what to copy and surface.
3. Create `src/docs/src/content/notebooks/nbNNN.mdx`. Frontmatter: `title`, `date`, optional `description`. Import `numbers.json` from `../../../public/notebooks/nbNNN/numbers.json` and use the `ParameterTable` component to render values.
4. Run `uv run --with sh python src/lab/notebooks/nbNNN.py`.

## Existing notebooks

- **nb000** — A single LIF neuron's voltage trace under tonic input, then a recurrent network of 200 LIF neurons (raster + population input current). Drives the `lif` and `net` CLI commands.
