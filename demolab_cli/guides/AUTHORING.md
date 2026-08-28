# AUTHORING

Demolab publishes Typst writings. Create `writings/<slug>.typ` with two exports:

```typst
#let meta = (
  title: "A clear title",
  created_at: "2026-08-23",
  updated_at: "2026-08-27T14:30:00+02:00",
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

### Authored dates and datetimes

`created_at`, `updated_at`, and the legacy `date` fallback accept strings in either form:

- `YYYY-MM-DD`, for example `"2026-08-27"`.
- `YYYY-MM-DDTHH:MM[:SS[.fraction]]` followed by `Z` or a numeric `+HH:MM` / `-HH:MM`
  timezone offset, for example `"2026-08-27T12:30Z"`, `"2026-08-27T14:30:00+02:00"`,
  or `"2026-08-27T12:30:00.125Z"`.

Datetimes require an explicit timezone. Calendar dates, clock components, and offsets are
validated; seconds must be 00–59. Datetimes display in a readable 12-hour format, for example
`28 August 2026 at 2:30 pm` in PDFs and the book. Web headers and listings use the
compact form `28 Aug 26, 2:30 pm`.
Seconds and fractional seconds are always omitted from display, without rounding minutes.
Midnight is `12:00 am` and noon is `12:00 pm`. The authored local time is shown
without a timezone label or conversion to the viewer's timezone. Date-only metadata has no time added.
HTML `<time datetime>` attributes retain the exact authored string, including timezone and full precision.

Web listings show one compact date under a single `Last changed` heading above the page's first entry list, using
`updated_at` when supplied and otherwise `created_at`. For example, `28 Aug 26, 2:30 pm`.
The date's tooltip identifies it as Created or Updated. Article headers share the list's
typography and metadata bar, but show both labelled Created and Updated dates on the right
when supplied. Their tooltips retain the full year. PDFs and the book also retain both
authored dates. No creation timestamp is relabelled as an update.

Update validation and "Recently worked on" ordering compare instants normalized to UTC.
For these comparisons only, a date-only value means midnight UTC on that date. You may mix
the two forms, but `updated_at` cannot be earlier than `created_at`: a date-only update on
the same day as a creation time after midnight UTC is therefore earlier and is rejected.
Equal instants are allowed, and a supplied update is still displayed. Recent-work ties
use ID descending, including equivalent timestamps with different offsets or fractional
precision. No value is inferred from Git, filesystem timestamps, builds, or deployment.
Run-discovery timestamps follow their separate protocol below.

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

### Fixed inputs for publication builds

Use a committed `build.sources` mapping to pin presentation directories per article:

```yaml
build:
  sources:
    exp022:
      exp022: runs/chosen-presentation-run/export
    exp092:
      exp023: runs/chosen-baseline-run/presentation
      exp025: runs/chosen-trained-run/presentation
    exp093:
      legacy.exp025: runs/older-run/presentation
      current.exp025: runs/newer-run/presentation
