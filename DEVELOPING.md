# Developing demolab

This repository is the source of `demolab-cli`. The package is installed editable, so
`uv run demolab` executes the working tree.

All internal demo inputs live in `.demo/`: `demolab.yaml`, `writings/`, and optional
`assets/` or `landing.typ`. See [.demo/README.md](.demo/README.md).
Generated files live only in the repository's `.demolab/`, never inside `.demo/`.

From the repository root (or a demo subdirectory), run `uv run demolab dev`,
`uv run demolab build`, or `uv run demolab clean`. Clean removes generated output without
touching `.demo/`; the next build recreates it. There is no need to copy or symlink inputs.

`demolab_cli/_paths.py` owns the shared layout. The engine checkout is recognised by
`.demo/demolab.yaml` plus `demolab_cli/build.py` and `demolab_cli/VERSION`; a root
`demolab.yaml` takes precedence as an ordinary lab. Typst's root remains the checkout root;
internal compiler inputs route config, writings, assets, and `data-file()` to the demo.
Every compile path (site, book, entry PDF, and deck) receives the same layout. The internal
site intentionally contains only ordinary stub writings in a few example collections. Feature
tests create their own isolated fixtures instead of turning the development site into a catalogue
of historical engine behaviour.

Ordinary labs still use root `demolab.yaml`, `writings/`, `assets/`, `.artifacts/`, and
`.demolab/`. Demo content is not shipped in the wheel or installed by `demolab init`, which
still installs only the stub skeleton.

`demolab_cli/preview.py` owns the storage-neutral JSON discovery protocol, configuration,
validation, and per-article selections. Commands run without a shell from the configuration
directory with `DEMOLAB_PREVIEW_SOURCE` set to the absolute source directory. The renderer
receives only an article/data-key → presentation-directory mapping. No Pingstore contract is
embedded in the engine. See AUTHORING for the protocol and resolver binding.
An explicitly empty Latest input maps to JSON null, which `data-file()` exposes as Typst `none`.
The opt-in `data-json()` / `data-image()` helpers and `video()` handle that sentinel; articles
guard numerical prose with native conditionals. Real selected-run file failures remain strict.

`data_sources.py` owns `build.sources`, ordinary-build Latest resolution, and source-file validation.
Builds reuse `preview.py`'s discovery configuration/protocol but never its Session or saved state.
Discovery adapters return eligible presentation runs; Latest uses their normalized `created_at`
timestamps, with ID as a tie-breaker, not filesystem times or run-name recency.
One `.demolab/bundle/data-inputs.json` inventory supplies
every compiler invocation; the preview worker writes its own equivalent inside `.demolab/preview/`.
Configured articles require every bound key to resolve. Declared Latest inputs without runs map to
null. An attributable article compilation error, including a missing or corrupt selected file,
produces a visible stub for that article while unrelated articles publish. Invalid source mappings,
discovery failures, deck failures, and unattributable compiler errors still abort publication.
The failed article's independently readable metadata keeps it in web listings with a build-error
marker, while its article PDF and book chapter remain omitted. Standalone data-backed PDF builds
replace output only after successful compilation.
Selected directories' video files are emitted as bundle assets at hashed `_demolab-data/` paths;
`video()` uses the same inventory to link them. No presentation-data staging copy is introduced.

`devserver.py` serializes preview requests through its existing watcher/build worker. A
loopback-only, same-origin, token-protected endpoint queues selections; `typ/preview.js`
provides the HTTP-injected, theme-native row below article metadata. URL fragments restore
all inputs of one article atomically; reset affects only that article. Preview state, frozen compiler input, scratch, PDFs,
and site live under `.demolab/preview/`. The private build-worker `--preview` flag selects
those paths and treats article stubs as failures before site replacement. Ordinary builds
invoke discovery independently but never consume local selections. Failed builds retain the last successful
site and accepted state; pending choices remain editable in the error panel. One dev server
per lab is supported; concurrent servers would share preview state and build paths.

`url_inputs.py` owns the opt-in query allowlist and isolated article rendering.
`typ/url-entry.typ` compiles one article and its resources in a fresh
`.demolab/url-inputs/view-*/site/` namespace. It never invokes discovery or changes
preview/publication state. Resource URLs use the private rendering namespace;
ordinary navigation stays at the lab root. The dev server serializes compilation
with its normal build worker, accepts these requests only from loopback clients,
and injects no live-reload scripts into parameterized responses. Writing defaults
and selection views remain user-owned. See AUTHORING and test_url_inputs.py.

`demolab.yaml` may override `writings` with a relative directory, defaulting to `writings/`.
`LabLayout` validates it and recursively enumerates visible source files. Typst's `eval` command
parses the setting lazily, cached by configuration contents (including parse errors), so the engine
keeps zero Python runtime dependencies and setup/docs/clean do not need Typst. Build manifests
carry each article/deck's stable basename ID and root-relative source path; imports never reconstruct
paths from IDs. The dev watcher refreshes its source root after config edits and includes
project-owned dependencies across the lab root, including `.artifacts/` and `.pingstore/`, while
excluding runtime, environments, caches, and scratch output. Full builds compile a fresh
`.demolab/bundle/site-next/` candidate and replace the generated site only on success, pruning
obsolete outputs without touching authored inputs.

Run `uv run pytest` for tests and `uv build` to produce the wheel and source distribution. A wheel
must contain `typ/`, `guides/`, and `scaffold/`, but not engine tests or generated demo output.
An end-to-end build must write `.demolab/site/index.html` and must not create `artifacts/site/`.

`demolab_cli/VERSION` is authoritative. A push to `main` that changes it publishes to PyPI through
trusted publishing and creates the matching `v<VERSION>` tag.
