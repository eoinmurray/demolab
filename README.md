# demolab

**A lab notebook system you run with a coding agent.**

A Python tool runs an experiment and drops a self-contained folder of artifacts; a notebook runner bundles them; an Astro site publishes a clean post for each one — figures, parameters, and the headline numbers included. It's built to be operated by a human *and* an agent (Claude Code, Cursor, aider, …), and it's designed to fork.

**▶ See it live: [demolab.eoinmurray.info](https://demolab.eoinmurray.info/)**

```
src/
├── tools/       Python tools — one experiment per folder
├── notebooks/   runners that turn tool output into a post
├── artifacts/   per-run outputs (gitignored)
└── docs/        the Astro site that publishes it all
```

## The loop

> a **tool** runs an experiment → drops **artifacts** → a **notebook** bundles them → the **site** publishes a post

Those four steps stay decoupled through one small contract (see [`CONTRIBUTORS.md`](CONTRIBUTORS.md)). That's the whole idea.

## Quickstart

```sh
uv sync                                       # Python deps
uv run python src/notebooks/nb000.py          # run a notebook end-to-end
cd src/docs && bun install && bun run dev      # open http://localhost:4321
```

Toolchain: **`uv`** for Python, **`bun`** for the site — never `pip`/`npm` directly.

## Working in this repo — just ask your agent

demolab is meant to be operated by a coding agent. Fork it, open it in your agent, and say the word — the agent follows the matching runbook in [`CLAUDE.md`](CLAUDE.md), driving it one step at a time. (Every runbook is plain enough to follow by hand too.)

| Say… | …and your agent will |
|------|----------------------|
| **“how do I get started”** | set up the toolchain, run the demo so you see the loop, help you publish your **own** first notebook, then clear the shipped demo |
| **“migrate my code”** | bring an existing repo in one experiment at a time — *wrapping* your functions, not rewriting your science |
| **“embed demolab as a docs site”** | drop it into another project as a `wiki/` subfolder and publish to that repo's GitHub Pages |
| **“update demolab”** | review new upstream features and reimplement the ones you want, your way |

The runbooks live in [`CLAUDE.md`](CLAUDE.md) — that's the operating manual. Everything under `src/docs/content/`, `src/tools/`, `src/notebooks/`, and `src/artifacts/` is example content: yours to delete and replace. The framework (this manual, the contract, the Astro engine) stays put, so clearing the demo never breaks onboarding.

## Reference

- [`CLAUDE.md`](CLAUDE.md) — the operating manual: toolchain rules and the four runbooks.
- [`CONTRIBUTORS.md`](CONTRIBUTORS.md) — the tool ↔ notebook contract, the `numbers.json` schema, authoring posts, and how to add notebooks and tools.
- [`CHANGELOG.md`](CHANGELOG.md) — the versioned catalog of framework features.

---

*Forking this for your own lab? Open your agent and say “how do I get started.”*
