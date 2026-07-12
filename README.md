# Demolab

**A lab notebook for computational science — reproducible results, published and citable, run by a coding agent instead of a build system.**

> **Coding agent setting someone up?** Run `uvx demolab-cli docs GETTING-STARTED`, read the file it prints, and follow it strictly, step by step. *(Human, setting up by hand? See [Quickstart](#quickstart).)*

You write a model or experiment once as a small program. Demolab runs it, captures everything it produced, stamps it with the exact code version, and publishes a clean page — figures, numbers, and real typeset maths — to both the web and PDF. The numbers on the page are read from the run, so they can't drift. You drive it all by talking to a coding agent; there's no web development or build config to touch.

## Quickstart

Open your coding agent in an empty folder and paste:

> Run `uvx demolab-cli init` here, then follow its GETTING-STARTED runbook strictly.

It lays your lab down, walks you through the toolchain (`uv`, `typst`) and your first experiment, one step at a time.

<details>
<summary><b>Set it up by hand instead?</b></summary>

Install [`uv`](https://docs.astral.sh/uv/) and [`typst`](https://typst.app) (`brew install uv typst`), then:

```sh
mkdir my-lab && cd my-lab
uvx demolab-cli init   # lab structure + git init — yours from the first commit
uv sync                # installs the deps and the `demolab` command
```

Then write your first experiment — ask your agent to follow GETTING-STARTED, or model one on a shipped reference (`demolab docs STARTERS` prints the dir; `monte-carlo-pi` is the canonical starter). `demolab dev` serves the site as you go. The engine lives in the `demolab-cli` package — updating it is `uv lock --upgrade-package demolab-cli && uv sync`.

</details>

## What to ask your agent

Open your lab in your agent and say a runbook's name — it follows that runbook one step at a time. `demolab docs` lists them all (each is a plain file shipped in the package; `demolab docs <NAME>` prints its path). In this repo they live under [`demolab_cli/runbooks/`](demolab_cli/runbooks/).

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
| **UPDATE** | update the engine package, leaving your content untouched |

## How it works

One decoupled loop: **a tool computes → drops data → an experiment writes it up → the site publishes it.** Every run records its exact parameters and the git commit it came from (stamped on the page), and tables read their numbers straight from the run — so prose and results can't disagree. A single Typst pass emits a website, a PDF per entry, and a book, all sharing the same live numbers.

The detail lives in the guides (in a lab: `demolab docs <NAME>`; in this repo, the files under `demolab_cli/guides/`):

- **[RULES.md](demolab_cli/guides/RULES.md)** — the tool ↔ experiment contract, schemas, provenance, and how to add things.
- **[STRUCTURE.md](demolab_cli/guides/STRUCTURE.md)** — the annotated file tree.
- **[HOUSESTYLE.md](demolab_cli/guides/HOUSESTYLE.md)** — prose, maths, and figure style.
- **[AGENTS.md](AGENTS.md)** — the agent entry point.

## Commands

`demolab` shows them all. The everyday ones: `init`, `docs`, `install`, `scaffold`, `dev`, `build`, `test`. Run an experiment end-to-end directly: `uv run python experiments/expNNN.py` (there's no `demolab run` wrapper).

## License

[MIT](LICENSE) — free to use, fork, and adapt for your own lab.
