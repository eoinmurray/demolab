# STRUCTURE — the lab's filesystem and layout

A map of what every part of a demolab lab is and where it lives. For the *why* behind the
zones (what the package owns, what's yours) see [`RULES.md`](RULES.md) §3; for term
definitions see [`GLOSSARY.md`](GLOSSARY.md). Bracketed `[§x]` / `[Gn]` / `[Hn]` tags point
at the rule that governs each path.

The engine ships in the **`demolab-cli` package** — a lab is content only. `demolab init`
lays the structure below down in one shot; `demolab scaffold` re-lays the bare structure
non-destructively; `demolab add-demo-content` also overlays the worked demo. The demo +
skeleton live *inside the package* (so they version with it) and double as the engine's
smoke test. See [Scaffolding](#scaffolding) below.

## The tree

A lab, once initialised:

```
my-lab/
├── tools/                  the science — one directory per tool          [§3.4, §4, §8, G23]
│   ├── neuron/               tool.py (the CLI) + test_neuron.py
│   └── mujoco/               tool.py + test_mujoco.py
├── experiments/            the runners — one expNNN.py per experiment     [§3.4, §7, G22]
│   ├── expNNN.py             runs a tool's CLI, renders figures, stages artifacts/data/expNNN/
│   ├── helpers/              shared runner code (not experiments) — style.py (figure style, H15), provenance.py (§4.7)
│   └── playground.py         the interactive Streamlit demo (exempt from the contract, §8.5, G16)
├── writings/               the writeups — one .typ per entry, by id       [§6, G24, HOUSESTYLE]
│   ├── expNNN.typ            an experiment writeup (#let meta + #let body)
│   ├── arNNN.typ             an article — prose-only, no runner            [G1]
│   └── arNNN.slide.typ       a deck — Touying slides → standalone PDF      [G9]
├── artifacts/              the committed record of every run              [§5]
│   ├── data/<id>/            figures + numbers.json + run.sh (+ any mp4) — the publisher-neutral record  [§5.1, G18]
│   ├── pdfs/                 compiled PDFs (per entry + book.pdf) — shareable                    [§5.3]
│   └── site/                 the built web site — GITIGNORED (CI rebuilds + deploys it)          [§5.3]
├── demolab.yaml            branding + collections config — and the LAB MARKER the CLI walks up to  [§3.3, §6.5, G4]
├── HOUSESTYLE.local.md     optional — your house-style overrides (extend/replace)  [§3.3]
├── AGENTS.md               the thin agent entry point — points at `demolab docs`   [§3.3]
├── CLAUDE.md               a thin pointer to AGENTS.md (for Claude Code)    [§3.3]
├── README.md               your lab's overview                              [§3.3]
├── pyproject.toml          your deps + demolab-cli (provides the `demolab` command)   [§1.1, §1.3]
├── uv.lock                 the resolved lockfile — pins the engine version, too
├── .github/workflows/      CI — tests; deploy workflows land via `demolab deploy-setup`  [§5.3]
├── .gitignore              ignores .demolab/, temp/, artifacts/site/, .venv/, …
├── .demolab/               engine staging, GITIGNORED + machine-managed — never edit   [§3.2]
│   ├── lib.typ               the helpers your writings import ("/.demolab/lib.typ")
│   ├── style.css · favicon.svg · cite-popover.js   the web theme assets
│   └── VERSION               stamp — a version change triggers a refresh on the next build
└── temp/                   short-lived run scratch — GITIGNORED             [§5.1]
    ├── <tool>/<cmd>/          a tool run's raw output (config/output/manifest/log/run.sh/data/mp4)  [§4.3]
    ├── bundle/               build scratch: staged main.typ + index.json manifest + compiled deck PDFs
    └── demo-preview/          the materialised demo `demolab dev --demo` serves
```

The engine itself — build code, `main.typ`/`lib.typ` sources, runbooks, guides, scaffold —
lives in the installed `demolab-cli` package (site-packages), reached via `demolab docs`
[§3.1]. There is no engine directory in the lab.

## Reading the tree

**S1 — Split by kind, not by pipeline stage.** Code (`tools/`), runners (`experiments/`), prose (`writings/`), and the record (`artifacts/`) each have a home — a result isn't scattered across a per-experiment folder. What ties an experiment together is its **id**, not a directory.

**S2 — One id threads through, by name.** `experiments/exp000.py` runs it → `artifacts/data/exp000/` holds its figures + `numbers.json` → `writings/exp000.typ` writes it up. Ids: `expNNN` (experiment), `arNNN` (article), `arNNN.slide` (deck). Same id, three places.

**S3 — Three kinds of writing.** `expNNN.typ` (an experiment's writeup, reads its run), `arNNN.typ` (a prose-only article), and `arNNN.slide.typ` (a deck, compiled to a standalone PDF). The build discovers the first two as bundle entries (`#let meta` + `#let body`); a `.slide.typ` is listed but rendered only as PDF (§6.1, G24).

**S4 — Committed vs regenerable.** *Committed* (the record CI can't reproduce, so it must be in git): `artifacts/data/` and `artifacts/pdfs/`. *Gitignored* (rebuilt on demand): `temp/`, `artifacts/site/`, and `.demolab/`. Never commit scratch; never rely on it surviving (§5.1, §5.3).

**S5 — The package vs your stuff.** The engine is the installed `demolab-cli` package — you never hand-edit it, and updating it is a dependency bump (§3.1). The gitignored `.demolab/` staging dir is the CLI's, not yours (§3.2). Everything else in the tree is yours: `tools/`, `experiments/`, `writings/`, `artifacts/`, `demolab.yaml`, and the root stubs `demolab init` laid down (§3.3).

**S6 — Where the build goes.** `demolab build` globs `writings/*.typ` into `temp/bundle/index.json`, stages the engine's `main.typ` beside it, and compiles it to three targets in one pass: the web site → `artifacts/site/`, per-entry PDFs + `book.pdf` → `artifacts/site/pdfs/` (mirrored to `artifacts/pdfs/`). On an empty (freshly-initialised) tree the build still succeeds — it emits a single `index.html` with a friendly empty state, and skips `all.html`/collection pages/`book.pdf`. CI deploys `artifacts/site/` to GitHub Pages (§5.2, §5.3).

## Scaffolding

The content tree is materialised on demand from the package's scaffold data.

**S7 — Two overlays, one command each.** `skeleton/` is the bare structure (empty `writings/` `experiments/` `tools/` `artifacts/` + the config templates `demolab.yaml`, `HOUSESTYLE.local.md`, `experiments/helpers/style.py` + `experiments/helpers/provenance.py`); `demolab scaffold` copies it into the lab root non-destructively (keep-existing, so re-running never clobbers your work; `demolab init` runs it as part of laying a new lab down). `demo/` is the worked example; `demolab add-demo-content` runs `scaffold` then overlays it. `demolab clear-demo-content` deletes exactly the paths in the package's `demo-manifest.json` — nothing you authored is listed there, so it can't touch your content.

**S8 — The demo is the engine's test.** Because `demo/` lives inside the package, it versions with the engine and can't drift from it. The engine's smoke test (run in the demolab-cli repo's CI) assembles skeleton + demo in a throwaway tree via `DEMOLAB_ROOT` and builds it end-to-end — so the shipped example is also the integration smoke test. It also asserts the empty (skeleton-only) tree builds its empty-state homepage. Read the demo any time with `demolab docs DEMO`.
