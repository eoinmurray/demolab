# demolab — the agent manual

You are operating a **demolab lab**: an agent-operated lab notebook for computational
science. The loop: a tool computes → drops data under `artifacts/data/<id>/` → an
experiment writes it up in `writings/<id>.typ` → `demolab build` publishes it all as a
website, per-entry PDFs, and a book. Every number on a page is read from the run that
produced it — nothing is hand-typed, so prose and results can't drift.

This manual ships inside the `demolab-cli` package and is printed by `demolab docs`, so it
is always in step with the installed engine. Read it top to bottom once per session; it's
short.

## The layout, in one breath

`tools/` (reusable science), `experiments/` (runners), `writings/` (the .typ writeups),
`artifacts/` (the committed record: `data/` + `pdfs/`; `site/` is a gitignored build),
`demolab.yaml` (branding — and the lab-root marker every `demolab` command walks up to).
The engine lives in the installed package, not the lab; the gitignored `.demolab/` dir is
machine-managed staging. Full tree: `demolab docs STRUCTURE`.

## Commands — type a NAME

demolab is driven by the user typing a **name in CAPS** (SCREAMING-KEBAB):

- **`HELP`** — present the menu at the bottom of this output, one line each.
- **`<RUNBOOK>`** (e.g. `LINT`, `DOCTOR`, `NEXT`) — run `demolab docs <NAME>`, read the
  file it prints, then **start it** and drive it step by step: run a step, show the
  result, confirm before the next. Never dump the whole runbook at once.
- **`<GUIDE>`** (e.g. `RULES`, `SLIDES`) — read it the same way, then **walk the user
  through it**: summarise, go section by section, answer questions — don't paste the file.

**The NAME is the command.** If the user's message is (or starts with) one of these names,
that *is* the request — act on it, don't ask what they mean. Natural phrasings route too
("lint the writings" → `LINT`, "set up my lab" → `GETTING-STARTED`).

**Docs are the source of truth.** When the user is confused, stuck, or asks "how do I…"
about operating demolab, check the menu before improvising an answer. If a runbook or
guide covers it, ground your answer in it — cite it or offer to start it.

> **`GETTING-STARTED` is a conversation, not a script to race through.** Orient the user,
> then ask its gated questions *in order* and wait for each answer. Do not autonomously
> scaffold, install, build an experiment, and report back — that skips every choice the
> user is supposed to make. Read the runbook first; run nothing before its step-0 orient
> and the user's "ready".

## Non-negotiables

- **Toolchain:** `uv` (Python) and `typst` (publishing) via the `demolab` CLI. Never call
  `pip` / `python` / `python3` directly.
- **Commits:** author every commit as the human only — never a `Co-Authored-By:` / agent
  trailer, never an agent in the author/committer fields.
- **Never hand-edit machine-managed dirs:** `.demolab/` and `temp/` belong to the CLI.
  The engine isn't in the lab tree at all — it's the installed package; updating it is a
  dependency bump (`demolab docs UPDATE`).
- **Never hand-type a result.** Writings read the run (`json("/artifacts/data/<id>/numbers.json")`,
  `numbers-table`, `#image`) — the contract is in `demolab docs RULES` §4–6.
- A root `HOUSESTYLE.local.md`, if present, extends or replaces the default house style —
  read it alongside `demolab docs HOUSESTYLE` before authoring prose.
- The lab's own additional rules live in the root `AGENTS.md` — read that too; where the
  two conflict, the lab's rules win.

## Everyday commands

`demolab` lists them all. The loop: `demolab run expNNN` (run an experiment end-to-end) ·
`demolab dev` (live-preview server — have the *user* run it in their own terminal) ·
`demolab build` (site + PDFs) · `demolab test`. Reference data ships in the package:
`demolab docs STARTERS` (canonical first experiments — model file shapes on them, never copy
blindly; `monte-carlo-pi` is the default) and `demolab docs DEMO` (the published docs site's
source).
