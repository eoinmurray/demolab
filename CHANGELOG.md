# Framework feature catalog

A catalog of **framework features** in the demolab template. Downstream repos
don't copy these files — their coding agents reimplement the features they want,
their own way, using this repo as reference (see the **Updating the framework** runbook in `CLAUDE.md`). This catalog is
the menu. It does *not* track content (notebooks, posts, tools) — that's
each repo's own.

Each `## [x.y.z]` entry is one batch of features, newest first. A downstream
agent reads the entries newer than the version it last reviewed, and the user
picks which to adopt. Describe features by intent and behavior so they can be
rebuilt from the description plus the code.

Versioning: **major** = a feature that changes a contract others may have built
on · **minor** = a new additive feature · **patch** = a small fix.

## [0.9.3] - 2026-07-01

### Changed
- **mujoco tool: extracted pure physics primitives.** `simulate_cartpole` and
  `simulate_double_pendulum` are now standalone data-in/data-out functions; the
  command handlers call them with an `on_frame` hook that renders live. mujoco
  now follows the same "generic primitive" shape as neuron, and its tests
  exercise the real functions instead of re-stepping the model. Behavior-
  preserving: nb002/nb003 metrics and mp4 output are byte-identical.

## [0.9.2] - 2026-07-01

### Added
- **Each tool in `core` ships tests** (`core/<tool>/test_<tool>.py`, run via
  `task test` / `uv run pytest`). `core` is now an importable package
  (`__init__.py` added) so tests import the science directly. `neuron` unit-tests
  its `simulate_*` primitives (shapes, spiking properties, seed determinism) and
  the `write_output` manifest contract; `mujoco` steps its MJCF models headlessly
  (no Renderer) to check the physics (pole falls, double pendulum diverges). Adds
  `pytest` as a dev dependency. The Streamlit playground is exempt.

## [0.9.1] - 2026-07-01

### Added
- **`core` ↔ `scripts` import firewall (ruff).** Scoped `core/ruff.toml` and
  `scripts/ruff.toml` ban imports across the boundary in both directions
  (`TID251`): `scripts` may not import `core`, and `core` may not import
  `scripts`. Runners reach tools through the file contract (subprocess a tool
  CLI), keeping tools generic and oblivious to experiment logic. Adds `ruff` as
  a dev dependency.

## [0.9.0] - 2026-07-01

### Changed
- **Flat, user-facing repo layout — grouped by *kind*, not pipeline stage.**
  Dropped the `src/` wrapper and reorganized so a scientist opens the repo to
  their own work:
  - `core/` — the tools (the science); one scoped folder per tool (was `src/tools/`).
  - `scripts/` — the runners (was `src/notebooks/`).
  - `entries/` — the writeups, paired to a runner by id: `.mdx` (web) or `.typ`
    (PDF). Web posts and articles moved here from the site's content dir.
  - `artifacts/` — the committed, kept record: each run's figures + `numbers.json`
    (was `src/results/`).
  - `temp/` — short-lived, gitignored run scratch (was `src/artifacts/`).
  - `demolab-web/` — the web publisher engine (was `src/docs/`).
  The web engine globs entries from `../entries` (split by `nb*`/`ar*` filename)
  and imports figures from `../artifacts`; `vite.server.fs.allow` permits reading
  the sibling dirs. Deploy workflow, `.gitignore`, and all docs updated to match.
- **Added `Taskfile.yml`** wrapping the toolchain (`task run -- nb000`, `task dev`,
  `task build`, `task sync`, …) so common commands don't require remembering the
  `uv` / `bun` invocations.

## [0.8.0] - 2026-07-01

### Added
- **Pluggable publishers, with a Typst example.** Publishing is now a swappable
  layer on top of the tool → artifacts contract, not baked into Astro. A runner
  stages its durable outputs (headline figure + `numbers.json`) into a new
  **publisher-neutral results layer, `src/results/<id>/`** (committed); any
  publisher reads from there. Ships a Typst PDF example (`src/notebooks/nb004.py`
  + `nb004.typ`) that reuses the same tool and bundle as the web notebook
  `nb000` — it reads `numbers.json` natively and compiles a PDF via the `typst`
  package. LaTeX is documented as a further option. Reference: `README.md`
  (“How publishing works”), `CONTRIBUTORS.md` (“Publishing”).

