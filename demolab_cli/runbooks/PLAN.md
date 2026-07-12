# Runbook: Plan the next night (and triage the last one)

> The daily driver: read last night's digest and open PR, decide what to promote or kill, then
> interview the scientist into the next night's **pre-registered** mandate — a new night-shift
> document whose queue entries each carry a kill criterion, a baseline, and a seed and time
> budget. Smaller and more frequent than **AUTORESEARCH** (which births the program); it feeds
> **NIGHT-SHIFT** (which works the night). Conventions:
> [`../guides/AUTORESEARCH-RULES.md`](../guides/AUTORESEARCH-RULES.md).

## When to use

Most mornings of an active program, and any time you want to set up the next night. Morning
triage is the first half of this runbook, not a separate ritual: you open the night's PR, decide,
then plan the next night from what you learned. Runs on `main`, no compute.

## What it does

0. **Load the lab's rules first.** Read the lab-root `AGENTS.md` and `HOUSESTYLE.local.md` (if
   present) and obey them — **lab rules win over engine defaults** (AUTORESEARCH-RULES §4).

1. **Read the night.** Find the open `night/*` PR for this program and read its description (the
   digest) and the record of last night's document. If there's no PR, skip to step 4.

2. **Triage the results.** For each experiment the night produced, check it against its
   pre-registered entry:
   - **Confirmed** — met its baseline, survived its kill criterion across the seed sweep → keep.
   - **Killed by its own criterion** — the mandate said this would falsify it; record it as a
     negative result, don't rescue it.
   - **Anomaly parked for you** — the night logged something odd and moved on (by design). Decide:
     ignore, or queue a follow-up to chase it.
   Then act on the PR: **merge** (accept the night), **request changes** ("rerun exp014 with more
   seeds"), or **close** (reject). The PR *is* the gate — nothing here republishes without it.

3. **Review the night's proposals.** Last night's digest may list `origin: proposed` next steps —
   experiments it thinks are worth running. They were **never run** (that's the rule). Carry the
   good ones into tonight's queue as `origin: human` `queued`; drop the rest. This is where you
   stop the agent from steering itself into cheap parameter-sweep local minima.

4. **Plan the next night (interview the scientist).** For each new experiment, pin down:
   - **Hypothesis** — stated so it can be wrong.
   - **Kill criterion** — the result that falsifies it or aborts the run. **Required.**
   - **Baseline** — the number/earlier `expNNN` it must reproduce or beat.
   - **Seeds** — the sweep size (default from the contract); one seed is an anecdote.
   - **Budget** — the per-run wall-clock ceiling.
   Keep each experiment small — one variable moved (the demolab loop). Lean on **NEXT** for
   candidate directions from the decision arc; this runbook turns a chosen direction into a
   committed, falsifiable entry.

5. **Refuse the unfalsifiable.** Do not write a queue entry that has no kill criterion. This one
   rule does more for rigor than any amount of after-the-fact red-teaming — enforce it even when
   the scientist is impatient.

6. **Write tonight's mandate and commit.** Scaffold the next night-shift document,
   `writings/arNNN.typ` ("Night shift — YYYY-MM-DD") with `collection: <slug>` and the next
   `order:`. Fill its **Mandate** section: the queue entries (`status: queued`, `origin: human`)
   and the operating contract (AUTORESEARCH-RULES §2); leave record and digest empty. Build to
   confirm the generated status table renders, commit on `main` ("Mandate <date> <slug>:
   exp0NN–exp0NN"). That commit is the night's pre-registration anchor and its worklist.

---

## Agent contract
- **Triggers** — `PLAN`, "plan the next night", "triage last night", "set up tonight",
  "what do we run tonight".
- **Gates** — load lab rules first (§0); runs on `main`, daytime, no compute. **Every queued
  entry must carry a kill criterion** (step 5). Never run experiments here; never carry a
  `proposed` entry forward without the scientist's say-so.
- **Report & apply** — triage the PR interactively, review proposals, interview into new entries,
  refuse the unfalsifiable, write and commit tonight's mandate on `main`. Then it's the night's to
  work.
