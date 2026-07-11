# CLAUDE.md

Read **[AGENTS.md](AGENTS.md)** before working here — it's the entry point.

## Commands — type a NAME

demolab is driven by names in CAPS. **If the user's message is just one of these names,
that IS the command — do it, don't ask what they mean:**

- **`HELP`** — run `demolab docs` and present the menu of runbooks and guides.
- **A runbook name** (e.g. `GETTING-STARTED`, `TOUR`, `LINT`, `DOCTOR`, `RED-TEAM`,
  `STEELMAN`, `NEXT`, `UPDATE`) — run `demolab docs <NAME>`, read the file it points at,
  then **start that runbook** and drive it step by step.
- **A guide name** (e.g. `RULES`, `HOUSESTYLE`, `SLIDES`, `STRUCTURE`, `GLOSSARY`,
  `SUPPORT`) — read it the same way, then **walk the user through it** interactively.

The full, current menu (names + one-liners) comes from `demolab docs` — run it rather than
relying on a memorised list. Details of the interaction rules are in [AGENTS.md](AGENTS.md).
