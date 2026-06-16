# Framework changelog

Versioned history of the **demolab framework** — the shared machinery that
`UPDATE.md` syncs from upstream (the Astro publishing engine, contracts, CI). It
does *not* track your own content (notebooks, posts, simulators); that's yours.

The top `## [x.y.z]` entry is the current framework version. The update runbook
(`UPDATE.md`) reads it to tell how far behind a repo is, and shows the entries
in between on update.
Each entry flags any **manual step** (a dependency to install, a contract change
to hand-port) that the file sync can't do for you.

Versioning: **major** = breaking contract change needing migration · **minor** =
additive framework feature · **patch** = fixes, no action needed.

## [0.3.0] - 2026-06-16

### Added
- `UPDATE.md` — a tool-agnostic runbook for one-way sync of framework files from
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
- Initial framework: the CLI ↔ notebook manifest contract (`config.json`,
  `output.json`, `manifest.json`, `run.sh`), the Astro publishing engine
  (`src/docs/src/`), and the contracts doc `CONTRIBUTORS.md`.
