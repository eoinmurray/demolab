# Changelog

Notable changes to the **demolab engine** (`demolab-engine/`). Format follows
[Keep a Changelog](https://keepachangelog.com); demolab uses [SemVer](https://semver.org) while
`0.x` signals the contract is still stabilising:

- **major** — a break that may need edits to *your* content (the tool↔experiment contract, the
  firewall, or the `meta` schema). *"update demolab"* flags it for review.
- **minor** — a new backward-compatible capability.
- **patch** — fixes and tweaks.

The current version lives in [`VERSION`](VERSION); `task version` prints it. On *"update demolab"*
the runbook shows the entries between your version and the latest.

## [Unreleased]

## [0.2.1] — 2026-07-06

### Changed
- **LINT enforces the references system.** The lint runbook now flags any hand-rolled citation —
  typed `[1]` brackets, a manual `== References` section, literal `doi.org` links, or author–year
  cites like "(Smith 2020)" — as an H24 violation; references must go through `#cite` +
  `#reference-list`. Also documented the system fully in RULES §6.6.

## [0.2.0] — 2026-07-06

### Changed
- **Listing layout stacked.** Entry rows now put the `id` + title on top with a quiet
  `date · status · pdf` sub-line beneath the title, instead of right-aligning the meta — so long
  titles wrap cleanly without orphaning the metadata. Applies to every listing (collection pages +
  `all.html`).

## [0.1.0] — 2026-07-06

Initial versioned release — the engine after its foundational build-out.

### Added
- **Engine-only distribution.** The repo ships with no content; `task scaffold` lays down the bare
  structure, `task add-demo-content` overlays a worked demo, `task clear-demo-content` removes it.
  The demo lives in `demolab-engine/scaffold/` and doubles as the smoke-test fixture.
- **One-line installers** — `install.sh` (macOS/Linux) and `install.ps1` (Windows), served from the
  project landing page at demolab.eoinmurray.info.
- **14 agent runbooks** — getting-started, tour, migrate-code, from-jupyter, from-paper,
  migrate-stack, embed-docs, next, ground-claims, lint, doctor, red-team, steelman, update — plus a
  `HELP` index, each triggerable by bare name.
- **Citations** — `#cite(...)` inline numbered cites + `#reference-list(...)` with DOI links, and
  Wikipedia-style hover popovers on the web (DOIs open in a new tab).
- **Entry status** — a free-form `meta.status` (`draft`/`revising`/`final`), shown as plain text
  across every listing and entry page, and driving listing order (Articles → Experiments → Slides,
  then status, then id).
- **Author/contact branding** — a byline under the homepage title + `<meta name="author">`.
- **Friendly empty-state homepage** on a freshly-scaffolded repo.

### Changed
- The figure-data format is the author's choice (CSV, JSON, `.npz`, …); only the contract files
  (`config`/`output`/`manifest`/`numbers.json`) stay JSON.
