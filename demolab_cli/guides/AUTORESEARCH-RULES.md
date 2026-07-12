# AUTORESEARCH-RULES — the semi-autonomous research contract

> The conventions for running a **research program** on demolab: a collection worked one night
> at a time by an overnight agent, pre-registered per night, and gated every morning by a human.
> This guide is the source of truth the three runbooks cite — **AUTORESEARCH** (start/steer a
> program), **PLAN** (queue the next night), **NIGHT-SHIFT** (work the night). It defines the
> per-night document, the queue schema, and the git workflow; the runbooks are the procedures.

## When to use

You and a collaborator want a research question worked semi-autonomously: steered by hand
during the day, run unattended for **at most one night** at a time, and never published without
review. This is not "an AI writes papers" — it's a lab notebook with a night shift. The whole
value is that every overnight claim is auditable the next morning, because demolab already
stamps every run with its git commit and reads every published number straight from the run.

## 1. The shape — one program = one collection, one document per night

A research program is exactly one demolab **collection** (RULES §6.5). It contains:

| Document | Article name | Role |
|---|---|---|
| **Night-shift documents** | `arNNN` ("Night shift — YYYY-MM-DD") | One self-contained document per night. Carries that night's mandate, record, and digest (§2). |
| **Experiments** | `expNNN` | Standard demolab entries (RULES §7), one per queue item that ran. |

There is **no standing `plan` and no standing `log`.** An earlier version of this contract used
three cross-linked, always-open documents (`plan` / `log` / `night-shift.yaml`); running a real
program showed they were brittle (slug renames broke every cross-link, three states drifted, the
log grew unbounded). One document per night replaces all three: append-only *across* nights —
a night's document is a working log the agent writes to throughout its own shift, but a closed
night is never edited, and each new night appends its own document. No cross-links, no drift.

**Tactical, not strategic.** The program is deliberately worked night by night, not against a
grand upfront plan. The overarching question and baseline are stated in the **first** night's
mandate; a mid-course pivot is stated in the mandate of the night it takes effect — dated, and
provably prior to that night's runs. The collection, read oldest to newest, *is* the arc:
question → journey → verdict. Give the night documents an ascending `order:` (RULES §6.5a) so
they list chronologically.

**Pre-registration is free here.** Because every page carries its commit (RULES §4.7), a
mandate committed before its night's runs is *provably* prior to the results. That is the
registered-reports guarantee, obtained from demolab's existing provenance rather than any new
machinery — and per-night pre-registration is more honest than one upfront plan, because it
never pretends the whole arc was known on night one. Protect it with the git rule (§5).

## 2. The night-shift document

One writing (`meta` + `body`, RULES §6.1) with `collection: <slug>` and an ascending `order:`.
Three sections, in rendered order **Digest → Mandate → Record** — the digest on top because it
is the morning read, read first and often only. The two authoring phases keep the existing
human/agent split:

- **Mandate — written by PLAN, on `main`, before the night.** The pre-registration: the queue
  slice this night will work, and the operating contract (budgets, scope, stop conditions). This
  section is human-authored and, once committed, **never edited** — a night branch may set queue
  *statuses* from run outputs, but never touches a hypothesis or kill criterion. Its commit is
  the pre-registration anchor.
- **Record — written by NIGHT-SHIFT, on the night branch, throughout the shift.** The working
  notebook: what ran, seeds, outcomes, aborts, and anomalies parked for a human. It accrues
  through the night; it is *not* style-exempt (§3).
- **Digest — written by NIGHT-SHIFT at shift end.** A ruthless triage summary (what confirmed,
  what died by its own criterion, which anomaly deserves attention) plus the night's `proposed`
  next steps. It is the morning read **and** the PR description (§5). The cross-night backlog
  lives here — each night proposes the next, the next night's PLAN picks them up. **No standing
  master queue.**

