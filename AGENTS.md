> **demolab lab** — before working here, run `uv run demolab docs` and follow what it
> prints (the agent manual + runbook menu). Do not substitute `uvx`: this lab's project
> environment is the source of truth. A user message that is just a NAME in CAPS (`HELP`,
> `LINT`, `DOCTOR`, …) is a command — the manual explains.

**This checkout is also the demolab-cli source repo** — the engine lives in `demolab_cli/`
(build code, Typst templates, runbooks, guides, scaffold, and the manual `demolab docs`
prints). Editing the engine itself? Read [DEVELOPING.md](DEVELOPING.md) first; the package
is installed editable here, so `uv run demolab` runs the working tree's code.

**Internal demo:** all authored demo configuration, articles, and data live in `.demo/`.
Only generated runtime belongs in `.demolab/`. Run `uv run demolab dev`, `build`, and
`clean` from this checkout; do not recreate root `writings/`, `.artifacts/`, or demo fixtures.
The printed authoring guides describe ordinary user labs, whose layout is unchanged.
