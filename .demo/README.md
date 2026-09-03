# Internal Demolab example

This directory contains the small, hand-authored site used while developing Demolab.
It demonstrates ordinary writings, collections, cross-collection tags, metadata, navigation, HTML output, and
PDF output. The pages are deliberately brief and contain no experiment runs or scientific
claims.

Run from the repository root:

```text
uv run demolab dev
uv run demolab build
uv run demolab clean
```

Authored inputs stay under `.demo/`. Generated runtime stays under the repository's
`.demolab/`; do not edit it by hand.
