# AGENTS.md

Demolab — an agent-operated lab notebook for computational science. This file is the
thin entry point; the substance lives in the engine so it updates cleanly (_"update
demolab"_). **Read the rules before working here.**

**Rules, contract & how-tos** → [`demolab-engine/guides/RULES.md`](demolab-engine/guides/RULES.md) — the single conventions doc: toolchain, the framework/content firewall, commits, the tool ↔ experiment contract + schemas, and how to add a tool / experiment / writing. Unfamiliar with a term (tool, experiment, deck, collection, provenance…)? → [`demolab-engine/guides/GLOSSARY.md`](demolab-engine/guides/GLOSSARY.md). Authoring a writing? → [`demolab-engine/guides/HOUSESTYLE.md`](demolab-engine/guides/HOUSESTYLE.md) for prose/math/figure style (a root `HOUSESTYLE.local.md`, if present, extends or replaces it — read it too). Authoring a slide deck? → [`demolab-engine/guides/SLIDES.md`](demolab-engine/guides/SLIDES.md) for deck conventions, layouts, and sizing. New to the layout? → [`demolab-engine/guides/STRUCTURE.md`](demolab-engine/guides/STRUCTURE.md) for the annotated file tree. Stuck and need a human? → [`demolab-engine/guides/SUPPORT.md`](demolab-engine/guides/SUPPORT.md) (GitHub issues / email).

Two rules important enough to state here too:

- **Toolchain:** use `uv` (Python) and `typst` (publishing) via `task` (go-task). Never call `pip` / `python` / `python3` directly.
- **Commits:** author every commit as the human only — never a `Co-Authored-By:` / agent trailer, never an agent in the author/committer fields.

## Runbooks

Say the trigger phrase — **or just the runbook's name** (`LINT`, `DOCTOR`, `UPDATE`, `MIGRATE-CODE`, …) — and open the matching file in [`demolab-engine/runbooks/`](demolab-engine/runbooks/), then drive it **interactively** (run each step, show the result, confirm before moving on — don't dump the whole runbook at once).

> **`HELP`** — if the user says **HELP** (or "what can you do", "--help", "list the runbooks"), present the runbook table below and the guides linked above, each with its one-line description, and remind them they trigger any of it by name. It's the menu; keep it short.

> **Setting up a fresh lab** ("set up my lab", "how do I get started") means **following [GETTING-STARTED.md](demolab-engine/runbooks/GETTING-STARTED.md) as a conversation** — orient the user, then ask the gated questions *in order* and wait for answers. **Do not autonomously clone, scaffold, install, run the demo, and report back** — that races past every choice the user is supposed to make (fresh-or-migrate, demo-or-clean, stack, branding, publish, what to compute). Read the runbook first; run nothing before its step 0 orient + ready-check.

| Trigger                                 | Runbook                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| _"set up my lab" · "how do I get started"_ | [GETTING-STARTED.md](demolab-engine/runbooks/GETTING-STARTED.md) |
| _"tour" · "walk me through this repo"_  | [TOUR.md](demolab-engine/runbooks/TOUR.md)                       |
| _"migrate my code"_                     | [MIGRATE-CODE.md](demolab-engine/runbooks/MIGRATE-CODE.md)       |
| _"from jupyter" · "convert my notebook"_ | [FROM-JUPYTER.md](demolab-engine/runbooks/FROM-JUPYTER.md)      |
| _"from paper" · "reproduce this paper"_ | [FROM-PAPER.md](demolab-engine/runbooks/FROM-PAPER.md)          |
| _"embed demolab as a docs site"_        | [EMBED-DOCS.md](demolab-engine/runbooks/EMBED-DOCS.md)           |
| _"migrate the stack to MATLAB / Julia"_ | [MIGRATE-STACK.md](demolab-engine/runbooks/MIGRATE-STACK.md)     |
| _"ground my claims"_                    | [GROUND-CLAIMS.md](demolab-engine/runbooks/GROUND-CLAIMS.md)     |
| _"what next" · "what should I run next"_ | [NEXT.md](demolab-engine/runbooks/NEXT.md)                      |
| _"update demolab"_                      | [UPDATE.md](demolab-engine/runbooks/UPDATE.md)                   |
| _"doctor the repo"_                     | [DOCTOR.md](demolab-engine/runbooks/DOCTOR.md)                   |
| _"lint the writings"_                   | [LINT.md](demolab-engine/runbooks/LINT.md)                       |
| _"red-team" · "critique this experiment"_ | [RED-TEAM.md](demolab-engine/runbooks/RED-TEAM.md)             |
| _"steelman" · "make the case for this"_ | [STEELMAN.md](demolab-engine/runbooks/STEELMAN.md)              |
