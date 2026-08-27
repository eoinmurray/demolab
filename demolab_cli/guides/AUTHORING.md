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

### Fixed inputs for publication builds

Use a committed `build.sources` mapping to pin presentation directories per article:

```yaml
build:
  sources:
    exp022:
      exp022: runs/chosen-training-run/presentation
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
or preview empty states. Unconfigured articles keep their authored resolution. Hardcoded paths
and unbound calls remain outside this mapping.

The build freezes one mapping and file inventory for the website, book, and standalone article
PDFs. With any article configured, a failed compilation aborts publication instead of producing
error stubs, preserving the last successful site and publication PDFs. Without build pins,
the existing tolerant build behavior is unchanged. Remove `build.sources` to return to authored
defaults; old generated mappings are not reused.

`demolab dev` with preview enabled ignores build pins (including unavailable build directories)
and keeps its discovery, Latest, and selection behavior. Without preview enabled, dev uses the
ordinary build path. Neither browser fragments nor `.demolab/preview/` state affect publication.

`video(data-file("exp022/demo.mp4"))` exports videos from selected presentation directories to
generated `_demolab-data/` URLs in the site, in both pinned builds and selected previews. Supported
extensions are `.mp4`, `.webm`, `.ogg`, `.ogv`, `.mov`, and `.m4v`; browser codec support still
depends on the encoded file. Videos in those directories are packaged once per source path;
other run files are not automatically published as downloads. Existing `assets/` videos and
external URLs keep their behavior. Reserve `assets/_demolab-data` for the engine.

Commit the configuration and ensure the same presentation files are available to CI before
running `demolab build`. A local directory in `.gitignore` will not appear in a clean checkout
merely because it is pinned here. There is no automatic copying into `.artifacts/`, upload,
download, or “publish the current preview” step.

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
authorizes this local command to run at startup, on watched changes, and on selection changes.
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
To show an empty selector before an experiment's very first run, declare the attachment
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

`demolab build` never runs discovery or reads preview selections, and publishes no selector
controls. It uses committed build pins when configured, otherwise the authored paths. Keep one
dev server per lab.

### Articles before their first run

Latest with no discovered runs is a normal empty state: the selector says **No runs available**
and is disabled. Other inputs continue working. When discovery finds a run, the next watched
rebuild fills the input automatically. This does not apply to a pinned run that disappeared,
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
and image arguments too. In ordinary builds these helpers read the authored paths normally;
missing publication data is not treated as an empty preview. Hardcoded paths are unaffected.

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
