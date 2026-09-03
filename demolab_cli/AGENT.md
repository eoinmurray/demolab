# demolab

This project is a presentation: Typst files under `writings/` (or the configured `writings`
directory in `demolab.yaml`), static inputs under `assets/`, and
configuration in `demolab.yaml`. The installed demolab engine builds a static website and optional
PDFs.

Writings are discovered recursively. Folders organise sources, not URLs or collections; each
article/deck filename must have a unique ID across the source tree. Helper files without the
article exports are not published. See AUTHORING for configuration and path boundaries.
Optional `meta.tags` values generate cross-collection tag pages without changing collection or
status ordering.

Use `demolab dev` for live preview and `demolab build` for final output. Do not hand-edit generated
files under `.demolab/`; `.artifacts/` is tracked, user-owned publication evidence and must not be
gitignored. Writings may read assets directly with root-relative Typst paths such as
`/assets/chart.svg` or `/assets/data.json`.

`demolab docs` lists the short authoring guides. Optional `preview` configuration runs a trusted,
user-supplied discovery command once per build to resolve Latest presentation inputs, and
provides article-scoped selectors only in dev; see AUTHORING. Demolab does
not execute experiments, enforce provenance, validate claims, or manage research workflows;
content remains the author's responsibility.

Optional `url_inputs` declarations allow the dev server to render a separate article
from query parameters passed as Typst compiler inputs. Each request has isolated
output; ordinary builds retain authored defaults. See AUTHORING. This is independent
of the older preview/discovery system, which remains available during migration.

Optional committed `build.sources` mappings pin presentation directories per article for
publication, overriding discovery for those articles. Builds ignore preview choices, freeze
their selections and file inventory, and publish no preview controls. Declared inputs with no
runs stay unavailable; discovery or selected-input errors fail without replacing the previous
site. See AUTHORING for fixed inputs and run-backed video output.
