# Demolab

**A lab notebook for computational science — reproducible results, published and citable, run by a coding agent instead of a build system.**

> **Coding agent setting someone up?** Open **[GETTING-STARTED.md](demolab-engine/runbooks/GETTING-STARTED.md)** and follow it strictly, step by step. *(Human, setting up by hand? See [Quickstart](#quickstart).)*

You write a model or experiment once as a small program. Demolab runs it, captures everything it produced, stamps it with the exact code version, and publishes a clean page — figures, numbers, and real typeset maths — to both the web and PDF. The numbers on the page are read from the run, so they can't drift. You drive it all by talking to a coding agent; there's no web development or build config to touch.

## Quickstart

Open your coding agent in an empty folder and paste:

> Clone github.com/eoinmurray/demolab and follow its GETTING-STARTED.md strictly.

It installs the toolchain (`uv`, `typst`, `go-task`), makes you your own copy, and walks you through setup and your first experiment, one step at a time.

<details>
<summary><b>Set it up by hand instead?</b></summary>

Install [`uv`](https://docs.astral.sh/uv/), [`typst`](https://typst.app), and [`go-task`](https://taskfile.dev) (`brew install uv typst go-task`), then make a *fresh* copy — don't plain-`git clone`, it drags demolab's history and remote along:

```sh
git clone --depth 1 https://github.com/eoinmurray/demolab my-lab
rm -rf my-lab/.git my-lab/.github/workflows/landing.yml  # strip history + upstream deploy workflow
cd my-lab && git init && git add -A && git commit -m "Start my lab from demolab"
```

Then `task add-demo-content && task run -- exp000 && task dev` to see the loop. `task clear-demo-content` wipes the demo; `task scaffold` gives a bare tree.

</details>

## What to ask your agent

Open the repo in your agent and say a runbook's name — it follows that runbook one step at a time. Each is a plain file under [`demolab-engine/runbooks/`](demolab-engine/runbooks/) you can also read yourself.

| Say… | …and it will |
|------|--------------|
| **GETTING-STARTED** | set you up end to end: scaffold, your first experiment live on a page, brand, publish |
| **TOUR** | guided walkthrough of the lab — what's here, what it found, where to start |
| **MIGRATE-CODE** | bring an existing codebase in, one experiment at a time |
| **FROM-JUPYTER** | launder a Jupyter notebook into a reproducible, seeded experiment |
| **FROM-PAPER** | scaffold experiments to reproduce a paper's key result in your stack |
| **MIGRATE-STACK** | write your tools in MATLAB / Julia / R / Octave instead of Python |
| **EMBED-DOCS** | drop demolab into another project as a `docs/` site |
| **NEXT** | read your whole arc and propose the next experiments worth running |
| **GROUND-CLAIMS** | find the source sentences behind each citation |
| **LINT** | check your writeups against the house style |
| **DOCTOR** | audit the repo against the conventions |
| **RED-TEAM** | adversarially check a result holds up before you publish it |
| **STEELMAN** | build the strongest honest case for a result, so you don't under-sell it |
| **UPDATE** | pull the latest engine, leaving your content untouched |

## How it works

One decoupled loop: **a tool computes → drops data → an experiment writes it up → the site publishes it.** Every run records its exact parameters and the git commit it came from (stamped on the page), and tables read their numbers straight from the run — so prose and results can't disagree. A single Typst pass emits a website, a PDF per entry, and a book, all sharing the same live numbers.

The detail lives in the guides:

- **[RULES.md](demolab-engine/guides/RULES.md)** — the tool ↔ experiment contract, schemas, provenance, and how to add things.
- **[STRUCTURE.md](demolab-engine/guides/STRUCTURE.md)** — the annotated file tree.
- **[HOUSESTYLE.md](demolab-engine/guides/HOUSESTYLE.md)** — prose, maths, and figure style.
- **[AGENTS.md](AGENTS.md)** — the agent entry point and full runbook index.

## Commands

`task --list` shows them all. The everyday ones: `install`, `scaffold` · `add-demo-content` · `clear-demo-content`, `run -- expNNN`, `dev`, `build`, `test`.

## License

[MIT](LICENSE) — free to use, fork, and adapt for your own lab.
