# AGENTS.md

This is a **demolab** lab (an agent-operated lab notebook). **Before doing anything else,
run `demolab docs` and follow what it prints** — the full agent manual plus the menu of
runbooks and guides, always in step with the installed engine. (No venv yet? `uv sync`
provides the `demolab` command, or run `uvx demolab-cli docs`.)

If the user's message is a NAME in CAPS (`HELP`, `LINT`, `DOCTOR`, …), that **is** the
command — the manual explains. Two rules worth stating even before you've read it: commits
are authored as the human only (never an agent trailer or co-author), and results are never
hand-typed (writings read their run's data).

## This lab's own rules

- **This checkout is also the demolab-cli source repo** — the engine lives in
  `demolab_cli/` (build code, Typst templates, runbooks, guides, scaffold, and the manual
  `demolab docs` prints). Editing the engine itself? Read [DEVELOPING.md](DEVELOPING.md)
  first; the package is installed editable here, so `demolab` runs the working tree's code.
