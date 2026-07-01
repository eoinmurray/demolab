# Contributing

How the pieces fit together and the conventions to follow when adding a tool command, a notebook, or a new tool. For a user-facing overview and run instructions, see [`README.md`](README.md).

## Toolchain

- **Python**: use `uv`. Never call `python` / `python3` directly. Dependencies are pinned in the root `pyproject.toml` / `uv.lock`; run scripts with `uv run python <script>` (e.g. `uv run python core/neuron/tool.py lif`). Run `uv sync` after pulling.
- **TypeScript / Node**: use `bun`. Never call `npm`, `pnpm`, `yarn`, or `node` directly. Install with `bun install`, run scripts with `bun run <script>`.

## The tool ↔ notebook contract

Each tool subcommand `<cmd>` writes a fixed set of files into `temp/<tool>/<cmd>/`, overwriting the previous run:

| File | Schema |
|------|--------|
| `config.json` | flat object of argparse args |
| `output.json` | flat object of metrics, command-specific field names |
| `manifest.json` | `{ headline_figure?: str, headline_video?: str, headline_metrics: [str, …] }` — declares what the docs site should surface |
| `output.log` | timestamped log lines |
| `run.sh` | executable shell script that re-invokes the tool with the same args |
| `<cmd>.png` / `<cmd>.mp4` | the canonical figure or video for the command (the authoritative pointer is `manifest.headline_figure` / `headline_video`) |
| `<cmd>.csv`, … | any additional data |

`write_output` in each tool's `tool.py` validates the manifest against the run before `manifest.json` is written: every key in `headline_metrics` must exist in `output.json`, and any declared `headline_figure` / `headline_video` must exist on disk, or the run fails. A manifest can therefore never lie about a run.

The notebook runner relies on this contract:

