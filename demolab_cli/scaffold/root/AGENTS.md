# AGENTS.md

Demolab — an agent-operated lab notebook for computational science. This file is the thin
entry point; the substance (runbooks + guides) ships inside the `demolab-cli` package and
is reached through the CLI, so it's always in step with the installed engine. **Read the
rules before working here.**

**Finding the docs:** run `demolab docs` for the menu of runbooks (step-by-step procedures)
and guides (reference). `demolab docs <NAME>` prints the file's absolute path — read that
file. Start with `demolab docs RULES` — the single conventions doc: toolchain, what you may
edit, commits, the tool ↔ experiment contract + schemas, and how to add a tool /
experiment / writing. Unfamiliar with a term? `demolab docs GLOSSARY`. Authoring a writing?
`demolab docs HOUSESTYLE` (a root `HOUSESTYLE.local.md`, if present, extends or replaces it
— read it too). A slide deck? `demolab docs SLIDES`. Lost in the layout? `demolab docs
STRUCTURE`. Need a human? `demolab docs SUPPORT`.

Three rules important enough to state here too:

- **Toolchain:** use `uv` (Python) and `typst` (publishing) via the `demolab` CLI. Never
  call `pip` / `python` / `python3` directly.
- **Commits:** author every commit as the human only — never a `Co-Authored-By:` / agent
  trailer, never an agent in the author/committer fields.
- **Don't edit the engine:** there is no engine directory to edit — it lives in the
  installed package. The gitignored `.demolab/` dir at the root is machine-managed staging;
  never hand-edit it. Updating the engine is a dependency bump (see `demolab docs UPDATE`).

## Commands — type a NAME

demolab is driven by typing a **name in CAPS** (SCREAMING-KEBAB). Three commands:

- **`HELP`** — run `demolab docs` and present its menu, one line each.
- **`<RUNBOOK>`** — a runbook name (e.g. `GETTING-STARTED`, `LINT`, `DOCTOR`) → run
  `demolab docs <NAME>`, read the file, then **start it** and drive it step by step: run a
  step, show the result, confirm before the next. Never dump the whole runbook at once.
- **`<GUIDE>`** — a guide name (e.g. `RULES`, `SLIDES`) → read it the same way, then **walk
  the user through it**: summarise, go section by section, answer questions — don't just
  paste the file.

**The NAME is the command.** If the user's message is (or starts with) one of these names,
that *is* the request: act on it, don't ask what they mean. Natural phrasings route too
("lint the writings" → `LINT`, "set up my lab" → `GETTING-STARTED`) — the `demolab docs`
menu's one-liners tell you which doc covers what.

**Docs are the source of truth.** When the user is confused, stuck, or asks "how do I…"
about operating demolab, check the menu *before* improvising an answer. If a runbook or
guide covers it, ground your answer in it — cite it, or offer to start it — rather than
explaining from memory.

> **`GETTING-STARTED`** ("set up my lab", "how do I get started") means **following the
> runbook as a conversation** — orient the user, then ask the gated questions *in order*
> and wait for answers. **Do not autonomously scaffold, install, build an experiment, and
> report back** — that races past every choice the user is supposed to make (what to
> compute, branding, publishing). Read the runbook first; run nothing before its step-0
> orient + ready-check.
