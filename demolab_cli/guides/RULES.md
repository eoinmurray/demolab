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

Demolab does not run source code, validate claims, manage research, or guarantee where numbers
came from. Authors own their content and evidence.
