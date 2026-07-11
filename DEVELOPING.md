# Developing demolab

This repo is the source of the **`demolab-cli`** package — the engine (`demolab_cli/`:
build code, Typst templates, runbooks, guides, scaffold + demo) plus the packaging to ship
it to PyPI. `uv sync` installs the package **editable**, so the `demolab` command here runs
the working tree's code directly, and the engine-data lookup resolves to these very files —
edit, run, no reinstall.

## Serve the shipped demo — the usual case

```sh
demolab dev --demo             # materialises the demo into temp/demo-preview and serves it
demolab dev --demo --landing   # …and previews the marketing landing page (site/landing.typ)
```

This copies the demo into `temp/demo-preview/` (a disposable lab; rebuilt fresh on every
invocation) and serves it. **Engine edits hot-reload** — the dev server watches the package's
`typ/` assets and `.py` files, which here *are* the working tree. **Demo-content edits don't**
(the served copy is a snapshot): edit under `demolab_cli/scaffold/demo/`, then rerun the
command — or serve the demo source directly when iterating on demo content itself:

```sh
DEMOLAB_ROOT=demolab_cli/scaffold/demo uv run python -m demolab_cli.devserver
```

(That writes build scratch into `scaffold/demo/temp/` + `scaffold/demo/artifacts/site/` —
both gitignored, both excluded from the wheel.)

## Full sandbox — when you need to *run* the experiments

To **run** the demo's experiments (regenerate figures, tweak a runner), materialise the demo
at the repo root — this repo's own `demolab.yaml` makes it a valid lab:

```sh
demolab add-demo-content   # copy the worked demo (skeleton + demo) to the repo root
demolab dev                # serve whatever content is at the root
demolab run exp000         # re-run a runner, etc.
```

This *copies* the demo to the root, so keep it out of git with a **local** exclude — never
the shipped `.gitignore`. `.git/info/exclude` is per-clone and never committed:

```sh
cat >> .git/info/exclude <<'EOF'
# local dev sandbox — never committed
/writings/
/experiments/
/tools/
/artifacts/
EOF
```

Tear it down with `demolab clear-demo-content` (or `rm -rf writings experiments tools artifacts`).

## Packaging & release

- **Build + inspect the wheel:** `uv build`, then `unzip -l dist/demolab_cli-*.whl` — the
  wheel must carry `typ/`, `runbooks/`, `guides/`, `scaffold/` (demo *without* its
  `temp/`/`artifacts/site/` noise) and no `demolab_cli/test_*.py`. CI builds from a clean
  checkout, so local noise can't ship even if the excludes drift.
- **Version:** `demolab_cli/VERSION` is the single source of truth (hatchling reads it via
  the regex version source; `demolab version` prints it; lib.typ stamps it into the site's
  generator meta). SemVer per `demolab_cli/CHANGELOG.md`.
- **Test from the wheel:** `uvx --from dist/demolab_cli-*.whl demolab-cli init` in an empty
  dir, then point the fresh lab's `[tool.uv.sources]` at the wheel to `uv sync` against it.
- **Release:** update `CHANGELOG.md`, bump `VERSION`, commit, then
  `git tag v<VERSION> && git push --tags` — `.github/workflows/publish.yml` builds and
  publishes to PyPI via trusted publishing (the tag must match `VERSION`).

## Why the lab needs `.demolab/` staging at all

Writings use root-relative paths (`/.demolab/lib.typ`, `/artifacts/…`) and Typst confines
every read to `--root` (the lab). The engine lives in site-packages — outside every lab —
so the CLI materialises the few files Typst must read (`lib.typ` + web assets) into the
gitignored `.demolab/` and stages `main.typ` into `temp/bundle/` per build. Everything else
the engine does happens in Python, where site-packages is a perfectly good home.