### Changed
- **Result bundles moved out of Astro's `public/` into top-level `src/results/`.**
  Astro posts now *import* their figures from `src/results/` (fingerprinted,
  base-path-correct) instead of referencing `public/notebooks/` via hand-built
  `BASE_URL` strings; `vite.server.fs.allow` is set so the dev server can read
  the sibling directory. `public/` now holds only framework assets (CNAME,
  favicon).

## [0.7.0] - 2026-07-01

### Changed
- **"tool" replaces "CLI" throughout**, for a non-developer (academic) audience.
  The per-experiment programs are "tools", not "CLIs": `src/clis/` → `src/tools/`,
  each `cli.py` → `tool.py`, and per-tool dirs dropped the `_cli` suffix
  (`neuron`, `mujoco`, `playground`). The interactive demo dir is `playground`,
  **not** `streamlit`, to avoid shadowing `import streamlit` when it lands on
  `sys.path`. Reference: `src/tools/*/tool.py`, `CONTRIBUTORS.md`.
- **Framework/content firewall; runbooks live in `CLAUDE.md`.** The
  getting-started / migrate / embed / update runbooks moved out of the published
  `documentation` collection and back into `CLAUDE.md` as the single operating
  manual — so clearing demo content can no longer break onboarding. Nothing the
  framework needs lives under `src/docs/content/`, `src/tools/`, `src/notebooks/`,
  or `src/artifacts/` anymore; those are 100% user content. `README.md` carries
  the human map and points at `CLAUDE.md`. The embed Pages workflow ships as
  `.github/workflows/deploy-wiki.yml.example`; the SVG authoring technique folded
  into `CONTRIBUTORS.md`.

### Removed
- The `documentation` article collection (intro, the SVG how-to, and the four
  guide articles). Their operational content now lives in `CLAUDE.md`,
  `README.md`, and `CONTRIBUTORS.md`.

## [0.6.0] - 2026-06-20

### Changed
- **Docs are now dogfooded on the site.** The getting-started / migrating /
  embedding / updating runbooks moved from the `guides/` folder into the
  `documentation` collection as site articles
  (`src/docs/content/articles/*.md`), so they're browsable on the published
  site under Documentation. `CLAUDE.md` triggers and the README point at the
  new locations. They're still plain markdown an agent or human can follow.

## [0.5.0] - 2026-06-20

### Added
- **Embed mode** (`src/docs/content/articles/ar006.md`): drop demolab into another project as a `wiki/`
  docs subfolder and publish to that repo's GitHub Pages. The tree was already
  path-portable; serve config and branding are now env-driven
  (`PUBLIC_SITE_URL`, `PUBLIC_BASE_PATH`, `PUBLIC_SITE_NAME`, `PUBLIC_SITE_REPO_URL`)
  with demolab defaults, so embedding needs no source edits.
- **Onboarding runbooks**: `src/docs/content/articles/ar004.md` (interactive, agent-driven setup
  + scaffold your first notebook) and `src/docs/content/articles/ar005.md` (import an existing repo,
  wrapping experiments one at a time).

## [0.4.0] - 2026-06-16

### Changed
- Reframed updates as **feature adoption** rather than a file sync. `src/docs/content/articles/ar007.md`
  is now a runbook for an agent to review this catalog and reimplement the
  features the user picks — adapted to the repo's own conventions, using upstream
  only as reference. Nothing is copied or overwritten, so a repo can diverge
  freely and still cherry-pick later ideas.

## [0.3.0] - 2026-06-16

### Added
- `src/docs/content/articles/ar007.md` — a tool-agnostic runbook for one-way sync of framework files from
  upstream, leaving your content untouched. Any coding agent or a human can run it.
- `CHANGELOG.md` + framework versioning, so updates are diffable.
- "Staying up to date" section in `README.md`.

## [0.2.0] - 2026-06-16

### Added
- Notebook lifecycle **`status`** field (`draft → building → revising → final`),
  rendered as a badge on the listing pages and the post header.
  - `src/docs/src/config/status.ts` — single source of truth for the values.
  - `src/docs/src/components/StatusBadge.astro` — the badge.
  - `status` added to the collection schema in `content.config.ts`; threaded
    through `lib/entries.ts`, `EntryList.astro`, and `Post.astro`.

### Manual step
- `status` is optional and absent renders no badge — no action required for
  existing notebooks. Set `status:` in a notebook's frontmatter to opt in.

## [0.1.0] - 2026-06-09

### Added
- Initial framework: the tool ↔ notebook manifest contract (`config.json`,
  `output.json`, `manifest.json`, `run.sh`), the Astro publishing engine
  (`src/docs/src/`), and the contracts doc `CONTRIBUTORS.md`.
