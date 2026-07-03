# Developing demolab

This repo is both the **demolab template** and demolab's own source. To work on **engine
features** (`demolab-engine/`) you need a real lab to build against — but the shipped repo is
engine-only. Stand one up **in place** so it uses the *live* engine:

```sh
task add-demo-content   # scaffold the worked demo at the repo root
task dev                # build + hot-reload against demolab-engine/ — edit lib.typ etc. and see it live
```

Now edits to `demolab-engine/build/` (`lib.typ`, `style.css`, `main.typ`, `build.py`) show up on the
next build/reload, against real content.

**Keep the sandbox out of git with a _local_ exclude** — never the shipped `.gitignore` (users
inherit that, and ignoring `writings/` there would wreck their repos). `.git/info/exclude` is
per-clone and never committed:

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

`git status` then stays clean while you iterate, and your engine edits commit normally. Tear the
sandbox down anytime with `task clear-demo-content`.

**Why in place, not a `dev/` subfolder:** writings use root-relative paths (`/demolab-engine/…`,
`/artifacts/…`) and Typst requires the compiled `main.typ` to physically sit under `--root`, so the
content and the real engine must share one root. A symlinked subfolder trips Typst's containment
check on the compiled source.
