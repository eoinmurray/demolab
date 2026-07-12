# Runbook: Work the night

> The autonomous shift: on a night branch, work tonight's pre-registered mandate — pop each
> `queued` experiment, implement and run it within its budget, check the result against its kill
> criterion and baseline, draft the writeup, record what happened as you go, and commit — one
> commit per experiment. End by writing the digest and opening a PR for the morning gate. This is
> the only runbook that runs unattended, and it runs for **at most one night**. It works the
> mandate **PLAN** committed and obeys its operating contract; conventions in
> [`../guides/AUTORESEARCH-RULES.md`](../guides/AUTORESEARCH-RULES.md).

## When to use

Unattended execution of an already-planned night — typically kicked off at end of day (by hand or
a scheduler). It never invents science: it works the mandate PLAN pre-registered, and may
*propose* more in the digest but never runs its own proposals. If tonight has no mandate with
`queued` entries, there is nothing to do — that's PLAN's job.

## What it does

0. **Load the lab's rules first.** Read the lab-root `AGENTS.md` and `HOUSESTYLE.local.md` (if
   present) and obey them for the whole shift — **lab rules win over engine defaults**
   (AUTORESEARCH-RULES §4). This includes any ban on AI-attribution trailers in commits or PR
   descriptions. Do this before touching anything.

1. **Resume check.** Is there an unmerged `night/*` branch for this program from a prior, crashed
   shift? If so, **stop and surface it** — resume it or abandon it is a human's call, not the
   night's. Never start a fresh branch over an orphan.

2. **Open the branch.** Create `night/YYYY-MM-DD-<collection>` off `main`. Open tonight's
   night-shift document and read its **Mandate**: the queue slice, and the operating contract
   (wall-clock-per-run, wall-clock-per-night, default seeds, scope, stop conditions).

3. **Work the queue.** For each `status: queued`, `origin: human` entry, in order, until a stop
   condition (queue empty / night budget spent / build red twice):
   - **Implement** — add/adjust the tool subcommand and write `experiments/expNNN.py` (RULES §7),
     modelled on an existing runner. Run the seed sweep from the entry.
   - **Enforce the budget** — abort the run at its wall-clock ceiling; a diverging training run
     does not get to eat the night. Record the abort, move on.
   - **Check against the pre-registration** — did it clear its `baseline`? Did its `kill`
     criterion fire? Set the entry's status from the run output: `done` or `killed`. Never edit
     the mandate's hypothesis or kill criterion — those are read-only on a night branch
     (AUTORESEARCH-RULES §5).
   - **Write it up** — `writings/expNNN.typ`, numbers pulled from the record, not typed.
   - **Record it (science only)** — append to the document's **Record** section: what ran, seeds,
     outcome, any abort, and any anomaly — the *scientific* narrative. Keep engineering detail out
     of it (that's the code log, below). Write it to housestyle *as you go* and lint it throughout
     the shift (a subagent pass is fine) — the record is a published artifact, not scratch, and
     must cold-read (AUTORESEARCH-RULES §3).
   - **Commit (the code log)** — one commit per experiment attempt, killed ones included. The
     commit message carries the *code* log — what the runner/tool changed and why, debugging, a
     build fix — kept out of the scientific Record (AUTORESEARCH-RULES §2). Merge-workflow only;
     no rebase/squash. No AI-attribution trailer on the commit.

4. **Anomaly policy: record and move on.** If a run looks odd, do **not** chase it at 3 a.m. —
   that's how a night burns on a seed artifact. Record it as an anomaly for the morning and
   continue the queue. Chasing is a human decision made in PLAN.

5. **Propose, don't run.** If the night's results suggest a worthwhile next experiment, add it to
   the digest as an `origin: proposed` next step — a **draft** for the human to pick up in PLAN.
   Never run a proposal, and never run anything the mandate didn't pre-register. (Only if the
   contract's `scope.may_propose` is true.)

6. **Write the digest.** At the top of tonight's document, write a ruthless triage summary: how
   many confirmed, how many killed by their own criteria, which anomaly (if any) deserves
   attention, what's proposed. Not a recitation of everything done — the thing a human reads in
   thirty seconds over coffee. It obeys housestyle and must cold-read (AUTORESEARCH-RULES §3).

7. **Open the PR.** Push the branch, open a PR whose **description is the digest** (the science) —
   with **no AI-attribution trailer** (§0; AUTORESEARCH-RULES §5). Any engineering context the
   reviewer should weigh — a workaround, a flaky build, a decision made mid-run — goes as a **PR
   comment** (the code log), not in the digest. Stop. The night is over; the morning gate (PLAN /
   the human review) decides what merges. Publish nothing — CI deploys from `main`, and only a
   human merge reaches `main`.

---

## Agent contract
- **Triggers** — `NIGHT-SHIFT`, "work the night", "run tonight's experiments", "start the night shift".
- **Gates** — **hard rules, non-negotiable:** load lab rules first (§0); resume-check before
  starting (§1); obey the contract's budgets and stop conditions; **never invent-and-run** an
  experiment the mandate didn't pre-register; never edit the mandate's hypothesis/kill criteria;
  merge-workflow commits only; no AI-attribution trailer in commits or the PR description; push to
  a `night/*` branch and open a PR — **never touch `main`**.
- **Report & apply** — the deliverable is the branch + the PR + the digest. Land the finished
  work, record the aborts and anomalies honestly (a killed experiment is a result, report it as
  one), keep the document cold-readable throughout, and hand the whole night to the morning review
  in a single PR.
