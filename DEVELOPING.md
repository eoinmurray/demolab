# Developing demolab

This repo is both the **demolab template** and demolab's own source. To work on **engine
features** (`demolab-engine/`) you need a real lab to build against — but the shipped repo is
engine-only. There are two ways to get one, depending on what you're doing.

## Serve the shipped demo (no copies) — the usual case

```sh
task dev:demo-site      # symlinks demolab-engine/scaffold/demo in, serves it, cleans up on exit
```

This points the dev server at the **shipped demo** (`demolab-engine/scaffold/demo/`) via symlinks —
one source of truth, no duplicated files at the root. Edit the engine (`demolab-engine/build/lib.typ`,
`style.css`, `main.typ`, `build.py`) *or* the demo content (in `scaffold/demo/`) and it hot-reloads.
On Ctrl-C the symlinks and build outputs are torn down, so the tree is left clean. Nothing is
committed, and the demo folder is never written to.

Use this for almost all engine work — you're iterating on the engine against real content without
polluting the root.

## Full sandbox — when you need to *run* the experiments

`dev:demo-site` only symlinks what's needed to *serve* (writings + figures). To also **run** the
demo's experiments (regenerate figures, tweak a runner), materialise the whole thing, which brings
`tools/` + `experiments/` and their Python deps:

```sh
task add-demo-content   # copy the worked demo (skeleton + demo) to the repo root
task dev                # serve whatever content is at the root
uv run python experiments/exp000.py   # re-run a runner, etc.
```

This *copies* the demo to the root, so keep it out of git with a **local** exclude — never the
shipped `.gitignore` (users inherit that, and ignoring `writings/` there would wreck their repos).
`.git/info/exclude` is per-clone and never committed:

```sh
cat >> .git/info/exclude <<'EOF'
# local dev sandbox — never committed
/writings/
/experiments/
/tools/
/artifacts/
/demolab.yaml
/HOUSESTYLE.local.md
EOF
```

Tear it down with `task clear-demo-content` (or `rm -rf writings experiments tools artifacts`).

## Why the content has to live at the root

Writings use root-relative paths (`/demolab-engine/…`, `/artifacts/…`) and Typst confines every read
to `--root`, which must be the repo root. So the content and the real engine have to share that one
root. The nuance that makes `dev:demo-site` work: a symlink whose target resolves **inside** `--root`
is fine (the demo's `writings/` → `scaffold/demo/writings/`, still under the repo root), whereas a
symlink pointing **outside** it — e.g. a tidy `dev/` subfolder linking up to the engine — trips
Typst's containment check. That's why we symlink the content *in*, not the engine *out*.
