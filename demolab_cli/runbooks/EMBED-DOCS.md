# Runbook: Embedding as a docs subfolder

> Use demolab as a docs subfolder inside another project.

## When to use
When you want demolab living inside another project as its docs/wiki subfolder rather than as
a standalone repo. The tree is path-portable — every tool/writing resolves paths relative to
the repo root (`typst --root`), and the built site uses **relative links**, so it works under
any URL path with no base config.

## What it does

1. **Place it.** Run `uvx demolab-cli init` inside the host project's empty `docs/` folder —
   `init` works in any empty directory, and the docs lab gets its own `pyproject.toml`
   (depending on `demolab-cli`). It detects it's inside an existing repo and skips its usual
   `git init`. The `docs/.github/` it lays down is inert there (GitHub only reads workflows
   at the repo root) — delete it, and don't run `demolab deploy-setup` (its workflows also
   assume the lab is the repo root).
2. **Run from inside the subfolder.** `demolab` finds the lab root by walking up to
   `demolab.yaml`, so run everything from `docs/`:
   `cd docs && demolab install && demolab build` (or `demolab dev`). Output lands in
   `docs/artifacts/site/`.
3. **Deploy from the HOST repo.** Add a Pages workflow to the *host* repo that installs
   `typst` + `uv`, runs `cd docs && uv sync && uv run demolab build`, and publishes
   `docs/artifacts/site/` — model it on the `deploy.yml` that `demolab deploy-setup` drops
   in a standalone lab. Enable Pages on the host (*Settings → Pages*).

Notes: one Pages site per repo — if the host already uses Pages, deploy the docs from a
dedicated repo.

---

## Agent contract
- **Triggers** — `EMBED-DOCS`, "embed demolab as a docs site", "use this as a wiki subfolder",
  "drop this into my project as docs".
- **Gates** — none.
- **Report & apply** — deployment touches the *host* repo (Pages workflow + Pages settings).
  One Pages site per repo: if the host already uses Pages, deploy the docs from a dedicated
  repo instead.
