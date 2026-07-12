# Runbook: Doctor the repo (conformance check)

> Verify the repo obeys demolab's conventions and report every violation with the rule it
> breaks and a `file:line` — a **health check, not an auto-fixer**. Pairs with **TOUR**
> (DOCTOR audits the repo against the rules; TOUR orients a human in it).

## When to use
When you want to know whether the repo still obeys demolab's conventions — before publishing,
after a big change, or whenever you suspect drift. [`../guides/RULES.md`](../guides/RULES.md)
is the source of truth for every rule; this runbook is the *inspection* that the repo obeys
it — it cites each rule, it doesn't restate it. (There is no `demolab doctor` command — this
runbook is the doctor, and folds the toolchain check in as step 0.) It reports; it fixes only what you approve, then
re-runs.

## What it does

0. **Toolchain present.** `command -v uv typst task` — all three must resolve. If any is
   missing, give the install (macOS: `brew install uv typst`; `uv` also via
   `curl -LsSf https://astral.sh/uv/install.sh | sh`).

1. **Build + tests are green (the coarse signal).**
   - `demolab build` — compiles all three targets with no error.
   - `demolab test` — `uv run pytest` passes.
   A red build or test is the first thing to fix; everything below is finer-grained.

2. **Mechanical checks (run these — each hit is a violation).**

   ```sh
   # RULES §8.4 — every tool ships a test. A "tool" is a dir with a tool.py
   # (skips __pycache__ and other non-tool dirs).
   for d in tools/*/; do t=$(basename "$d"); [ -f "$d/tool.py" ] || continue; \
     [ -f "$d/test_$t.py" ] || echo "MISSING TEST: $d (needs test_$t.py)"; done

   # RULES §4.5 — import boundary.
   grep -rnE '^\s*(from|import) experiments' tools/ && echo "VIOLATION: a tool imports experiments/"
   grep -rnE '^\s*(from|import) tools'       experiments/ && echo "VIOLATION: a runner imports a tool (use its CLI)"

   # RULES §6.1 — every non-slide writing is well-formed (#let meta + #let body).
   for f in writings/*.typ; do case "$f" in *.slide.typ) continue;; esac; \
     { grep -qE '^#let meta' "$f" && grep -qE '^#let body' "$f"; } || echo "MALFORMED WRITING: $f"; done

   # RULES §7 — every experiment has its committed record + writeup (id threads through).
   for f in experiments/exp*.py; do id=$(basename "$f" .py); \
     [ -f "artifacts/data/$id/numbers.json" ] || echo "MISSING RECORD: artifacts/data/$id/numbers.json"; \
     [ -f "writings/$id.typ" ] || echo "MISSING WRITEUP: writings/$id.typ"; done

   # RULES §4.7 — provenance stamped into every committed record.
   grep -rL '_provenance' artifacts/data/*/numbers.json 2>/dev/null | sed 's/^/MISSING PROVENANCE: /'

   # RULES §4.7 — every experiment record carries a run.sh reproducer.
   for f in experiments/exp*.py; do id=$(basename "$f" .py); \
     [ -f "artifacts/data/$id/run.sh" ] || echo "MISSING REPRODUCER: artifacts/data/$id/run.sh"; done

   # RULES §2.1 — no agent authorship anywhere in history.
   git log --format='%an|%cn|%b' | grep -iE 'co-authored-by:.*(claude|anthropic|\[bot\])|generated with|claude' \
     && echo "VIOLATION: agent authorship in git history"

   # RULES §5.1 / §5.3 — scratch is gitignored, never tracked.
   git ls-files temp artifacts/site | head -1 | grep -q . && echo "VIOLATION: temp/ or artifacts/site/ is tracked"

   # RULES §3.3 — branding belongs in demolab.yaml, not hacked into the black box.
   # (Informational — compare against upstream during "update demolab".)

   # AUTORESEARCH-RULES §1 — the per-night model has no standing `plan`/`log`; a leftover one is
   # the old three-document shape and should migrate to per-night documents.
   for a in plan log; do [ -f "writings/$a.typ" ] && \
     echo "AUTORESEARCH: standing '$a' article — migrate to per-night night-shift documents (AUTORESEARCH-RULES §1)"; done

   # AUTORESEARCH-RULES §5 — the autoresearch PR description (the digest) carries no
   # AI-attribution trailer. Fires only where gh is available and the repo has PRs.
   command -v gh >/dev/null 2>&1 && gh pr list --state all --limit 50 --json body --jq '.[].body' 2>/dev/null \
     | grep -iE 'co-authored-by:.*(claude|anthropic|\[bot\])|generated with claude' \
     && echo "VIOLATION: AI-attribution trailer in a PR description (AUTORESEARCH-RULES §5)"
   ```

