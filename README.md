# demolab

**Turn your simulations into reproducible, published, citable results — without being a software engineer.**

demolab is a lab notebook system for computational scientists. You write your model or experiment once as a small Python program; demolab runs it, captures everything the run produced, and publishes a clean web page for it — figures, parameters, headline numbers, and proper mathematical notation included. You drive the whole thing by talking to a coding agent (Claude Code, Cursor, and the like), so you never have to hand-wire a website or a build system.

It's designed for people doing computational neuroscience, neuromorphic engineering, control systems — anyone who runs experiments in code and wants to share results that others can actually reproduce.

**▶ See it live: [demolab.eoinmurray.info](https://demolab.eoinmurray.info/)**

> **A note on jargon.** A **tool** here is just a small Python program — your core simulator or experiment. A **notebook** is _not_ a Jupyter notebook: it's a pair of files (a short runner script plus a page of prose). A **coding agent** is an AI assistant that reads this repo and does the setup and wiring for you. A **static site** is plain HTML — no server to run, free to host.

## The structure

Everything is top-level, grouped by what it *is*:

```
core/          your tools — the science (models, solvers); one folder per tool
scripts/       the runners — nbNNN.py runs a tool and stages its results
entries/       the writeups — nbNNN.mdx (web) or nbNNN.typ (PDF), paired to a script by id
artifacts/     the kept record — each run's figures + numbers.json (committed)
temp/          short-lived run scratch (regenerated, gitignored)
demolab-web/   the website engine (Astro) — you rarely open this
```

One experiment threads through by id: `scripts/nb000.py` runs it → `artifacts/nb000/` holds its figures + numbers → `entries/nb000.mdx` writes it up. Split by *kind* (code · data · prose), not by pipeline stage.

The other files at the repo root: **`CLAUDE.md`** (the operating manual your agent follows), **`CONTRIBUTORS.md`** (the rules for adding a tool or entry), **`CHANGELOG.md`**, and **`Taskfile.yml`** (handy commands). Everything else is inside `demolab-web/`.

## The two rules

Learn these two things and the rest follows:

1. **Core logic lives in tools; exploration lives in notebooks.** A tool owns the reusable computation — your model, your solver, your simulation. A notebook _runs_ that tool (often several times, with different parameters) and publishes what comes out. Keep the science in the tool; keep the storytelling in the notebook.
2. **A notebook is a paired `.py` + document.** The `.py` is the runner that executes the tool; the document is what gets published (prose, figures, tables, math). By default that document is an `.mdx` page for the website — but it can just as well be LaTeX or Typst if you'd rather produce a PDF (see [How publishing works](#how-publishing-works)). Same name, two files, one result.

## The main pillars

**1. Tools do the science, notebooks tell the story.** You write a simulation once. Any number of notebooks can then drive it — sweep a parameter, change an input, compare regimes — each publishing its own result. Your computation never gets copy-pasted or forked; it stays in one place and gets _called_.

**2. Every run is reproducible and self-describing.** When a tool runs, it drops a self-contained folder: the exact parameters used (`config.json`), the results (`output.json`), the figure, a log, and a `run.sh` that re-runs it identically. A small manifest declares which figure and which numbers matter — and it's _validated_, so a run can never misreport what it produced. The numbers in your published page come straight from that folder, so your prose can't drift out of sync with your results. And each tool ships tests (`task test`), so the primitives that produce those numbers are checked, not just trusted.

**3. Results publish themselves as a website.** Each notebook becomes a clean post — figures, a parameter table, the headline numbers, and real typeset mathematics (LaTeX/KaTeX). It's a plain static site, so it hosts free on GitHub Pages and there's nothing to keep running. Share a link; cite a result.

**4. A coding agent does the wiring.** This is what makes it usable if you're not a developer. You don't set up build tools, write config, or debug a website. You open the repo in a coding agent and say what you want in plain language — it follows a runbook step by step and does the plumbing, checking each step with you.

## How publishing works

Every tool run drops a self-contained folder into `temp/` (scratch — regenerated on each run). A notebook's runner then stages the bits worth keeping — the headline figure(s) and a small `numbers.json` — into **`artifacts/<id>/`**. That folder is the *publisher-neutral record*: it's committed to git and it's the single source every publisher reads from. The publisher on top is swappable.

**The default publisher is [Astro](https://astro.build/), a static-site generator** (it turns content into plain HTML ahead of time):

1. The runner stages the bundle into `artifacts/<id>/`.
2. The notebook's page (`.mdx` — Markdown with a little extra power) *imports* the figure straight from `artifacts/`, so the asset is fingerprinted and the URL is always correct.
3. `bun run build` turns every page into static HTML in `dist/` — no database, no server to keep alive.
4. A GitHub Action publishes `dist/` to GitHub Pages on every push. That's the live site.

You mostly touch step 2 (writing the page); your agent handles the rest.

### Prefer a PDF? Swap the publisher.

The website isn't load-bearing — **the contract is**: every run leaves a figure and machine-readable numbers in `artifacts/`. Anything that can read those can publish them. To produce a **PDF** instead, keep your tools and runners as they are and swap only the document half of the notebook:

- **Typst** — *shipped as example `nb004`.* Typst reads JSON natively, so [`entries/nb004.typ`](entries/nb004.typ) does `#let d = json("/artifacts/nb004/numbers.json")` and drops `#d.lif.firing_rate_hz` into the text, with `#image("/artifacts/nb004/lif.png")` for the figure. Its runner [`nb004.py`](scripts/nb004.py) runs the tool, stages the same bundle, and compiles the PDF (`uv run python scripts/nb004.py`). It's the *same* LIF result as the web notebook `nb000` — just a different publisher — and because the table is read from the run, the numbers can't drift.
- **LaTeX** — *outline.* Same idea, one extra step: LaTeX can't read JSON directly, so the runner also emits a small `numbers.tex` of macros (e.g. `\newcommand{\firingRate}{90.0}`) next to the figure; the `.tex` `\input`s it and `\includegraphics` the figure. Build with `tectonic` or `pdflatex`.

For crisp print output, have the tool save a **vector** figure (`savefig(..., format="pdf")` or SVG) instead of PNG. Either way the two rules still hold — a notebook is a runner plus a document; only the document format and the build command change.

## Quickstart

**Prerequisites** — three command-line tools:

- [`uv`](https://docs.astral.sh/uv/) — Python environment + dependencies
- [`bun`](https://bun.sh) — the website
- [`go-task`](https://taskfile.dev) — the shortcut commands below (`brew install go-task`)

Then:

```sh
task install          # install Python + website dependencies
task run -- nb000     # run a notebook end-to-end
task dev              # open http://localhost:3000
```

`task --list` shows the rest (`build`, `test`, …). Under the hood it's **`uv`** for Python and **`bun`** for the website — never `pip` / `npm` directly (they'd use the wrong, unpinned versions). Prefer them raw? `uv sync`, `uv run python scripts/nb000.py`, `cd demolab-web && bun run dev`.

## Working in this repo — just ask your agent

demolab is meant to be operated by a coding agent. Fork it, open it in your agent, and say the word — the agent follows the matching runbook in [`CLAUDE.md`](CLAUDE.md), one step at a time, verifying as it goes. (Every runbook is plain enough to follow by hand, too.)

| Say…                               | …and your agent will                                                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **“how do I get started”**         | set up the toolchain, run the demo so you see the loop, help you publish your **own** first notebook, then clear the shipped demo |
| **“migrate my code”**              | bring an existing repo in one experiment at a time — _wrapping_ your functions, not rewriting your science                        |
| **“embed demolab as a docs site”** | drop it into another project as a `wiki/` subfolder and publish to that repo's GitHub Pages                                       |
| **“update demolab”**               | review new upstream features and reimplement the ones you want, your way                                                          |

## What's yours, and what's the framework

Everything under `core/`, `scripts/`, `entries/`, `artifacts/`, and `temp/` is **example content** — yours to delete and replace with your own science. The **framework** (the operating manual, the contract, the website engine) lives elsewhere and stays put. So when you clear out the demo to make the lab your own, nothing about setup, migrating, or publishing breaks. Start your agent, say _"how do I get started,"_ and it walks you through exactly that.

## Reference

- [`CLAUDE.md`](CLAUDE.md) — the operating manual: toolchain rules and the four runbooks.
- [`CONTRIBUTORS.md`](CONTRIBUTORS.md) — the tool ↔ notebook contract, the `numbers.json` schema, authoring posts, and how to add notebooks and tools.
- [`CHANGELOG.md`](CHANGELOG.md) — the versioned catalog of framework features.

## License

[MIT](LICENSE) — free to use, fork, and adapt for your own lab.

---

_Forking this for your own lab? Open your agent and say “how do I get started.”_
