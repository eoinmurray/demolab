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
