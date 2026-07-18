# Runbook: Run an autoresearch program

> The single front door for a semi-autonomous research program. Inspect the program's actual
> state, then do the next safe thing: formulate it, review the previous night, pre-register the next
> mandate, work the locked queue, resume an interrupted shift, present the morning PR, pivot, or
> close. The user never has to choose a phase-specific command. The scientific contract lives in
> [`../guides/AUTORESEARCH-RULES.md`](../guides/AUTORESEARCH-RULES.md).

## When to use

Use `AUTORESEARCH` for every interaction with an autoresearch program: shaping a rough idea,
starting one, asking for status, planning or starting a night, reviewing results, requesting a
rerun, changing direction, or closing the program. Natural phrasings route here too ("refine this
research idea", "plan tonight", "work the night", "review last night", "resume the program").

`AUTORESEARCH` is state-aware and idempotent. Re-running it discovers the existing collection,
mandate, branch, and PR before acting. It never allocates a second night, duplicates a run, opens
a second PR, or publishes merely because the command was invoked twice.

## The three human gates

The command may automate everything between these gates, but never crosses one silently:

1. **Program gate** — after reviewing the state of play and alternative formulations, the
   scientist approves a Programme Brief: falsifiable question, operational definitions, baseline,
   outcomes, confounds, feasibility limits, and program stop condition.
2. **Mandate gate** — the scientist approves and locks the hypotheses, kill criteria, seed and
   resource budgets, scope, and stop conditions before compute begins.
3. **Publication gate** — the scientist reviews the evidence packet and chooses merge, request
   changes, or close. The agent never merges its own night.

## Procedure

### 0. Load local rules

Read the lab-root `AGENTS.md` and `HOUSESTYLE.local.md` (if present) before doing anything. Lab
rules win over engine defaults. This includes commit authorship and PR-description rules.

### 1. Resolve the current state

Inspect all autoresearch collections, their newest night documents, `night/*` branches, and open
or recently closed PRs. If several programs exist, show each with one derived state and ask which
to continue:

- **formulating** — no approved Programme Brief, or the scientist wants to refine the question;
- **draft** — the next mandate is being prepared but is not locked on `main`;
- **locked** — a mandate is committed on `main`, with queued work and no night branch;
- **running** — its night branch exists and has unfinished queued work;
- **review** — its branch has finished and its PR is open;
- **changes requested** — the open PR has a human-approved rerun or correction;
- **accepted** — the last PR merged; the program needs another night, a pivot, or closure;
- **rejected** — the last PR closed unmerged; the scientist must decide what replaces it;
- **closed** — the collection has a retrospective and no further work is planned.

Derive state from committed documents, Git, run artifacts, and PR state; do not trust a manually
typed state flag. Report the state and perform only its matching phase below.

### 2. Formulating — turn the idea into a researchable question

Do not begin by asking the scientist to supply a perfectly formed hypothesis. Their opening may
be a curiosity, problem, mechanism, desired improvement, or vague claim. Preserve it verbatim as
the **original idea**, then help refine it.

#### 2.1 Orient from the state of play

Before proposing a question, inspect the relevant lab evidence:

- existing experiment writeups, `numbers.json`, runners, baselines, and available datasets/tools;
- autoresearch Records and Digests, including killed hypotheses and parked anomalies;
- resource constraints and whether an evaluator can run unattended;
- references or external evidence the scientist supplied or explicitly asks to investigate.

Present a short **State of play** separating what is established, assumed, unknown, unavailable,
and technically feasible. Do not pretend the lab answers a field-wide question when it contains
one convenient benchmark.

#### 2.2 Test suitability

Assess whether the idea is appropriate for autoresearch:

- Is there a falsifiable question and an automatically measurable outcome?
- Is there a credible baseline that the stack can reproduce first?
- Are the intervention, comparison, unit of analysis, and important fixed conditions identifiable?
- Can repeated seeds or independent replicates express uncertainty meaningfully?
- Can a run finish inside bounded wall-clock, compute, evaluation, and monetary budgets?
- Can the evidence distinguish the claim from obvious confounds?
- Does it avoid unavailable physical experiments, human-subject approval, or irreducibly subjective
  judgment?

Give one explicit verdict:

- **SUITABLE** — ready to formulate as a program;
- **NEEDS REFINEMENT** — promising, but an outcome, baseline, contrast, or scope is still vague;
- **BLOCKED** — required evidence or infrastructure is unavailable;
- **WRONG WORKFLOW** — this is better handled as a one-off experiment, `FROM-PAPER`,
  `LITERATURE-SEARCH`, or another named workflow.

Do not force every interesting thought into AUTORESEARCH merely because it owns a capitalized
command.

#### 2.3 Offer formulations

When more than one honest scope is available, show at most three alternatives:

1. **Conservative** — the cleanest falsification using the strongest available baseline;
2. **Balanced** — the most useful claim supportable within present resources;
3. **Ambitious** — the broader claim, with its extra assumptions, cost, and failure risk exposed.

For each, state the question, outcome, baseline, falsifier, first-night objective, and what the
formulation cannot establish. Recommend one, but let the scientist select, combine, or rewrite
them.

#### 2.4 Produce the Programme Brief

Reflect the chosen formulation back as a compact review object:

- original idea and current state of evidence;
- falsifiable program question and why it matters;
- operational definitions, intervention, comparison, and unit of analysis;
- primary outcome plus any diagnostic secondary outcomes;
- baseline the first night must reproduce;
- falsifier and program-level stop condition;
- known confounds, limitations, and unavailable evidence;
- available data, evaluator, and resource envelope;
- first-night objective and the next two or three likely questions.

**Nothing is committed during formulation.** Present the whole Programme Brief and ask the
**program gate** question. If the scientist rejects or edits it, remain in formulation. If the
idea is blocked or belongs to another workflow, stop or route it rather than registering a hollow
program.

Only after explicit approval, register one collection in `demolab.yaml` with a slug, label,
description, and `collection-order` entry. Copy the approved Programme Brief into the first
night's Mandate so the collection itself remains the program record; do not create a standing
plan document. Continue to **draft** and make baseline reproduction the first queue entry.

### 3. Draft — review the last night and prepare the next mandate

If a previous night exists, read its Digest, Record, experiment writeups, `numbers.json` files,
and PR outcome first. For every result, compare it with the criterion committed before the run:

- **confirmed** — reproduced or beat its baseline and survived its kill criterion across seeds;
- **killed** — fired its own kill criterion; preserve it as a negative result and do not rescue it;
- **anomaly** — parked by the shift; ask the scientist whether to ignore it or investigate later.

Review proposed follow-ups. They have not run. The scientist may promote a proposal to a new
`origin: human` queue entry, edit it, or discard it.

For every entry in the next queue, pin down:

- a falsifiable hypothesis;
- a required kill criterion;
- a baseline;
- seed count (one seed is an anecdote);
- per-run wall-clock and resource ceiling.

Keep experiments small: one question or controlled change per entry. Allocate the next unused
`arNNN` for the night document and unused `expNNN` ids for its queue. Treat ids already present in
files **or committed mandates** as occupied; reserve the article and experiment ids together in
the mandate. Never recycle an abandoned id.

Reserve two article ids together and create both documents:

- `writings/arNNN.typ` ("Night shift — YYYY-MM-DD") with the collection and chronological
  `order:`. Its rendered order is Digest -> Mandate -> Record; leave Digest and Record empty.
- `writings/arMMM.typ` ("Activity trace — YYYY-MM-DD") as that night's live, shareable decision
  and activity trace. Link its id from the night document's metadata and reserve it in the same
  mandate commit so another program cannot claim it.

The activity trace is not hidden chain-of-thought. It preserves the complete user-visible
conversation and a structured audit trail of decisions, evidence, actions, tool outcomes,
failures, costs, commits, and pending work. Give each visible message its timestamp, role,
session/task id, and checkpoint id. Before anything enters the published trace, redact secrets,
credentials, private infrastructure identifiers and paths; fail closed when sanitization is
uncertain. Retain an immutable private raw transcript outside the repository and record a hash
prefix in each public checkpoint.

Build both documents, present the complete queue and operating contract, and ask the **mandate
gate** question.

On approval, commit the mandate to `main` before any run. That commit is the pre-registration and
id-reservation anchor. If `main` advanced before the push, refresh it, re-check id reservations,
and retry without force-pushing. Do not compute until this commit succeeds.

### 4. Locked — start the shift

Offer to run now or at the time requested by the scientist. Before starting, repeat the maximum
night duration, run/evaluation count, compute allowance, and monetary ceiling.

Check for an older unmerged `night/*` branch for this program. If one exists, stop and present
**resume** or **abandon**; never create a fresh branch over it. Otherwise create
`night/<collection>/<arNNN>` from the exact locked-mandate commit and continue to **running**. The
immutable night id, rather than its scheduled date, makes the branch unique if a shift is delayed
or restarted.

### 5. Running — work only the locked queue

For each `status: queued`, `origin: human` entry, in order, until the queue is empty or a stop
condition fires:

1. Implement or reuse the tool command and create `experiments/expNNN.py`.
2. Run the registered seed sweep within its resource and wall-clock budget.
3. Read the result against the locked baseline and kill criterion; derive `done` or `killed` from
   run output. Never edit the hypothesis, baseline, or kill criterion.
4. Create `writings/expNNN.typ`, reading every result from committed artifacts.
5. Add the scientific outcome, seeds, aborts, and anomalies to the night Record. Put engineering
   detail in the commit message or a PR comment, not the scientific Record.
6. Lint as the Record grows and commit once per experiment attempt, killed attempts included.

Maintain the activity trace throughout the shift, not retrospectively at the end. Append every
user-visible user and assistant message verbatim and chronologically; never substitute a summary
for visible text. Exclude hidden chain-of-thought and internal reasoning. At each meaningful
scientific milestone, append a timestamped decision entry stating the evidence considered, action
taken, justification exposed to the collaborator, result, budget effect, and pending work. Build,
validate, commit, and push a hash-linked checkpoint after scientific decisions, failures, protocol
anomalies, compute dispatch or reaping, and completed experiments so the PR preview remains useful
during the session. Logging must never delay a safety-critical action such as stopping or reaping
compute. A read-only companion may validate or maintain the trace, but the running agent remains
responsible for its completeness.

Do not chase an anomaly mid-shift. Record it and continue. The agent may add a proposed follow-up
to the Digest when `scope.may_propose` permits, but never runs it.

If invoked while work is already running, report completed/remaining experiments and budget used;
do not start duplicate processes. If interrupted, resume the existing branch and completed run
artifacts rather than allocating another night.

At shift end, write a ruthless Digest: confirmed and killed counts, aborts, the anomaly deserving
attention, budget use, and proposed follow-ups. Finalize the activity trace with its last
checkpoint and private-source hash. Build and test the complete record. Push the branch and open
one PR whose description is the Digest; engineering caveats go in PR comments. Stop at the
**publication gate**.

### 6. Review — walk the scientist through the evidence

Lead with the Digest and rendered preview, then compare every result with its locked mandate.
Surface protocol deviations, dirty provenance, missing seeds, resource overruns, and anomalies
before recommendations. Let the scientist inspect writeups, figures, `numbers.json`, attempts,
commits, and code as deeply as they want.

Ask for one decision:

- **merge** — accept the night using a merge commit; never squash or rebase, because run stamps
  point at the night commits;
- **request changes** — record the exact approved rerun/correction and continue on the same branch;
- **close** — reject the night while preserving its PR as the audit trail.

Never merge on the scientist's behalf without this explicit decision. After merge or close,
offer to prepare the next mandate, pivot, or close the program; those choices return to **draft**.

### 7. Changes requested — correct without rewriting history

Resume the same branch. A rerun that keeps the question, metric, dataset, baseline, and kill
criterion is another attempt at the same experiment and receives another commit. If any of those
scientific terms change, do not mutate the locked mandate: create a new night and experiment id
through **draft**. Update the PR and return to **review**.

### 8. Pivot or close

A material pivot returns to **formulating**: refresh the State of play, reformulate the question,
and obtain a new program-gate approval. Never edit an earlier mandate. Put the approved change and
its reason at the top of the next dated mandate, commit it before its runs, and continue normally.

To close, write a Retrospective in the final Digest or a short closing document: what held, what
died, what the sequence of nights establishes, and the honest limitations. The collection should
read oldest to newest as question -> journey -> verdict.

---

## Agent contract

- **Triggers** — `AUTORESEARCH`, "shape/refine this research idea", "start/continue the research
  program", "plan tonight", "work the night", "run tonight's experiments", "review last night",
  "resume", "pivot", or "close the program".
- **Single front door** — do not redirect the user to phase-specific commands. Resolve state and
  continue here.
- **Gates** — local rules first; inspect the state of play and obtain approval for a complete
  Programme Brief before registering a program; require a kill criterion for every queued
  experiment; lock the mandate on `main` before compute; run only approved entries within budget;
  never edit locked scientific criteria; never merge the agent's own PR.
- **Idempotence** — resume existing mandates, branches, runs, and PRs. Never duplicate them.
- **Report & apply** — show the current state, do its next safe phase, and stop only at a human gate,
  completed unattended shift, genuine blocker, or explicit program closure.
