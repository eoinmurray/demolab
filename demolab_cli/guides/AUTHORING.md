# AUTHORING

Demolab publishes Typst writings. Create `writings/<slug>.typ` with two exports:

```typst
#let meta = (
  title: "A clear title",
  created_at: "2026-08-23",
  updated_at: "2026-08-27",
  description: "One sentence for listings.",
  collection: "notes",
)

#let body = [
  Your presentation goes here.
]
```

The filename becomes the URL. Slugs are unrestricted apart from normal filename safety; numeric
IDs are unnecessary. `title` and `created_at` are required. Add `updated_at` only after a
substantive content update; every supplied update date is displayed, even if it equals the
creation date. Omit it when no update should appear. Demolab renders authored values and never
infers dates. The legacy `date` field remains a deprecated fallback for existing writings.
Optional `description`, `collection`, `status`, `order`, and `annotations` fields control listings
and presentation.

## Source directory and nested folders

The default source directory is `writings/`. To choose another, add to `demolab.yaml`:

```yaml
writings: articles
```

The path is relative to the directory containing `demolab.yaml`. It must name a directory
inside that content tree, using forward slashes; absolute paths, `..`, and generated `.demolab/`
paths are rejected. A custom directory must already exist. An absent default `writings/` is
still a valid empty lab. In the engine checkout this resolves below `.demo/`.

Demolab searches nested folders automatically: `articles/physics/gravity.typ` publishes as
`gravity.html`, and `articles/talks/keynote.slide.typ` publishes as `pdfs/keynote.pdf`.
`demolab build gravity` still builds just that article's PDF. Moving a source between folders
does not change its ID, URL, or collection; collections remain explicit metadata.

IDs must be unique across articles and decks, including case-only differences. Duplicate
filenames fail with both source paths; rename one file to resolve the conflict. Ordinary `.typ`
helpers without both `meta` and `body` exports are not published. Source-relative Typst imports
continue to resolve beside the importing file; root-relative `/assets/...` paths are unchanged.

Hidden files/folders are skipped. Directory symlinks are not traversed, and source symlinks
escaping the content tree or pointing into generated runtime are rejected. Co-located files
are available to Typst imports but are not automatically copied to the website; use `assets/`
for public static downloads.

Live preview watches nested sources and helpers, and switches watched directories when this
setting changes. Source edits conservatively rebuild decks because helpers may be shared.
Successful full builds replace the generated site, removing obsolete pages and PDFs; failed
builds preserve the previous site. Changing the setting never moves or deletes authored files.

## Assets and publication

Put static inputs under `assets/`. Typst can read them from absolute project paths such as
`#image("/assets/chart.svg")` or `#let data = json("/assets/results.json")`. Static files are
copied into the website at the same relative path; `#video("clip.mp4")` references an asset.

Use `demolab dev` for live preview and `demolab build` for a complete publication. Generated web
and PDF output lives under `.demolab/site/` and `.demolab/pdfs/`; reserve `.artifacts/` for tracked
publication evidence owned by your project.

For presentation evidence, `data-file("benchmark-a/numbers.json")` resolves beneath
`.artifacts/` by default. An article may optionally bind a Typst dictionary that maps a data key
to another directory beneath the same data root:

```typ
#let sources = ("benchmark-a": "benchmark-a-run-001")
#let data-file = data-file.with(sources: sources)
```

Every `data-file("benchmark-a/...")` call in that scope then uses the mapped directory. This is
static authored resolution; it does not discover runs, infer Latest, or create a preview selector.
An unmapped key retains `.artifacts/<key>/` compatibility, and a missing mapped file fails rather
than falling back to the key's ordinary directory.

### Optional article-scoped run selectors

Add `preview` to `demolab.yaml` to enable development-only selectors:

```yaml
preview:
  source: .pingstore/runs
  discover: [python, scripts/discover_runs.py]
  articles:
    exp092: [exp023, exp025, exp038, exp048]
    exp093:
      legacy: [exp025, exp038, exp049]
      current: [exp025, exp038, exp049]
```

`source` is relative to `demolab.yaml`, inside the lab root and outside `.demolab/`.
`discover` is an argument array executed exactly as given, **without a shell**, with the
configuration directory as its working directory. Use commands you trust: enabling preview
authorizes this local command to run at startup, on watched changes, and on Refresh sources.
The absolute source directory is passed in `DEMOLAB_PREVIEW_SOURCE`, not appended to arguments.
Demolab imposes a 30-second timeout and a 4 MiB limit on each output stream.

