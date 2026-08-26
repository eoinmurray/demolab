# demolab

This project is a presentation: Typst files under `writings/`, static inputs under `assets/`, and
configuration in `demolab.yaml`. The installed demolab engine builds a static website and optional
PDFs.

Use `demolab dev` for live preview and `demolab build` for final output. Do not hand-edit generated
files under `.demolab/`; `.artifacts/` is tracked, user-owned publication evidence and must not be
gitignored. Writings may read assets directly with root-relative Typst paths such as
`/assets/chart.svg` or `/assets/data.json`.

`demolab docs` lists the short authoring guides. Demolab does not run code, enforce provenance,
validate claims, or manage research workflows; content remains the author's responsibility.
