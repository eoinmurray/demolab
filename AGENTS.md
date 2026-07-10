# AGENTS.md

Demolab — an agent-operated lab notebook for computational science. This file is the
thin entry point; the substance lives in the engine so it updates cleanly (_"update
demolab"_). **Read the rules before working here.**

**Rules, contract & how-tos** → [`demolab-engine/guides/RULES.md`](demolab-engine/guides/RULES.md) — the single conventions doc: toolchain, the framework/content firewall, commits, the tool ↔ experiment contract + schemas, and how to add a tool / experiment / writing. Unfamiliar with a term (tool, experiment, deck, collection, provenance…)? → [`demolab-engine/guides/GLOSSARY.md`](demolab-engine/guides/GLOSSARY.md). Authoring a writing? → [`demolab-engine/guides/HOUSESTYLE.md`](demolab-engine/guides/HOUSESTYLE.md) for prose/math/figure style (a root `HOUSESTYLE.local.md`, if present, extends or replaces it — read it too). Authoring a slide deck? → [`demolab-engine/guides/SLIDES.md`](demolab-engine/guides/SLIDES.md) for deck conventions, layouts, and sizing. New to the layout? → [`demolab-engine/guides/STRUCTURE.md`](demolab-engine/guides/STRUCTURE.md) for the annotated file tree. Stuck and need a human? → [`demolab-engine/guides/SUPPORT.md`](demolab-engine/guides/SUPPORT.md) (GitHub issues — the agent can file one for you via `gh`).

Two rules important enough to state here too:

- **Toolchain:** use `uv` (Python) and `typst` (publishing) via `task` (go-task). Never call `pip` / `python` / `python3` directly.
- **Commits:** author every commit as the human only — never a `Co-Authored-By:` / agent trailer, never an agent in the author/committer fields.

## Commands — type a NAME

demolab is driven by typing a **name in CAPS** (SCREAMING-KEBAB). Three commands:

- **`HELP`** — list the runbooks and guides below, one line each. The menu.
- **`<RUNBOOK>`** — a runbook name → **start it** and drive it step by step: run a step, show the result, confirm before the next. Never dump the whole runbook at once. E.g. `LINT`, `DOCTOR`, `GETTING-STARTED`.
- **`<GUIDE>`** — a guide name → **walk the user through it**: summarise it, go section by section, answer questions — don't just paste the file. E.g. `RULES`, `SLIDES`.

**The NAME is the command.** If the user's message is (or starts with) one of these names — `LINT`, `RULES`, `HELP` — that *is* the request: act on it, don't ask what they mean. The lower-case phrasings in the "also triggers on" column still work as aliases, but the CAPS name is canonical and always routes.

**Docs are the source of truth.** When the user is confused, stuck, or asks "how do I…" about operating demolab, check the runbook and guide tables *before* improvising an answer. If one covers it, ground your answer in it — cite it, or offer to start it — rather than explaining from memory. Don't turn every question into a runbook pitch; just don't answer from memory what a doc already answers.

> **`GETTING-STARTED`** ("set up my lab", "how do I get started") means **following the runbook as a conversation** — orient the user, then ask the gated questions *in order* and wait for answers. **Do not autonomously clone, scaffold, install, build an experiment, and report back** — that races past every choice the user is supposed to make (what to compute, branding, publishing). Read the runbook first; run nothing before its step-0 orient + ready-check.

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
| [`AUTORESEARCH`](demolab-engine/runbooks/AUTORESEARCH.md) | start / steer a research program | "start a research program", "set up autoresearch" |
| [`PLAN`](demolab-engine/runbooks/PLAN.md) | plan the next experiments + triage last night | "plan the next experiments", "triage last night" |
| [`NIGHT-SHIFT`](demolab-engine/runbooks/NIGHT-SHIFT.md) | work the queue overnight, autonomously | "work the queue overnight", "run tonight's experiments" |

### Guides — `NAME` walks you through it

| Name | Covers | Also triggers on |
| ---- | ------ | ---------------- |
| [`RULES`](demolab-engine/guides/RULES.md) | the contract, toolchain, firewall, how-tos | "what are the conventions", "how do I add a tool / experiment / writing" |
| [`HOUSESTYLE`](demolab-engine/guides/HOUSESTYLE.md) | prose / math / figure style (the H-rules) | "how should I write this", any prose/figure style question |
| [`SLIDES`](demolab-engine/guides/SLIDES.md) | deck conventions + the layout catalog | "make a deck", "which slide layout" |
| [`STRUCTURE`](demolab-engine/guides/STRUCTURE.md) | the annotated file tree | "where does X live", "what's this folder for" |
| [`AUTORESEARCH-RULES`](demolab-engine/guides/AUTORESEARCH-RULES.md) | the semi-autonomous research contract (plan/log/queue/night-shift, git flow) | "how does the queue / night-shift work" |
| [`GLOSSARY`](demolab-engine/guides/GLOSSARY.md) | the vocabulary | an unfamiliar term — tool, experiment, deck, collection, provenance… |
| [`SUPPORT`](demolab-engine/guides/SUPPORT.md) | getting a human (GitHub issues, via `gh`) | "is this a bug", "where do I report this", stuck after repeated failures |
