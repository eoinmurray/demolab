# Developing demolab

This repo is both the **demolab template** and demolab's own source. To work on **engine
features** (`demolab-engine/`) you need a real lab to build against — but the shipped repo is
engine-only. There are two ways to get one, depending on what you're doing.

## Serve the shipped demo (no copies) — the usual case

```sh
task dev:demo-site      # serves demolab-engine/scaffold/demo directly
```

This reads content from and writes build output to **shipped demo**
(`demolab-engine/scaffold/demo/`) via `DEMOLAB_ROOT` — no symlinks, copies, or `temp/` staging
at the repo root. Edit the engine (`demolab-engine/build/lib.typ`, `style.css`, `main.typ`,
`build.py`) *or* the demo content (in `scaffold/demo/`) and it hot-reloads. Build scratch lands
in `scaffold/demo/temp/` and the site in `scaffold/demo/artifacts/site/` (both gitignored).

Use this for almost all engine work — you're iterating on the engine against real content without
polluting the root or conflicting with a local `add-demo-content` sandbox.

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

## Why demo preview doesn't touch the repo root

Writings use root-relative paths (`/demolab-engine/…`, `/artifacts/…`) and Typst confines every read
to `--root`. The shipped demo lives under `demolab-engine/scaffold/demo/`, so `dev:demo-site` sets
`DEMOLAB_ROOT` there: the build reads writings, data assets, and `demolab.yaml` from that tree,
passes a `content-prefix` into Typst so `/artifacts/data/…` resolves correctly, and serves from
`scaffold/demo/artifacts/site/`. Typst `--root` stays at the repo checkout so the engine paths
still work.
