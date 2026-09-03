# RULES

Demolab has one pipeline: user-owned `writings/ + assets/ + .artifacts/` inputs produce generated
`.demolab/site/` and optional `.demolab/pdfs/` output.

1. `demolab.yaml` marks the project root and configures the writings directory, branding,
   collections, annotations, and PDF publishing. Every key is optional, but the file itself must remain.
2. `writings/**/*.typ` are user-authored pages exporting `meta` and `body`. The `writings` config
   key may select a different directory relative to `demolab.yaml`; source paths cannot escape
   the content tree or include generated runtime. Files ending in `.slide.typ` are optional
   standalone Typst decks. Folders never change public IDs or infer collections. Article/deck
   IDs must be unique, including case-only differences; helpers without article exports are skipped.
3. `assets/` contains user-owned static inputs. Writings may read these directly.
4. `.demolab/bundle/`, `.demolab/site/`, and `.demolab/pdfs/` are engine-owned generated output.
   `.artifacts/` is tracked, user-owned publication evidence; Demolab reads from it but never
   creates or deletes it. Experiments may also use `temp/` for disposable
   scratch. Do not edit generated files by hand. Successful full builds replace the generated site
   to remove obsolete output; failed builds preserve the previous site. A web-only build (`pdfs: false`) removes stale PDFs
   from `.demolab/site/` but leaves legacy `artifacts/pdfs/` deliverables untouched.
5. `demolab dev` previews; `demolab build` publishes; `demolab deploy-setup` installs static Pages
   workflows. Typst is the only rendering toolchain.
6. An experiment may set `meta.status` to its artifact stage: `ExpScoutPlan`, `ExpScout`,
   `ExpStudyPlan`, or `ExpStudy`. Every supplied stage is visible, and listings follow that
   lifecycle order. Omit it from articles and untyped legacy writings. It identifies the artifact
   that exists, not execution progress or editorial completion.
7. A writing or deck may set `meta.tags` to a list of unique lowercase slugs, with hyphens or
   dots separating components. Tags generate
   cross-collection browsing pages and remain display/discovery metadata only: they never infer
   collections, form hierarchy, or affect lifecycle, date, curated, or homepage ordering.
8. Every writing sets immutable `meta.created_at` to a `"YYYY-MM-DD"` date or an ISO
   datetime with an explicit `Z` or `+/-HH:MM` timezone. Set `meta.updated_at` to the date or
   datetime of the most recent substantive content update and omit it when unchanged. Demolab
   validates and renders only authored values; it never derives them from Git, filesystem,
   build, or deployment data. `updated_at` cannot precede `created_at` after UTC normalization;
   date-only values compare as midnight UTC. Deprecated `meta.date`
   remains a compatibility fallback for existing writings. A supplied `updated_at` is always
   displayed, even when it equals `created_at`; omit it when no update should be shown. Dates do
   not affect collection order.
9. The homepage is a collection directory unless `demolab.yaml` sets `index.mode: expanded`.
   Expanded mode optionally shows the newest `index.recent` ordinary writings by authored
   `updated_at ?? created_at` (ID descending breaks ties), then expands collections in existing
   `collection-order`. Collection writings combine into one ID-descending list: status and curated
   `order` remain visible metadata but never affect this homepage order. Slides are not recent and
   keep their existing separate treatment. `index.recent` defaults to `0` and cannot be negative.
10. Collection nesting is authored only through a registered collection's `children` list. Child
   order is the list order; every child has at most one parent; unknown children and cycles fail
   the build. Children inherit the nearest configured theme and cannot override a hidden parent's
   homepage visibility. Nesting never infers dates, parentage, or writing order.

Demolab does not run source code, validate claims, manage research, or guarantee where numbers
came from. Authors own their content and evidence.
