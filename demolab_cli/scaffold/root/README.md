# My lab

A [demolab](https://github.com/eoinmurray/demolab) lab notebook: Python experiments produce
per-run artifacts; Typst publishes them as a website, per-entry PDFs, and a book.

## Working here

```sh
uv sync              # install dependencies + the `demolab` command
demolab dev          # live-preview the site at http://localhost:3000
uv run python experiments/exp000.py   # run an experiment end-to-end
demolab build        # build the site + PDFs into artifacts/
```

Run `demolab` for the full command list. If you work with a coding agent, it reads
[AGENTS.md](AGENTS.md) and drives the runbooks (`demolab docs`) — typing `HELP` in an agent
chat shows the menu.

## Layout

- `experiments/` — runners that stage `artifacts/data/<id>/` (figures + numbers)
- `writings/` — the write-ups (`<id>.typ`), published by `demolab build`
- `tools/` — reusable science shared by experiments
- `artifacts/` — the committed record: `data/` per run, `pdfs/` compiled deliverables
- `demolab.yaml` — branding + collections (also marks this directory as a lab)

The engine ships in the `demolab-cli` package — nothing to vendor or maintain here.
Updating: `uv lock --upgrade-package demolab-cli && uv sync`.
