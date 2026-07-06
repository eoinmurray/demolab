# AGENTS.md

Demolab — an agent-operated lab notebook for computational science. This file is the
thin entry point; the substance lives in the engine so it updates cleanly (_"update
demolab"_). **Read the rules before working here.**

**Rules, contract & how-tos** → [`demolab-engine/guides/RULES.md`](demolab-engine/guides/RULES.md) — the single conventions doc: toolchain, the framework/content firewall, commits, the tool ↔ experiment contract + schemas, and how to add a tool / experiment / writing. Unfamiliar with a term (tool, experiment, deck, collection, provenance…)? → [`demolab-engine/guides/GLOSSARY.md`](demolab-engine/guides/GLOSSARY.md). Authoring a writing? → [`demolab-engine/guides/HOUSESTYLE.md`](demolab-engine/guides/HOUSESTYLE.md) for prose/math/figure style (a root `HOUSESTYLE.local.md`, if present, extends or replaces it — read it too). Authoring a slide deck? → [`demolab-engine/guides/SLIDES.md`](demolab-engine/guides/SLIDES.md) for deck conventions, layouts, and sizing. New to the layout? → [`demolab-engine/guides/STRUCTURE.md`](demolab-engine/guides/STRUCTURE.md) for the annotated file tree. Stuck and need a human? → [`demolab-engine/guides/SUPPORT.md`](demolab-engine/guides/SUPPORT.md) (GitHub issues / email).

Two rules important enough to state here too:

- **Toolchain:** use `uv` (Python) and `typst` (publishing) via `task` (go-task). Never call `pip` / `python` / `python3` directly.
- **Commits:** author every commit as the human only — never a `Co-Authored-By:` / agent trailer, never an agent in the author/committer fields.

## Commands — type a NAME

demolab is driven by typing a **name in CAPS** (SCREAMING-KEBAB). Three commands:

- **`HELP`** — list the runbooks and guides below, one line each. The menu.
- **`<RUNBOOK>`** — a runbook name → **start it** and drive it step by step: run a step, show the result, confirm before the next. Never dump the whole runbook at once. E.g. `LINT`, `DOCTOR`, `GETTING-STARTED`.
- **`<GUIDE>`** — a guide name → **walk the user through it**: summarise it, go section by section, answer questions — don't just paste the file. E.g. `RULES`, `SLIDES`.

**The NAME is the command.** If the user's message is (or starts with) one of these names — `LINT`, `RULES`, `HELP` — that *is* the request: act on it, don't ask what they mean. The lower-case phrasings in the "also triggers on" column still work as aliases, but the CAPS name is canonical and always routes.

> **`GETTING-STARTED`** ("set up my lab", "how do I get started") means **following the runbook as a conversation** — orient the user, then ask the gated questions *in order* and wait for answers. **Do not autonomously clone, scaffold, install, run the demo, and report back** — that races past every choice the user is supposed to make (fresh-or-migrate, demo-or-clean, stack, branding, publish, what to compute). Read the runbook first; run nothing before its step-0 orient + ready-check.

### Runbooks — `NAME` starts it

| Name | Does | Also triggers on |
| ---- | ---- | ---------------- |
| [`GETTING-STARTED`](demolab-engine/runbooks/GETTING-STARTED.md) | set up a fresh lab, interactively | "set up my lab", "how do I get started" |
| [`TOUR`](demolab-engine/runbooks/TOUR.md) | walk through this repo | "tour", "walk me through this repo" |
| [`MIGRATE-CODE`](demolab-engine/runbooks/MIGRATE-CODE.md) | wrap an existing codebase | "migrate my code" |
| [`FROM-JUPYTER`](demolab-engine/runbooks/FROM-JUPYTER.md) | convert a notebook | "from jupyter", "convert my notebook" |
| [`FROM-PAPER`](demolab-engine/runbooks/FROM-PAPER.md) | reproduce a paper | "from paper", "reproduce this paper" |
| [`EMBED-DOCS`](demolab-engine/runbooks/EMBED-DOCS.md) | use demolab as a docs site | "embed demolab as a docs site" |
| [`MIGRATE-STACK`](demolab-engine/runbooks/MIGRATE-STACK.md) | switch language (MATLAB / R / Julia / …) | "migrate the stack to MATLAB" |
| [`GROUND-CLAIMS`](demolab-engine/runbooks/GROUND-CLAIMS.md) | back every claim with a run or citation | "ground my claims" |
| [`NEXT`](demolab-engine/runbooks/NEXT.md) | suggest what to run next | "what next", "what should I run next" |
| [`UPDATE`](demolab-engine/runbooks/UPDATE.md) | vendor the latest engine | "update demolab" |
| [`DOCTOR`](demolab-engine/runbooks/DOCTOR.md) | audit the structure against RULES | "doctor the repo" |
| [`LINT`](demolab-engine/runbooks/LINT.md) | audit the prose + figures vs the house style | "lint the writings" |
| [`RED-TEAM`](demolab-engine/runbooks/RED-TEAM.md) | attack the result's validity | "red-team", "critique this experiment" |
| [`STEELMAN`](demolab-engine/runbooks/STEELMAN.md) | make the strongest case for it | "steelman", "make the case for this" |

### Guides — `NAME` walks you through it

| Name | Covers |
| ---- | ------ |
| [`RULES`](demolab-engine/guides/RULES.md) | the contract, toolchain, firewall, how-tos |
| [`HOUSESTYLE`](demolab-engine/guides/HOUSESTYLE.md) | prose / math / figure style (the H-rules) |
| [`SLIDES`](demolab-engine/guides/SLIDES.md) | deck conventions + the layout catalog |
| [`STRUCTURE`](demolab-engine/guides/STRUCTURE.md) | the annotated file tree |
| [`GLOSSARY`](demolab-engine/guides/GLOSSARY.md) | the vocabulary |
| [`SUPPORT`](demolab-engine/guides/SUPPORT.md) | getting a human (issues / email) |
