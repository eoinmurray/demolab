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
