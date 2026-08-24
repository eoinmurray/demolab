#import "/.demolab/lib.typ": *

#let meta = (
  title: "Authoring a page",
  created_at: "2026-08-23",
  description: "The small writing contract and direct asset access.",
  collection: "guide",
  order: 2,
)

#let example = json("/assets/example.json")

#let body = [
  Every page is a `.typ` file under `writings/` exporting `meta` and `body`. Filenames are
  ordinary slugs; no numeric or experiment prefix is required.

  == Assets and data

  Put images, video, downloads, or JSON under `assets/`. Writings read them directly. This page
  loaded a value from `assets/example.json`: *#example.value*.

  == Organisation

  Add `collection`, `description`, `status`, or `order` to `meta` when useful. Register named
  collections in `demolab.yaml` to control their labels, descriptions, order, and web theme.
]
