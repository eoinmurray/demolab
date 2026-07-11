# RULES — demolab's conventions

The single source of truth for how a demolab lab is structured and the conventions to
follow — principles *and* the tool ↔ experiment contract. It ships inside the `demolab-cli`
package (`demolab docs RULES` prints this file's path), so it is always in step with the
installed engine; the lab-root `AGENTS.md` / `CLAUDE.md` are thin pointers to it.

Rules are numbered `§<section>.<rule>` so other docs (e.g. the *Doctor the repo* runbook)
can cite them precisely. Terms (tool, experiment, deck, collection, provenance…) are
defined in [`GLOSSARY.md`](GLOSSARY.md).

## 1. Toolchain

**1.1 — Python via `uv`.** Never call `python` / `python3` directly. Deps are pinned in the root `pyproject.toml` / `uv.lock`; run scripts with `uv run python <script>` (e.g. `uv run python tools/neuron/tool.py lif`); `uv sync` after pulling.

**1.2 — Publishing via `typst`.** Use the `typst` CLI (an installed prerequisite, alongside `uv`). It compiles the site + PDFs (`demolab build` / `demolab dev`); the bundle build passes `--features bundle,html` (experimental, deliberately used here). No Node/`bun` — demolab publishes entirely with Typst.

**1.3 — Prefer `demolab`.** Common commands are exposed through the `demolab` CLI — prefer `demolab <name>` (run `demolab` to list them). To check the toolchain *and* that the repo obeys these conventions, run the *Doctor the repo* runbook (*"doctor the repo"*).

**1.4 — Python is the default, not a requirement.** The contract (§4) is *file-based and language-neutral* — a tool is reached by running its CLI (a subprocess), never by importing it, and speaks only through files; Typst publishes from `numbers.json` + PNGs regardless of what produced them. To move the tool layer to MATLAB / R / Julia / Octave, follow the *Migrating the stack* runbook ([MIGRATE-STACK.md](../runbooks/MIGRATE-STACK.md)).

## 2. Commits

**2.1 — Human-only authorship.** Author every commit as the human only. **Never** record an agent as author or co-author: no `Co-Authored-By:` trailer naming Claude or any AI, no agent name in the author/committer fields, no "🤖 Generated with …" line. The history reads as the human's own work.

## 3. Repo layout — the framework/content firewall

The concrete annotated file tree is in [`STRUCTURE.md`](STRUCTURE.md); this section is the *why* — which zone each path belongs to and how it updates.

**3.1 — The engine is the package** (pure upstream; never on disk to edit): the `demolab-cli` package in site-packages holds the build code + CLI, the Typst templates (`main.typ`, `lib.typ`, web assets), the runbooks and guides (this file included — reached via `demolab docs`), and the scaffold (`skeleton/` — the bare structure `demolab scaffold` lays down; `demo/` — the source of the published docs site; `starters/` — first-experiment references you model on, never overlay), versioned as one unit (SemVer; `demolab version` prints it). A lab ships **content-only**. Updating is a dependency bump (`demolab docs UPDATE`), and `uv.lock` pins the engine version for reproducibility.

**3.2 — Machine-managed staging** (gitignored, owned by the CLI — never hand-edit): `.demolab/` at the lab root holds the few engine files Typst must read from inside the lab tree (`lib.typ`, the web assets, a `VERSION` stamp); every build refreshes it when the installed engine version changes. `temp/bundle/` holds the staged bundle root (`main.typ`) plus build scratch. Local edits to either are overwritten without warning — a customisation that seems to need them is a missing config knob (see 3.3, or propose it upstream).

**3.3 — Your root overrides, optional** (root files the framework reads; never overwritten by updates): `demolab.yaml` (wordmark + PDF titles + collections — also the **lab marker**: the CLI finds the lab root by walking up to it, so don't delete it) and `HOUSESTYLE.local.md` (your house-style overrides, which extend or replace the default `HOUSESTYLE.md`; an agent reads it). Every key defaults ⇒ a minimal file is fine. The root stubs (`AGENTS.md`, `CLAUDE.md`, `README.md`, `pyproject.toml`, `.gitignore`, CI) are laid down once by `demolab init` and are yours from then on.

**3.4 — User content** (100% the user's — freely deletable and replaceable): `tools/*`, `experiments/*` (runners, plus `playground.py` — the Streamlit demo, exempt from the contract), `writings/*` (`.typ` writeups), `artifacts/*` (`data/` per-run figures + `numbers.json`, `pdfs/` compiled PDFs; `artifacts/site/` is a gitignored build), `temp/*` (regenerable scratch).

## 4. The tool ↔ experiment contract

**4.1 — Reuse is the bar.** A tool exists to hold *reusable* science — a model or solver run across more than one experiment, or the same one re-run with swept parameters. Using a tool is a choice, not a requirement: a genuine one-off can compute inline in its runner and stage its own `artifacts/data/expNNN/` directly; articles (`ar*`) use no tool at all. **Don't manufacture a tiny tool to satisfy the contract** — the CLI, manifest, tests, and import firewall earn their ceremony by being *shared*. Going inline trades away the manifest validation and easy unit-testing — fine for a throwaway; provenance is *not* lost, since an inline runner stamps it with `helpers/provenance.stamp` (§4.7). When reuse actually appears, **promote** the code into `tools/<tool>/tool.py` then and point the runner at its CLI — not in anticipation.

**4.2 — Tools emit data, not plots.** A tool writes the machine-readable data a figure is drawn *from* — the format is the author's choice (CSV, JSON/JSONL, `.npz`, Parquet, HDF5, whatever suits the science); drawing the figure is the runner's job. What matters is that the *data* is emitted, not a rendered plot, so the figure can be redrawn and the numbers are available. (The contract files themselves — `config.json`, `output.json`, `manifest.json`, `numbers.json` — are always JSON; only the figure-data format is open.) The one exception is a **rendering** (a physics video, `mujoco` → `.mp4`), which a tool *does* produce. `write_output` validates that a declared `headline_video` exists on disk and that every `headline_metrics` key is in `output.json` — so a manifest can never lie about a run.

**4.3 — The file set.** Each tool subcommand `<cmd>` writes a fixed set of files into `temp/<tool>/<cmd>/`, overwriting the previous run:

| File | Schema |
|------|--------|
| `config.json` | flat object of argparse args |
| `output.json` | flat object of metrics, command-specific field names |
| `manifest.json` | `{ headline_video?: str, headline_metrics: [str, …] }` |
| `output.log` | timestamped log lines |
| `run.sh` | executable script that re-invokes the tool with the same args |
| `<cmd>.csv` / `.json` / `.npz` / … | the run's data — the numbers a figure would be drawn from (author's choice of format) |
| `<cmd>.mp4` | *rendering tools only* — the canonical video (`manifest.headline_video`) |

**4.4 — The runner reads, doesn't hardcode.** Subcommand name maps 1:1 to the directory under `temp/<tool>/`. The runner reads `manifest.json` to discover the headline metrics (and a headline video, if any) — it never hardcodes metric field names. It *renders* the figures itself from the tool's data (whatever format the tool wrote). It only chooses *which* commands an experiment bundles (`COMMANDS` in `expNNN.py`).

**4.5 — Import boundary.** A runner reaches a tool by *running its CLI* (subprocess), never by `import`ing it, and tools never import runner code. They communicate only through the files in §4.3 — which is what keeps tools generic and the contract language-neutral (§1.4).

**4.6 — `numbers.json` aggregation.** The runner aggregates each command's `config.json` + its headline metric fields into a single `numbers.json` in `artifacts/data/expNNN/`:

```json
{
  "lif": { "config": { "current": 2.5, "duration": 100.0, ... }, "firing_rate_hz": 90.0 },
  "net": { "config": { "n": 200, ... }, "mean_firing_rate_hz": 104.2 }
}
```

**4.7 — Provenance.** `setup_run_dir` stamps a `_provenance` block into `config.json` — the git commit SHA, a `dirty` flag (uncommitted changes at run time), and a UTC timestamp — which flows into the committed `numbers.json`. Every published result records exactly which code produced it; the publisher surfaces it as a page/PDF footer. Degrades gracefully outside a git repo (`commit: null`). An **inline** runner (no tool to inherit from) gets the same block by wrapping its config in `helpers/provenance.stamp(config)` — the runner-side twin of `setup_run_dir`'s stamp, kept as a separate copy because the firewall (§4.5) forbids a tool importing `experiments/`. Alongside the stamp, every runner drops a `run.sh` reproducer into `artifacts/data/<id>/` via `helpers/provenance.write_run_sh(ARTIFACTS)` — the committed twin of the `run.sh` tools write into scratch `temp/` (§4.3).

## 5. Publishing

**5.1 — Scratch vs record.** `temp/<tool>/<cmd>/` is scratch — gitignored, overwritten every run. The runner writes the rendered figure(s) + aggregated `numbers.json` (and any video) + a `run.sh` reproducer into **`artifacts/data/<id>/`**, which *is* committed. That folder is the publisher-neutral record: the single place the publisher reads from. (The tool's own `run.sh` stays in scratch `temp/`; the runner's is committed here.)

**5.2 — Typst is the publisher.** `demolab build` globs `writings/*.typ` (and each entry's mp4s) into a JSON manifest (`temp/bundle/index.json`), stages the engine's static `main.typ` beside it, then compiles it (it reads the manifest) to **three targets in one pass** — no generated Typst source:
- **Web** — `artifacts/site/`: `index.html` (entries grouped by collection, §6.5), `all.html` (every entry, newest first), and an HTML page per entry (figures inline, videos play, math as MathML, styled by the engine's stylesheet).
- **Per-entry PDFs** — `artifacts/site/pdfs/<id>.pdf`.
- **Book** — `artifacts/site/pdfs/book.pdf`: every entry, with a table of contents.

**5.3 — What's committed.** PDFs are mirrored to the committed, shareable `artifacts/pdfs/`. `artifacts/site/` is a gitignored build output (CI regenerates + deploys it to Pages). CI does **not** run the experiments, so `artifacts/data/` **must** be committed — that record, not the ephemeral `temp/`, is what reaches the site.

**5.4 — Numbers can't drift.** Each `writings/<id>.typ` reads its own bundle natively — `json("/artifacts/data/<id>/numbers.json")`, `#image("/artifacts/data/<id>/fig.png")` (compiled with `--root` at the repo root) — so the numbers and figures come straight from the run.

## 6. Authoring writings

For *how a writing should read* — prose, math, figures, structure — see [`HOUSESTYLE.md`](HOUSESTYLE.md). This section is the mechanics.

**6.1 — `meta` + `body`.** A writing is `writings/<id>.typ`: a `#let meta = (title, date, description?, collection?, status?, order?)` block and a `#let body = [ … ]` block. `build.py` discovers entries by those two top-level definitions. Model a new one on an existing `writings/<id>.typ`.

**6.2 — Use `lib.typ` helpers; never hand-type numbers.** Import with `#import "/.demolab/lib.typ": …`:
- `numbers-table(entry, title: "…")` — a parameter/metric table straight from a `numbers.json` command entry.
- `video("<file>.mp4", caption: […])` — plays as HTML `<video>`, omitted from the PDF. `build.py` auto-emits every mp4 as a bundle asset.
- `provenance-footer(run.<cmd>.config)` — the git-commit footer.
- `cite(...)` + `reference-list(...)` — inline citations + a DOI reference list (see §6.6).
- `pending-figure(caption: […], note: […], ratio: 16/9)` — a placeholder for a figure whose asset isn't ready yet (a re-run in flight, data not cleared for release). Numbers as a normal "Figure N" and reserves the figure's footprint (a tinted dashed panel) so the page doesn't reflow when the real plot lands. Swap it back to `#figure(#image(...), …)` once the asset exists — a `pending-figure` left in a `final` entry is a lint smell.

Numbers must come from the run (§5.4) — never hand-type a literal that could disagree with `numbers.json`.

**6.3 — Figures.** A data figure is a tool-rendered PNG staged by the runner — `#image("/artifacts/data/<id>/fig.png", width: 100%)`. A *drawing* (a schematic, not a simulation result) can be drawn directly in Typst — native graphics scale crisply, no image file. For something a reader should *explore*, point them at the Streamlit playground (`demolab playground`); in-browser interactivity is deliberately not part of the static site.

**6.4 — The `status` field.** Optional `meta` field for lifecycle — `draft → building → revising → final`, and back freely. It renders as **plain text** next to the date **everywhere the entry appears**: its own page, every listing (each collection page + `all.html`), and the PDF/book. `final` (the default) shows **nothing** — a clean line means done, so only work-in-progress is flagged. Free-form; pick a convention and stick to it. It also drives listing order (§6.5).

**6.5 — Collections & ordering.** Set `collection: <slug>` in an entry's `meta` to group it on the homepage; the slug title-cases by default (`neuron-models` → "Neuron models"). An optional `collections` map + `collection-order` list in the root `demolab.yaml` give each collection a `label` / `description` and set the display order — a collection with no registry entry still works, but title-cases its slug with **no description**, which reads as unfinished. **When you introduce a new collection, register it**: add a `label` + one-line `description` to the `collections` map and append the slug to `collection-order`. Decks are grouped under `slides`; uncollected entries fall under `uncategorized`. Every listing (each collection page + `all.html`) groups entries by kind — **Articles, then Experiments, then Slides** — and within a group sorts by **status** (lifecycle order, so work-in-progress surfaces above `final`) then by **id**, newest first.

**6.5a — Curated reading order.** An optional integer `order:` in a writing's `meta` marks its collection as *curated*: that collection's page lists entries by `order` ascending (unranked entries trail, in id order) instead of the default status-then-newest sort. Use it when a collection should read as a sequence — a documentation arc, a course, a serial — and leave it off for a chronological log of results. If you rank one entry in a collection, rank them all; a half-ranked collection reads as an accident.

**6.6 — Citations & references.** Cite prior work with two `lib.typ` helpers, so numbering, linking, and the web popover all come for free — never hand-type a bracket or a manual list (HOUSESTYLE H24). Import both: `#import "/.demolab/lib.typ": cite, reference-list`.

- **Inline** — `#cite(1, 2)` renders `[1, 2]`. The numbers are **author-managed** (you pass them), so there's no `.bib` file to keep in sync. On the web each number links to its entry.
- **The list** — `#reference-list(((text: [Author A, Author B (year). Title. _Journal_ vol:pp.], doi: "10.…"), …))` renders the numbered **References** section. Each item is a dict: `text` is free Typst content (italicise the journal/title with `_…_`); `doi` is optional and, when present, renders a `doi:…` link to `https://doi.org/<doi>` that opens in a **new tab**.
- **Numbering is positional** — `#cite(1)` points at the *first* entry in the list, `#cite(2)` the second, and so on. Keep the inline numbers and the list order in step (this is the thing hand-typing would silently break).
- **Hover popovers (web only)** — hovering an inline cite shows a small Wikipedia-style card with that reference's text + DOI, pulled from the rendered list entry (so it can't drift). The PDF has no scripts: the inline `[n]` and the References section still render, just without the popover.

See `ar006` for a worked example — ten references with DOIs, inline cites throughout, and the reference list at the foot of the body.

## 7. Adding an experiment

**7.1 — Tool subcommand.** Add a subcommand (or reuse one) in the relevant `tools/<tool>/tool.py`. Pass a `manifest` to `write_output` declaring the headline metrics (and a video, for a rendering tool).

**7.2 — Runner.** Create `experiments/expNNN.py` modeled on an existing runner; declare `COMMANDS`; render the figure(s) from the tool's data into `artifacts/data/expNNN/`. Single-tool runners use bare strings (`COMMANDS = ("lif", "net")`); multi-tool runners use `(tool, command)` pairs (`COMMANDS = (("mujoco", "cartpole"),)`). Finish `main()` with `helpers/provenance.write_run_sh(ARTIFACTS)` so the committed record carries a reproducer; an inline runner also stamps each config with `helpers/provenance.stamp` (§4.7).

**7.3 — Writeup.** Create `writings/expNNN.typ` as a `meta` + `body` pair (§6.1); read the run with `json(...)`, embed figures with `#image(...)`, render tables with `#numbers-table(...)`.

**7.4 — Run + build.** `uv run python experiments/expNNN.py`, then `demolab build` (or the running `demolab dev`).

**7.5 — Staged runs (optional).** An expensive experiment — long training, a big sweep — may split its runner into ordered stages so you can re-enter without repeating the costly prefix. The flow, in dependency order:

- **compute** — the simulation/training itself; writes bulk output to `temp/` (scratch, §5.1).
- **analyse** — reads that scratch and distils what the figures need into the committed record `artifacts/data/<id>/` (the plot-ready bundle: `numbers.json` plus any arrays a plot consumes).
- **plot** — renders the figures, reading **only** from `artifacts/data/<id>/`.

Each stage depends only on its predecessor's output, so a run can start at any stage: full (default), analyse + plot (reuse `temp/`), or plot only (reuse the committed record). **The invariant is the boundary, not the mechanism** — the plot stage reads only from `artifacts/data/<id>/`, which is exactly what lets "plot only" reproduce every figure from a clean clone with no `temp/` (§5.1, §5.3). demolab does **not** mandate *how* you stage: flag names, a stage harness, function signatures, where scratch lives — all the author's call. Most runners need none of this and stay a single one-shot `main()` (§7.2); staging is opt-in, earned by compute cost. Reproducibility never depends on it either — a full run always regenerates `temp/` from `run.sh` (§4.7) and the figures fall out.

## 8. Adding a tool

**8.1 — One directory, the file set.** Each tool lives in its own directory under `tools/` and writes its run artifacts under `temp/<tool>/<cmd>/` (§4.3). A rendering tool also writes its video and declares `headline_video`. It does **not** write plots (§4.2).

**8.2 — Reuse the `setup_run_dir` / `write_output` pattern.** From an existing `tool.py`: `setup_run_dir(command, args)` creates the run dir, configures a logger to `output.log` + stdout, dumps `config.json`, writes the `run.sh` reproducer. `write_output(run_dir, metrics, manifest)` validates the manifest and writes `output.json` + `manifest.json` last. Subcommands are wired via `argparse` `set_defaults(func=...)`; `main()` calls `args.func(args)`.

**8.3 — `write_output` validation.** `headline_metrics` is required and validated against `output.json`; any declared `headline_video`/`headline_figure` must exist on disk. Data tools declare no asset (`{"headline_metrics": [...]}`); a rendering tool adds `headline_video`.

**8.4 — Every tool ships tests.** Put them in `tools/<tool>/test_<tool>.py` (run with `demolab test`). Unit-test the science functions directly — shapes, known properties, determinism (seeded) — and the manifest contract (`write_output` rejects a metric absent from `output.json`, or a missing figure). Keep tests off the filesystem where possible — call the sim functions, not the CLI.

**8.5 — The playground is exempt.** The Streamlit playground (`experiments/playground.py`) is an interactive demo, not an `exp*` runner: it authors no committed artifacts and is exempt from *producing* a manifest. But it still **runs the `neuron lif` CLI** on each slider change and reads back `temp/neuron/lif/lif.csv` + `output.json`, rather than reimplementing the simulation. **Don't duplicate the science** — reach the tool through its CLI.
