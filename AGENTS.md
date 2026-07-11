> **demolab lab** — before working here, run `demolab docs` and follow what it prints
> (the agent manual + runbook menu; no venv yet? `uvx demolab-cli docs`). A user message
> that is just a NAME in CAPS (`HELP`, `LINT`, `DOCTOR`, …) is a command — the manual explains.

**This checkout is also the demolab-cli source repo** — the engine lives in `demolab_cli/`
(build code, Typst templates, runbooks, guides, scaffold, and the manual `demolab docs`
prints). Editing the engine itself? Read [DEVELOPING.md](DEVELOPING.md) first; the package
is installed editable here, so `demolab` runs the working tree's code.