```

These are illustrative directories, not a storage convention. Paths are relative to
`demolab.yaml`; they must exist inside the lab, outside `.demolab/`, with no parent traversal,
symlinks, or special files. No discovery command, run-ID parser, or storage-specific metadata
is required. Use immutable directories if repeatable inputs matter; Demolab does not lock or
hash their contents, validate scientific provenance, or acquire missing runs.

Bind `data-file` to the article as shown below for preview. During `demolab build`, these pins
take precedence over its Typst `sources` dictionary. Each configured article must pin every
key it reads through the bound `data-file()`; missing keys and files are errors, never fallback
or empty states. Pins override the whole article, not individual discovered keys. Unpinned
articles use Latest when discovery attaches inputs to them, otherwise their authored resolution.
Hardcoded paths and unbound calls remain outside this mapping.

The build freezes one mapping and file inventory for the website, book, and standalone article
PDFs. With any article configured, a failed compilation aborts publication instead of producing
error stubs, preserving the last successful site and publication PDFs. This also applies to
articles resolved through discovery. Without pins or discovered input bindings, the existing
tolerant build behavior is unchanged. Remove `build.sources` to use Latest where discovery is
configured, or authored defaults otherwise; old generated mappings are not reused.

`demolab dev` with preview enabled ignores build pins (including unavailable build directories)
and keeps its discovery, Latest, and selection behavior. Without preview enabled, dev uses the
ordinary build path. Neither browser fragments nor `.demolab/preview/` state affect publication.

`video(data-file("exp022/demo.mp4"))` exports videos from selected presentation directories to
generated `_demolab-data/` URLs in the site, in fixed/Latest builds and selected previews. Supported
extensions are `.mp4`, `.webm`, `.ogg`, `.ogv`, `.mov`, and `.m4v`; browser codec support still
depends on the encoded file. Videos in those directories are packaged once per source path;
other run files are not automatically published as downloads. Existing `assets/` videos and
external URLs keep their behavior. Reserve `assets/_demolab-data` for the engine.

Commit the configuration and ensure the same presentation files are available to CI before
running `demolab build`. A local directory in `.gitignore` will not appear in a clean checkout
merely because it is pinned here. There is no automatic copying into `.artifacts/`, upload,
download, or “publish the current preview” step.

### Automatic Latest inputs and optional run selectors

The existing `preview` configuration supplies discovery for both `demolab build` and
`demolab dev`. Only dev enables selectors; ordinary builds remain static:

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
configuration directory as its working directory. Use commands you trust: this configuration
runs the command once per build (including standalone article PDF builds), and in dev at startup,
on watched changes, and on selection changes. Discovery still runs when build pins are present.
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
`created_at` must include a timezone; Latest means greatest normalized creation timestamp,
then greatest ID on ties. This is creation-time ordering, not completion-time ordering; neither
filesystem times nor run-name ordering determines recency. `presentation` is relative to `source`.
Directories are read in place, without copying;
paths escaping the lab, runtime paths, and symlinks are rejected. The command owns discovery
conventions and storage-contract checks: return only eligible completed presentation runs,
not newer compute or analysis runs. For Pingstore, use its read-only discovery adapter to
validate authoritative `run.json` metadata and select presentation-stage output. Demolab
itself has no Pingstore dependency or built-in assumptions about run-directory names.

An omitted article automatically matches its filename ID to the discovered `experiment`.
A list declares independent experiment inputs. A mapping declares named groups with keys
`<group>.<experiment>`; groups do not imply linked run selections. `article-id: []` disables
discovery bindings and selectors for that article (explicit build pins still apply). Use the
stable basename ID, regardless of nested source folders.
To get an empty input before an experiment's very first run, declare the attachment
explicitly (for example `exp022: [exp022]`); an empty catalogue cannot establish automatic matches.

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

In `demolab dev`, a minimal selector row below the article metadata lists each run ID once,
marking the newest as Latest. Every input initially follows Latest unless the URL fragment specifies
a run. Changes apply immediately. Each choice affects only that article and key, including all its figures,
numerical prose, and preview PDFs. Groups each start at Latest, so paired comparisons may
initially compare a run against itself. Source files, configuration, and script arguments
that name local files are watched; restart dev after changes to other discovery dependencies.

The fragment stores choices as `#run.<data-key>=latest` or
`#run.<data-key>=run%3A<run-id>`, joined by `&` for multiple inputs. Refreshing that URL
restores the article's choices together. Heading anchors can precede the run parameters.
Reset to default clears this article's fragment selections and returns its inputs to Latest,
without resetting other articles. Automatic live reload adopts the shared server preview,
avoiding competing rebuilds between tabs; manual refresh restores the URL choices.
Accepted server selections remain in `.demolab/preview/state.json`; preview output lives in
`.demolab/preview/site/`. Compilation or discovery errors are visible in the panel. Failed
changes never save a new accepted choice or replace the last successful site. Missing files
do not fall back to another run. A disappeared saved run remains an error until changed;
Reset to default also recovers malformed local state. `demolab clean` removes
preview state along with other generated output.

`demolab build` resolves each unpinned article input to Latest from its single discovery result.
It freezes the selections and file inventory in `.demolab/bundle/data-inputs.json` for every
compiler target, without enabling preview mode, reading saved selections, or publishing selector
controls. A later build may pick up newer runs. Directory contents are not locked or snapshotted;
use immutable run directories. Discovery failures and missing/corrupt selected inputs stop the
build and preserve the previous site; they are not converted to empty inputs or error stubs.
No Pingstore data is changed and nothing is staged into `.artifacts/`. Keep one dev server per lab.

### Articles before their first run

Latest with no discovered runs is a normal empty state in builds and previews. In dev, the
selector says **No runs available** and is disabled; static builds have no selector. Other inputs
continue working. When discovery finds a run, the next build fills the input automatically.
This does not apply to a pinned run that disappeared,
invalid discovery output, or missing/corrupt files inside an actual selected run: those are errors.

For this state only, `data-file()` returns `none` instead of a path. It never reads an authored
default in its place. Opt into empty-aware content using `data-json()` and `data-image()`;
`video()` also accepts `none`. Images and videos use the existing themed 16:9 pending panel.
Numerical prose and calculations need an explicit Typst conditional—Demolab cannot invent
the fields or results of absent JSON:

```typ
#let data-file = data-file.with(article: "exp022")
#let result = data-json(data-file("exp022/numbers.json"))
#let body = [
  This explanation remains visible before any runs exist.

  #if result == none [Awaiting a run.] else [Accuracy: #result.accuracy_percent%.]

  #figure(
    data-image(data-file("exp022/accuracy.svg"), width: 100%),
    caption: [Accuracy], kind: image, supplement: [Figure],
  )
  #video(data-file("exp022/demo.mp4"), caption: [Demonstration])
]
```

`data-json(path)` otherwise calls native `json(path)`; `data-image(path, ..args)` calls native
`image(path, ..args)`. Existing raw `json(data-file(...))` / `image(data-file(...))` calls remain
strict and must be guarded or migrated to render an empty input. Guard data-dependent captions
and image arguments too. Without discovery bindings or build pins, these helpers still read
authored paths normally; missing files at those paths are errors, not empty inputs.
Hardcoded paths are unaffected.

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
