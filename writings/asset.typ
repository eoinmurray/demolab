#import "/.demolab/lib.typ": *

#let meta = (
  title: "Using an asset",
  created_at: "2026-08-26",
  description: "A second page demonstrating direct access to a JSON asset.",
  collection: "pages",
  order: 2,
)

#let example = json("/assets/example.json")

#let body = [
  A writing can read files directly from `assets/`. This page loaded the bundled JSON example.

  == Value from JSON

  The value is *#example.value*.

  The same pattern works for images, downloads, video, and other static inputs.
]
