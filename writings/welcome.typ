// Source-checkout demo content and end-to-end fixture.
#import "/.demolab/lib.typ": *

#let meta = (
  title: "Demolab, simplified",
  created_at: "2026-08-23",
  description: "A small presentation system for Typst writings, static assets, websites, and optional PDFs.",
  collection: "guide",
  order: 1,
)

#let body = [
  Demolab turns a directory of Typst writings and ordinary assets into a navigable website.
  PDF publishing is available, but optional. There is no experiment framework, provenance
  contract, research workflow, or application server hiding beneath it.

  == The whole loop

  ```text
  writings/ + assets/ -> demolab build -> artifacts/
  ```

  Use `demolab dev` while writing and `demolab build` when the presentation is ready.
]
