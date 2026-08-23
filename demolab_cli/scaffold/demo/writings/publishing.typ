#import "/.demolab/lib.typ": *

#let meta = (
  title: "Publishing",
  date: "2026-08-23",
  description: "Build the website, choose whether to emit PDFs, and deploy static output.",
  collection: "guide",
  order: 3,
)

#let body = [
  `demolab build` writes the website to `artifacts/site/` and, by default, mirrors PDFs to
  `artifacts/pdfs/`. Set `pdfs: false` in `demolab.yaml` for a web-only presentation.

  `demolab deploy-setup` installs GitHub Pages workflows. The deployed result is static HTML and
  assets: no runtime service, database, or JavaScript build tool is required.
]