3. **Judgment checks (no grep suffices — the agent decides).**
   - **§4.2 — tools emit data, not plots.** Scan each `tools/*/tool.py` for figure-drawing
     (`savefig`, `plt.`, writing a `.png`); the exception is a *rendering* tool writing an
     `.mp4` (declared `headline_video`).
   - **§4.1 — no forced one-off tools.** Flag any `tools/<t>` used by exactly one experiment
     and unlikely to be reused — it may belong inline; don't force a change.
   - **§6.2 — numbers don't drift.** Spot-check that each `writings/*.typ` pulls figures/tables
     from `json(...)` / `#image(...)` / `#numbers-table(...)`, not hand-typed literals.
   - **§7.5 — staged runs plot from the record.** *Only for a runner that offers a plot-only /
     skip-compute mode* — a one-shot `main()` is out of scope. Check the flow holds: the plot
     stage reads its inputs from `artifacts/data/<id>/`, never `temp/`. A grep can't prove this
     — verify it **behaviourally**: confirm `artifacts/data/<id>/` is committed and complete,
     then re-run the runner's plot-only mode with scratch hidden (move `temp/` aside, or point
     the runner's scratch root at an empty dir — however *that* runner locates it) and confirm
     it exits 0 and reproduces the figures. A plot-only pass that fails only once `temp/` is
     hidden is reaching into scratch. Don't prescribe the fix — the rule defines the flow, not
     the mechanism; report the boundary breach and let the author choose how to close it.
     Advisory unless the experiment claims clone-and-replot, since plotting from warm `temp/`
     while iterating is fine (§5.1).
   - **§3 — docs match reality.** Runbook counts, path references, and the firewall in
     [`../guides/RULES.md`](../guides/RULES.md) still describe the actual tree.
   - **AUTORESEARCH-RULES §2 — every `queued` entry has a kill criterion.** In an autoresearch
     program, read each night document's mandate queue: any entry with `status: queued` and no
     `kill` field is a violation (PLAN should have refused it). Also confirm `status` values are
     read from run outputs, not hand-typed to `done` (spot-check against `artifacts/data/<id>/`).
   - **AUTORESEARCH-RULES §2 — each night document carries a mandate, record, and digest.** Spot-
     check a program's night-shift documents have the three sections, and that a closed night's
     mandate was not edited after its runs (git blame the mandate against the run commits).

4. **Report.** Present one grouped report:
   - **Broken** (build/test red, agent authorship, import-boundary breach) — fix now.
   - **Conformance** (missing tests, malformed writings, missing records/provenance, tracked
     scratch) — fix before publishing.
   - **Advisory** (judgment flags: plots-in-tools, forced one-offs, possible drift, stale docs,
     staged-run plot boundary) — the user's call.

   For each finding: cite the rule by its `§N.M` in
   [`../guides/RULES.md`](../guides/RULES.md), the `file:line`, and the fix. Apply only what the
   user approves, then re-run the relevant checks to confirm green.

---

## Agent contract
- **Triggers** — `DOCTOR`, "doctor the repo", "check the repo follows the conventions", "audit
  demolab conformance", "does this repo still obey the rules".
- **Gates** — §0 (toolchain resolves) must hold before the checks mean anything.
- **Report & apply** — drive it interactively: run each check, collect the hits, present **one**
  report grouped by severity, then offer to fix. Apply only what the user approves, then re-run
  the relevant checks to confirm green.
