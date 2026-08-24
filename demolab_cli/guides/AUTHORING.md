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
substantive content update; Demolab renders authored values and never infers dates. The legacy
`date` field remains a deprecated fallback for existing writings. Optional `description`,
`collection`, `status`, `order`, and `annotations` fields control listings and presentation.

Put static inputs under `assets/`. Typst can read them from absolute project paths such as
`#image("/assets/chart.svg")` or `#let data = json("/assets/results.json")`. Static files are
copied into the website at the same relative path; `#video("clip.mp4")` references an asset.

Use `demolab dev` for live preview and `demolab build` for a complete publication.

The homepage remains a compact collection directory by default. To expand collection contents
and optionally show recently updated ordinary writings, add this to `demolab.yaml`:

```yaml
index:
  mode: expanded
  recent: 5
```

Omit `recent` or set it to `0` to remove “Recently worked on”. Recent work is ranked only by
authored `updated_at ?? created_at`, then by ID descending; slides are excluded.