**Scientific log in the document, code log in git.** The Record is the *scientific* notebook —
what ran, what it showed, what was killed or parked. Engineering detail — what a tool or runner
changed and why, a debugging dead-end, a build fix — is a *code* log: it goes in the per-experiment
commit messages and, where the reviewer needs it in context, as comments on the night's PR, **not
in the Record**. This is what lets the Record cold-read (§3): a collaborator opening the document
wants the science, not the stack traces. The rule of thumb — would it mean anything to the
collaborating scientist? Science, into the document; plumbing, into the commits and the PR thread.

**The queue slice** (in the mandate) is structured data the runbooks read — a list of entries,
one per planned experiment (a `queue:` field in `meta`, or a fenced ```yaml block the runbooks
parse). Each entry:

| Field | Meaning |
|---|---|
| `id` | The `expNNN` id it will become. |
| `hypothesis` | The claim, stated so it can be wrong. |
| `kill` | **Required.** The result that falsifies it / aborts the run. No entry is queued without this. |
| `baseline` | What it must reproduce or beat (a published number, or an earlier `expNNN`). |
| `seeds` | Seed count for the sweep (§6). One seed is an anecdote, not a result. |
| `budget` | Per-run wall-clock ceiling (and any resource cap). Stops a diverging run eating the night. |
| `status` | `queued → running → done → killed`. **Read from run outputs, not hand-edited** (RULES §6.2) — the mandate can't claim a success that didn't run. |
| `origin` | `human` (queued via PLAN) or `proposed` (drafted in a prior night's digest, awaiting human approval). A `proposed` entry is never run. |

The typeset status table in the body is **generated from this queue** (single source, same trick
as `numbers-table`), so the published mandate and the agent's worklist can never disagree.

**The operating contract** (also in the mandate) is the policy the night obeys — budgets, scope,
and stop conditions. One night, one contract, stated in that night's document. Example:

```yaml
budgets:
  wall_clock_per_run: 45m      # hard ceiling per experiment
  wall_clock_per_night: 8h     # total shift budget
  seeds_default: 5
scope:
  collection: neuron-models    # the only collection this shift may touch
  may_propose: true            # append `proposed` next steps to the digest (never run them)
stop_when:
  - queue_empty
  - night_budget_exhausted
  - build_red_twice            # bail rather than thrash
```

## 3. Housestyle applies — no exemption, cold-read required

A night-shift document is a **published scientific artifact**, not private scratch. It obeys the
prose rules like any other entry (HOUSESTYLE / LINT) — the earlier "the log is deliberately
messy" exemption is gone: it licensed exactly what made real programs illegible (terminal
shorthand, metrics used before they are defined, no lead-with-the-claim).

- **Lint throughout the night, not only at the end.** NIGHT-SHIFT lints the document as it writes
  so drift is caught early instead of accumulating into an end-of-run mess. Subagent passes are
  fine. "Working document" means *mutable during its shift*, never *exempt from style*.
- **Cold-read is the bar.** The test is: *would a domain expert who has never seen this repo
  understand this?* Expand every shorthand, define every metric and symbol on first use, and lead
  each section with its claim. A program's documents must be sendable to a collaborator as-is,
  with no repo context. This is a LINT dimension (see LINT).
- **Still can't drift.** As with any page, figures and metrics cite the record; run numbers are
  never hand-typed (RULES §6.2).

## 4. Lab rules first

A cold cloud session runs on **engine defaults** unless the flow makes it read the lab's own
rules — which is how an unattended night once shipped a PR carrying an AI-attribution trailer its
lab's `AGENTS.md` explicitly banned. So every autoresearch procedure (AUTORESEARCH, PLAN,
NIGHT-SHIFT) **loads the lab-root `AGENTS.md` and `HOUSESTYLE.local.md` (if present) as its first
step, and obeys them — lab rules win over engine defaults** — before acting, not as an
afterthought. The morning gate (§5, DOCTOR) also checks for the concrete violations, so a
non-compliant artifact can't ship even if the agent misses the rule.

## 5. Git & PR workflow

- **Main is the published record.** Turn on branch protection; CI deploys the site from `main`
  only, so nothing publishes without a merge.
- **The mandate lands on `main` in a daytime PLAN session.** That commit is the night's
  pre-registration anchor. A night branch may update queue **statuses** and write the record +
  digest, but never edits a hypothesis or kill criterion — hypothesis changes are human-reviewed
  by construction.
- **One branch per night per program:** `night/YYYY-MM-DD-<collection>`. Programs touch disjoint
  collection directories, so parallel nights merge cleanly.
- **One commit per experiment attempt**, including killed ones — a negative result is a result,
  and per-experiment commits let you cherry-pick the two good runs out of a mixed night.
- **The commit messages and PR comments carry the code log** — the engineering narrative kept out
  of the Record (§2): what the runner/tool changed and why, debugging, build fixes. Put it in the
  per-experiment commit message, and surface anything the reviewer should weigh as a PR comment.
  The scientific record stays in the document; the code log stays in git and the PR thread.
- **Merge commits only — never squash or rebase.** Run stamps point at the night-branch commits;
  rewriting history breaks the provenance shown on published pages.
- **The PR is the morning gate.** NIGHT-SHIFT ends by opening a PR whose description *is* the
  digest. Triage = review the PR: merge, request changes ("rerun exp014, more seeds"), or close.
- **No AI-attribution in commits or the PR description.** Commits carry no agent authorship
  (house rule, RULES §2), and the PR description — being the digest — must not add a "Generated
  with…" / "Co-Authored-By" trailer either. Lab `AGENTS.md` may state this too (§4); DOCTOR
  checks both the commit trailers *and* the PR description. Accountability lives in the digest's
  prose ("ran under the night shift within this budget"), on the page a supervisor reads — not in
  git metadata.
- **Reaping:** enable GitHub's *auto-delete head branches on merge*
  (`gh api -X PATCH repos/{owner}/{repo} -f delete_branch_on_merge=true`); the preview teardown
  (the PR-preview workflow) fires on the same close/merge. Orphan branches (a crashed night, a
  closed-unmerged PR) are surfaced by NIGHT-SHIFT's resume check and killed by a human — no
  auto-reaper that could delete the only copy of a half-finished experiment. **Reap branches,
  never PRs:** merged/closed PRs are the audit trail.

## 6. SNN / compute-heavy rigor

- **Baseline gate.** Before any novel claim, the stack must reproduce a known baseline (e.g. a
  LIF network's published accuracy on N-MNIST / SHD). No trust without reproduction — it's the
  `baseline` field on the first night's queue entries.
- **Multi-seed by default.** A queue entry's `seeds` drives a sweep with error bars, not a
  single-seed anecdote. Bake this into the tool ↔ experiment contract before compute-heavy work.
- **Analysis plan precedes data.** The `kill` and `baseline` are committed in the mandate before
  the run — no HARKing a story out of the numbers after the fact. PLAN enforces it at queue time.

## 7. How it plugs into the existing rules

- Statuses and metrics are **read from `numbers.json`** (RULES §6.2), so the mandate and record
  can't drift from what ran.
- Pre-registration = **provenance** (RULES §4.7): the mandate's commit predates the results' commits.
- Long runs use **staged runners** (RULES §7.5) so a night can re-enter compute without repeating it.
- **NEXT** reads the night documents' records and digests (not just published results), so it
  proposes from the decision arc; its suggestions are the raw material a human turns into
  `queued` entries via **PLAN**.
- **DOCTOR** checks program structure (each night document carries a mandate + record + digest,
  every `queued` entry has a `kill`, no AI-attribution trailer in commits or PR descriptions).
- **LINT** applies the full prose rules to night documents, including the cold-read dimension.