The command prints a JSON array to stdout (diagnostics belong on stderr):

```json
[
  {"id": "run-001", "experiment": "exp023", "label": "Baseline",
   "created_at": "2026-08-25T10:00:00Z", "presentation": "run-001/presentation"}
]
```

IDs must be unique across the catalogue. `label` is optional; other fields are required.
`created_at` must include a timezone; Latest means greatest timestamp, then greatest ID on
ties. `presentation` is relative to `source`. Directories are read in place, without copying;
paths escaping the lab, runtime paths, and symlinks are rejected. The command owns discovery
conventions and storage-contract checks, including which runs are completed. For Pingstore,
read authoritative `run.json` metadata and validate `pingstore.run/v2` in your script; Demolab
itself has no Pingstore dependency or built-in assumptions about run-directory names.

An omitted article automatically matches its filename ID to the discovered `experiment`.
A list declares independent experiment inputs. A mapping declares named groups with keys
`<group>.<experiment>`; groups do not imply linked run selections. `article-id: []` disables
selectors for that article. Use the stable basename ID, regardless of nested source folders.

Bind the article scope **before reading JSON or constructing content**:

```typ
#import "/.demolab/lib.typ": *
#let data-file = data-file.with(article: "exp092")
#let result = json(data-file("exp023/numbers.json"))
```

For named groups, use qualified keys and optionally specify authored publication directories:

```typ
#let sources = ("legacy.exp025": "old-exp025", "current.exp025": "exp025")
#let data-file = data-file.with(article: "exp093", sources: sources)
#let legacy = json(data-file("legacy.exp025/numbers.json"))
#let current = json(data-file("current.exp025/numbers.json"))
```

Without `sources`, those default to `.artifacts/legacy.exp025/` and
`.artifacts/current.exp025/`. Bind once per article, not per figure. Reusable helpers should
accept this resolver as an argument; importing another article's already-constructed body
retains that other article's scope. Hardcoded paths and unbound calls remain unchanged and
are not controlled by the selector.

In `demolab dev`, the article's Data sources panel offers Latest, individual runs, and
Published/default. Every input initially follows Latest unless an explicit local choice was
remembered. Each choice affects only that article and key, including all its figures,
numerical prose, and preview PDFs. Groups each start at Latest, so paired comparisons may
initially compare a run against itself. Source files, configuration, and script arguments
that name local files are watched; use Refresh sources for other discovery dependencies.

Selections are remembered in `.demolab/preview/state.json`; preview output lives in
`.demolab/preview/site/`. Compilation or discovery errors are visible in the panel. Failed
changes never save a new accepted choice or replace the last successful site. Missing files
do not fall back to another run. A disappeared saved run remains an error until changed;
Reset all selections to Latest also recovers malformed local state. `demolab clean` removes
preview state along with other generated output.

`demolab build` never runs discovery or reads preview selections, and publishes no selector
controls. It always uses the authored paths. Keep one dev server per lab.

The homepage remains a compact collection directory by default. To expand collection contents
and optionally show recently updated ordinary writings, add this to `demolab.yaml`:

```yaml
index:
  mode: expanded
  recent: 5
```

Omit `recent` or set it to `0` to remove “Recently worked on”. Recent work is ranked only by
authored `updated_at ?? created_at`, then by ID descending; slides are excluded.

## Nested collections

Collections are flat unless a parent explicitly lists `children` in `demolab.yaml`:

```yaml
collections:
  documentation:
    label: Documentation
    description: Developer documentation grouped by project.
    theme: docs
    homepage: false
    children: [pinglab-docs, snnlang-docs]
  pinglab-docs:
    label: Pinglab docs
    description: Guides and API notes for Pinglab.
  snnlang-docs:
    label: SNNLANG docs
    description: Language reference and integration guides.
```

The parent page is generated even when no writing belongs directly to it. It lists children in
the authored order with their labels, descriptions, and recursive entry counts. Every child must
be registered under `collections`; a child can have only one parent, and cycles are rejected.
`theme: docs` is a visual skin only: themed collections and writings use the same components,
metadata, navigation, ordering, and responsive layout as ordinary collections and writings.

Children inherit `theme` and homepage visibility from their parent unless they set their own
theme. A parent's `homepage: false` always keeps its full subtree out of homepage directories and
recent work; direct pages, the all-entries index, and PDFs remain available. Hierarchy never
changes authored dates or writing order, and Demolab never infers parentage from collection slugs.
