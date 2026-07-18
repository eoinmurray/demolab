> **demolab lab** — before working here, run `uv run demolab docs` and follow what it
> prints (the agent manual + runbook menu). In an ordinary lab where `demolab` is already
> active, `demolab docs` is equivalent. Use `uvx demolab-cli docs` only when bootstrapping
> a new lab with no project environment. A user message that is just a NAME in CAPS
> (`HELP`, `LINT`, `DOCTOR`, …) is a command — the manual explains.

**This checkout is also the demolab-cli source repo** — the engine lives in `demolab_cli/`
(build code, Typst templates, runbooks, guides, scaffold, and the manual `demolab docs`
prints). Editing the engine itself? Read [DEVELOPING.md](DEVELOPING.md) first; the package
is installed editable here, so `uv run demolab` runs the working tree's code.
