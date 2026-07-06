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

### Added
- **`guides/SLIDES.md` — deck authoring guide.** Conventions for `writings/*.slide.typ` decks,
  numbered `D1–D13`: the `.slide.typ` marker and skeleton, sizing in absolute `pt` against the
  842 × 474 pt canvas (~350 pt usable under a title), per-aspect figure rows, the
  silent-pagination overflow trap and the page-count check, the layout vocabulary (bullets,
  two-column, code, equation + terms, four figure layouts, table, focus, closer), and the
  dev-server caveat for decks created mid-`task dev`. Indexed from `AGENTS.md`, RULES §3.1,
  STRUCTURE's tree, and GLOSSARY G9.
- **`pending-figure` — placeholder for an unrendered figure.** A `#pending-figure(caption: …,
  note: …, ratio: …)` helper (and the `#pending` body it wraps) stands in for a figure whose asset
  isn't ready yet — a re-run in flight, data not cleared for release. It numbers as a normal
  "Figure N" and reserves the figure's footprint (a tinted, dashed, rounded panel with a small
  framed-image mark over the muted reason) so the page doesn't reflow when the real plot lands.
  Replaces the bare floating text that a missing asset used to leave on the web. RULES §6.2.

## [0.2.4] — 2026-07-06

### Fixed
- **`#cite` spacing ([#1](https://github.com/eoinmurray/demolab/issues/1)).** The inline citation
  was set flush against the preceding word (`runs[2]`). The helper now owns a thin gap before the
  bracket — a weak `h()` in the PDF, a `margin-left` on the web span — so authors attach `#cite`
  directly to the word (`runs#cite(2)`) and the bracket keeps its space without ever orphaning onto
  the next line. Documented the convention in HOUSESTYLE H24.

## [0.2.3] — 2026-07-06

### Added
- **Heading anchors.** Every heading on a web page now carries a slug `id` (its text lowercased,
  non-alphanumerics collapsed to hyphens), so any section is directly linkable as
  `entry.html#the-slug`. A quiet `#` permalink fades in on hover to grab that URL. Applies to entry
  titles, section/subsection headings, and the auto-built References heading.

## [0.2.2] — 2026-07-06

### Fixed
- **Figure numbering restarts per entry.** The whole bundle compiles in one pass, so Typst's
  global figure counter was carrying across every document — a standalone entry PDF could open at
  "Figure 7". Each entry (its page + standalone PDF) now numbers figures from 1; the book keeps
  numbering continuously 1…N across chapters.

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