- Subcommand name maps 1:1 to the directory name under `temp/<tool>/`.
- The runner reads `manifest.json` to discover the headline asset and metrics — it does **not** hardcode metric field names or asset filenames. Adding a new surfaced metric is a one-file change in `tool.py` (extend the command's `headline_metrics` list).
- The runner only chooses *which commands* a notebook bundles (`COMMANDS` in the `nbNNN.py` runner).

`core` and `scripts` are **import-firewalled** (ruff `TID251`, via `core/ruff.toml` + `scripts/ruff.toml`): a runner reaches a tool by *running its CLI* (subprocess), never by `import`ing it, and tools never import runner code. They communicate only through the files above — so tools stay generic and every result carries its `config.json` / `manifest.json` / `run.sh` provenance.

### `numbers.json` aggregation

The runner aggregates each command's `config.json` + its headline metric fields into a single `numbers.json` in `artifacts/nbNNN/`:

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

A publisher then reads `numbers.json` (and the staged figure) to render prose, figures, and parameter tables.

## Publishing (the results layer)

`temp/<tool>/<cmd>/` is scratch — gitignored, overwritten every run. The runner copies the durable bits (the headline figure(s) and the aggregated `numbers.json`) into **`artifacts/<id>/`**, which *is* committed. That folder is the **publisher-neutral record**: the single place every publisher reads from, independent of Astro.

- **Astro (default).** Posts *import* the figure from the results layer — `import fig from '../artifacts/nbNNN/fig.png?url'`, then `<img src={fig} />`. Vite fingerprints the asset and applies the base path, so there are no hand-built URLs and nothing lives under `public/`. (`vite.server.fs.allow` in `astro.config.mjs` lets the dev server read the sibling `artifacts/`.)
- **Typst (shipped example: `nb004`).** `nb004.py` stages the same bundle, then compiles `nb004.typ` to a PDF via the `typst` package. The document reads `numbers.json` natively — `json("/artifacts/nb004/numbers.json")` — and embeds the figure with `#image(...)`, compiled with `--root` set to the repo root. For print, save the figure as vector (`savefig(..., format="pdf")` or SVG).
- **Anything else.** Any format that can read an image and JSON can be a publisher: keep the tools and runners, swap the document and the build step.

CI only builds the Astro site (`bun run build`) — it does **not** run the notebooks. So `artifacts/` must be committed; that committed bundle, not the ephemeral `temp/`, is what actually reaches the published site.

## Authoring posts

Most figures are *generated* — a tool runs, matplotlib renders a `.png`, the runner copies it into the post. That's the path for anything that's the output of a computation.

For a **hand-built diagram** (a schematic, a geometric illustration — a figure that isn't a simulation result), draw it inline as **SVG** instead of shipping an image. Because posts are MDX/JSX you can make it parametric:

- **Parametric constants.** Put `export const a = 120`, `b = 160`, … at the top of the post and feed every coordinate from them; change one number and the whole figure redraws. No image file, no build step, and it scales crisply.
- **Expressions in attributes.** Every attribute takes a JS expression — `viewBox={`0 0 ${s} ${s}`}`, `points={`${a},0 ${s},${a} …`}`, `x={a/2}`. A `viewBox` makes the coordinate system resolution-independent; `width`/`height` just scale it.
- **Shared style via spread.** Hold text styling once in `export const label = {…}` and spread it into each `<text {...label}>`.

Rule of thumb: reach for a tool-generated PNG when the figure is *data*; reach for inline SVG when it's a *drawing*. For a figure the reader should *explore*, ship a client-side Astro component (see the in-browser playground component under `demolab-web/src/components/`).

## Adding a new notebook

1. Add a tool subcommand (or reuse existing ones) in the relevant `core/<tool>/tool.py`. Pass a `manifest` to `write_output` declaring the headline figure/video and metrics.
2. Create `scripts/nbNNN.py` modeled on an existing runner. Declare `COMMANDS` for the commands you want; the runner reads each command's `manifest.json` to know what to copy and surface.
   - A single-tool runner (e.g. `nb000.py`) uses bare command strings: `COMMANDS = ("lif", "net")`.
   - A multi-tool runner (e.g. `nb002.py`) uses `(tool, command)` pairs: `COMMANDS = (("mujoco", "cartpole"),)`, so one notebook can drive an arbitrary mix of tools.
3. Create `entries/nbNNN.mdx`. Frontmatter must satisfy the `notebooks` collection schema (`demolab-web/src/content.config.ts`): `title` and `date` are required; `description`, `collection`, and `status` are optional. Import each figure from the results layer (`import fig from '../artifacts/nbNNN/fig.png?url'`) and inline parameter values from `numbers.json` into plain markdown tables. (To publish a PDF instead of a web page, skip the `.mdx` and follow the Typst example in [Publishing](#publishing-the-results-layer).)
4. Run `uv run python scripts/nbNNN.py`.

### The `status` field

`status` tracks where a notebook sits in its lifecycle and renders as a badge on the listing pages and the post header. The values are the single source of truth in `demolab-web/src/config/status.ts`:

| Status | Meaning |
|--------|---------|
| `draft` | Ideas and context — prose-heavy, no trusted results yet; expect churn. |
| `building` | Distilled to the core claim; code and plots landing. |
| `revising` | Results exist; under review with changes in flight. |
| `final` | Reviewed and approved — ready to send. |

A notebook moves `draft → building → revising → final` and may move backward freely (a `final` entry can be reopened). The field is optional: an omitted `status` renders no badge, and an unknown value is a build-time error (validated against the enum in both `content.config.ts` and `normalizeStatus`). To add or change a status value, edit `config/status.ts` — the schema, badge, and listings all read from it.

## Adding a new tool

Each tool lives in its own directory under `core/` and writes its run artifacts under `temp/<tool>/<cmd>/`. The manifest contract is the same for all tools; a new tool just needs to write `config.json`, `output.json`, `manifest.json`, `output.log`, `run.sh`, plus the assets its manifest declares (`headline_figure` and/or `headline_video`).

Reuse the established pattern in an existing `tool.py`:

- `setup_run_dir(command, args)` creates the run directory, configures a per-command logger that writes both to `output.log` and stdout, dumps `config.json` (all argparse args except `func`), and writes an executable `run.sh` reproducer.
- `write_output(run_dir, metrics, manifest)` performs the manifest validation and writes `output.json` + `manifest.json` last.
- Subcommands are wired through `argparse` with `set_defaults(func=...)`; `main()` calls `args.func(args)`.

Note the two `write_output` variants differ by design: `neuron/tool.py` requires a `headline_figure`, while `mujoco/tool.py` makes both `headline_figure` and `headline_video` optional (`.get(...)`) to support video-only runs. Same contract, generalized.

> The Streamlit playground (`core/playground/app.py`) is an interactive demo and intentionally does **not** follow the manifest contract — it produces no artifacts and is not part of the notebook pipeline.

## The feature catalog (upstream maintainers)

This repo is the upstream **reference** that downstream repos draw ideas from. They don't copy your files — their agents reimplement the features they want, their own way, using this repo as reference (see the **Updating the framework** runbook in [`CLAUDE.md`](CLAUDE.md)). So [`CHANGELOG.md`](CHANGELOG.md) is a **feature catalog**, and each entry has one job: describe a feature well enough that someone else's agent can rebuild it from the description plus your code.

Whenever you add or change a reusable **framework capability** (the Astro engine under `demolab-web/src/`, the contracts, the tool plumbing, CI), catalog it:

1. **Bump the version** with a new top entry in `CHANGELOG.md`. Use **major** for a feature that changes a contract others may have built on, **minor** for a new additive feature, **patch** for a small fix.
2. **Describe the feature by intent and behavior** — what it does, why, and where the reference implementation lives — not just which files moved. That's what a downstream agent reads to rebuild it natively.

Changes to **content** (notebooks, posts, tools, artifacts) aren't reusable features and don't belong in the catalog. If a change spans both, catalog only the reusable part.
