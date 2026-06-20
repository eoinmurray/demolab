# demolab

**A lab notebook system you run with a coding agent.**

A Python CLI runs an experiment and drops a self-contained folder of artifacts; a notebook runner bundles them; an Astro site publishes a clean post for each one — figures, parameters, and the headline numbers included. It's built to be operated by a human *and* an agent (Claude Code, Cursor, aider, …), and it's designed to fork.

```
src/
├── clis/        Python CLIs — one experiment tool per folder
├── notebooks/   runners that turn CLI output into a post
├── artifacts/   per-run outputs (gitignored)
└── docs/        the Astro site that publishes it all
```

## The loop

> a **CLI** runs an experiment → drops **artifacts** → a **notebook** bundles them → the **site** publishes a post

Those four steps stay decoupled through one small contract (see [`CONTRIBUTORS.md`](CONTRIBUTORS.md)). That's the whole idea.

## Quickstart

```sh
uv sync                                       # Python deps
uv run python src/notebooks/nb000.py          # run a notebook end-to-end
cd src/docs && bun install && bun run dev      # open http://localhost:4321/demolab
```

Toolchain: **`uv`** for Python, **`bun`** for the site — never `pip`/`npm` directly.

## Start with your agent

Fork it, open it in your coding agent, and just say:

| Say… | …and your agent will | Guide |
|------|----------------------|-------|
| **“how do I get started”** | set you up, run the demo, and help you publish your first notebook | [`GETTING_STARTED.md`](GETTING_STARTED.md) |
| **“migrate my code”** | import an existing repo, one experiment at a time — wrapping, not rewriting | [`MIGRATING.md`](MIGRATING.md) |
| **“embed demolab as a docs site”** | drop it into another project as a `wiki/` and publish to its GitHub Pages | [`EMBEDDING.md`](EMBEDDING.md) |
| **“update demolab”** | review new upstream features and reimplement the ones you want, your way | [`UPDATING.md`](UPDATING.md) |

Every guide is a plain runbook — you can follow it by hand too.

## Reference

- [`CONTRIBUTORS.md`](CONTRIBUTORS.md) — the CLI ↔ notebook contract, the `numbers.json` schema, and how to add notebooks and CLI tools.
- [`CHANGELOG.md`](CHANGELOG.md) — the versioned catalog of framework features.

---

*Forking this for your own lab? Start your agent and say “how do I get started.”*
