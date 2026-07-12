# Runbook: Start or steer a research program

> Stand up a **research program** as a demolab collection — define the falsifiable arc with the
> scientist, register the collection, and write the first night's mandate; over the program's
> life, capture pivots and the closing retrospective. This is the **program-level** session, run
> a handful of times per program; nightly queue-filling is **PLAN**, and the overnight execution
> is **NIGHT-SHIFT**. Conventions live in
> [`../guides/AUTORESEARCH-RULES.md`](../guides/AUTORESEARCH-RULES.md); this runbook is the procedure.

## When to use

At the birth of a research program, and at its big hinge points — a major pivot, or the close.
It is interactive and human-led: the agent interviews the scientist and writes down what they
decide. It runs no compute. Everything it produces lands on `main` in a daytime session, because
the falsifiable question and kill criteria are human-reviewed by construction (AUTORESEARCH-RULES §5).

## What it does

0. **Load the lab's rules first.** Read the lab-root `AGENTS.md` and `HOUSESTYLE.local.md` (if
   present) and obey them — **lab rules win over engine defaults** (AUTORESEARCH-RULES §4). Do
   this before writing anything.

1. **New program or existing one?** Look for a collection whose entries are night-shift documents.
   - **Exists** → this is a steer: go to step 5 (pivot) or step 6 (close).
   - **None** → this is a birth: steps 2–4.

2. **Define the falsifiable arc (interview the scientist).** Draw out, and write down in the
   scientist's words:
   - The **question**, stated so a result could prove it wrong.
   - Why it matters — what it confirms or rules out in the field.
   - The **baseline** the stack must reproduce before any novel claim is trusted (a published
     number, e.g. a LIF net's accuracy on N-MNIST/SHD). This becomes the first queue entry.
   - The rough arc: the two or three questions after the baseline. Not a full programme — enough
     to aim the first nights. The program is worked tactically, night by night (AUTORESEARCH-RULES §1).
   Don't invent the science. If the scientist is vague, ask; a program with no falsifiable
   question is the thing this runbook exists to refuse.

3. **Pick the collection and register it.** Choose a slug (`neuron-models`, `stdp-window`, …),
   add it to `demolab.yaml` (`collections:` + `collection-order:`, RULES §6.5) with a label and
   one-line description.

4. **Write the first night's mandate.** Scaffold the first night-shift document,
   `writings/arNNN.typ` ("Night shift — YYYY-MM-DD") with `collection: <slug>` and an `order:` (a
   low number; nights list chronologically). In its **Mandate** section, state the program's
   question and baseline, and seed the queue with the baseline-reproduction entry (schema in
   AUTORESEARCH-RULES §2), plus the operating contract (budgets, `scope.collection`, stop
   conditions). Leave the record and digest empty — the night fills them. Build to confirm it
   renders (`demolab build` / the running `demolab dev`), then commit on `main` ("Open program
   <slug>"). That commit is the pre-registration anchor. Hand off to **PLAN** to flesh out the
   queue, or straight to **NIGHT-SHIFT** if the baseline entry is enough for night one.

5. **Pivot (existing program).** A pivot is not an in-place edit of a past mandate — those are
   frozen (AUTORESEARCH-RULES §1). Capture the new direction in the **next** night's mandate: a
   dated statement at its top of what changed and why, then the queue entries the pivot implies.
   Committed on `main` before that night runs, it is provably prior. Hand to **PLAN** to fill the
   rest of the queue.

6. **Close (retrospective).** When the arc is done, write a closing **Retrospective** in the
   final night's digest (or a short closing document): what held, what died, what the nights'
   records say in hindsight, and the honest limitations. The collection now reads, oldest to
   newest, as question → journey → verdict.

---

## Agent contract
- **Triggers** — `AUTORESEARCH`, "start a research program", "set up an autoresearch program",
  "steer/pivot the program", "close out the program".
- **Gates** — load lab rules first (§0); runs on `main`, daytime, no compute. Refuse to open a
  program with no falsifiable question or no baseline. Fill the full nightly queue in **PLAN**,
  not here.
- **Report & apply** — interview interactively; register the collection; write the first night's
  mandate; build to confirm; commit on `main`. Then point the scientist at **PLAN** to plan the
  first night.
