#import "/.demolab/lib.typ": *

#let meta = (
  title: "Welcome",
  created_at: "2026-08-26",
  description: "A minimal working page in the example site.",
  collection: "pages",
  order: 1,
)

#let body = [
  This is a small working Demolab site. Each file under `writings/` becomes a web page and,
  when PDF output is enabled, a PDF.

  == A deliberately small fixture

  The checkout keeps only enough example content to exercise listings, navigation, assets, and
  builds. Run `demolab dev` to preview it or `demolab build` to produce the static output.
]
