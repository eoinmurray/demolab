# RULES

Demolab has one pipeline: `writings/ + assets/ -> artifacts/`.

1. `demolab.yaml` marks the project root and configures branding, collections, annotations, and
   PDF publishing. Every key is optional, but the file itself must remain.
2. `writings/*.typ` are user-authored pages exporting `meta` and `body`. Files ending in
   `.slide.typ` are optional standalone Typst decks; the normal build compiles and lists them.
3. `assets/` contains user-owned static inputs. Writings may read these directly.
4. `artifacts/site/`, `artifacts/pdfs/`, `temp/`, and `.demolab/` are generated. Do not edit them
   by hand. A web-only build (`pdfs: false`) leaves existing shareable PDFs untouched.
5. `demolab dev` previews; `demolab build` publishes; `demolab deploy-setup` installs static Pages
   workflows. Typst is the only rendering toolchain.
6. An experiment may set `meta.status` to its artifact stage: `ExpScoutPlan`, `ExpScout`,
   `ExpStudyPlan`, or `ExpStudy`. Every supplied stage is visible, and listings follow that
   lifecycle order. Omit it from articles and untyped legacy writings. It identifies the artifact
   that exists, not execution progress or editorial completion.
7. Every writing sets immutable `meta.created_at: "YYYY-MM-DD"`. Set `meta.updated_at` to the
   date of the most recent substantive content update and omit it when unchanged. Demolab validates
   and renders only these authored calendar dates; it never derives them from Git, filesystem,
   build, or deployment data. `updated_at` cannot precede `created_at`. Deprecated `meta.date`
   remains a compatibility fallback for existing writings. Dates do not affect collection order.

Demolab does not run source code, validate claims, manage research, or guarantee where numbers
came from. Authors own their content and evidence.
