# Runbook: Literature search

> Build an exhaustive, DOI-verified corpus of papers on a narrow question, and measure how
> complete it is. Two sources do the work — the model's pre-cutoff memory and live databases
> (OpenAlex, Crossref, arXiv) — with the model scoping and seeding while the databases and
> DOI-checks supply recall and precision. Produces a living article in `writings/` backed by a
> committed record in `artifacts/data/`. It builds the **corpus**, not the review — the map,
> synthesis, connections, and gaps are a later pass.

## When to use
When you want a near-exhaustive, auditable paper list on a question narrow enough that only a few
hundred papers exist — the PING mechanism for gamma, not "gamma oscillations." The premise is a
split of labour: the model is a good **size oracle** and a bad **recall oracle** (it can tell
hundreds from thousands, but can't list the hundreds without fabricating), so it scopes and seeds,
and the databases plus a DOI check do the finding and the fact-checking. What you get is a corpus
with a *measured* recall estimate, not a claim of completeness taken on faith. If the question
can't be narrowed to an exhaustible set, say so and offer a defensible sub-slice — an honest survey
beats a promise the method can't keep.

## The record — one bundle per search
Everything lives keyed to the article's `arNNN` id, and **the machine is the sole editor of it**.
The user reviews and answers `❓[ID]` markers; they never hand-edit the record — a quiet human edit
would make the recall numbers meaningless (you'd no longer know what the pipeline found versus what
someone typed). Going another round on a misread marker is expected and fine.

- `writings/arNNN.typ` — the living article, the reader's view. Reads the record via `data-file()`
  and renders the confidence header, bibliography, and provenance — regenerated each pass.
- `artifacts/data/arNNN/` — the committed record (the source of truth):
  - `scope.json` — the frozen scope: anchors, facets, synonym ring, explicit exclusions.
  - `corpus.jsonl` — one paper per line: doi, membership, `mechanism` (memory / search), in/out,
    verified, the run that found it.
  - `feedback.jsonl` — the `❓[ID]` review log: marker, the user's answer, how it was resolved.
  - `runlog.jsonl` — append-only phase ledger: every query fired, counts, the recall estimate at
    that step. This is what makes the corpus auditable without the scripts.
  - `numbers.json` — headline metrics for the confidence header (corpus size, estimated true size,
    recall %).
- `temp/arNNN/` — disposable scratch (gitignored): the one-off fetch/verify scripts and their raw
  API dumps. No committed tool — the work is the agent's judgment plus throwaway plumbing; the
  *record* is the reproducible artifact, not the scripts (raw data is disposable, the record is
  committed).

## What it does

0. **Refine the question — pure conversation, no files.** Walk the user from raw interest to a
   scout-ready question. Reflect the corpus size back from memory ("gamma broadly is thousands —
   not a search target; what specifically?"), offer narrowing *and widening* axes with their size
   implications (mechanism vs. phenomenon, model vs. experiment, region, species, era), and
   converge on **1-5 anchor papers** plus explicit in/out boundaries and the purpose. Exit when the
   estimate lands roughly 100-400 and the user signs off on a restated one-paragraph scope. Nothing
   touches disk yet — this stays cheap and restartable. Won't converge → name it and offer a
   sub-slice or an honest survey.

1. **Preflight — propose, never gate.** Check which sources are reachable and at what tier
   (OpenAlex / Crossref / arXiv keyless; Semantic Scholar and PubMed throttled without a free key).
   *Propose* optional upgrades with the reason and the cost of skipping — a contact email for the
   "polite pool", a free Semantic Scholar / NCBI key in `.env.local` — then proceed with whatever's
   there. Getting keys means signing up, so that's the user's action, not yours. Declining is a
   first-class answer (the email identifies them to third parties); default to keyless and don't
   nag. Whatever's missing becomes a neutral coverage caveat in the confidence header — auth status
   is provenance. In autonomous mode there's no one to ask: take the keyless defaults, log the same
   caveat.

2. **Scout — interactive.** A cheap Source-1 recon pass: fan out facets, flag terminology
   collisions ("PING" also names a network tool), harvest the author / venue / synonym vocabulary,
   and re-estimate size. Draft `scope.json` as a *proposal* with `❓[ID]` forks carrying a size
   estimate per cut ("include the clinical-epilepsy silo? ~+140"). Exit when the user answers the
   forks. This is the first thing that touches disk.

3. **Freeze — the gate.** Apply the answers, finalise `scope.json`, commit, and **tag the commit**
   (`freeze-arNNN-v1`). Scope is now immutable: the recall estimate is only valid because both
   samples target the same frozen population, so a drifting question corrupts the count. Scope
   reopens only via a new tag (a deliberate v2), never an edit to the frozen block; questions that
   surface later are logged, not acted on. Autonomous fallback: freeze on the widest defensible
   defaults and log them.

4. **Harvest — Source 1 (unattended).** The model's memory *as recall*, against the frozen
   vocabulary: facet × persona × temporal sweeps with repeated sampling and union (many decorrelated
   reads beat one lossy readout). DOI-verify every candidate against Crossref via a throwaway script
   in `temp/arNNN/`; discard anything that won't resolve — an unverifiable DOI is a hallucination.
   Write survivors to `corpus.jsonl` tagged `mechanism: [memory]`. This is sample **A**. Log every
   query to `runlog.jsonl`.

5. **Search — Source 2 (unattended).** The databases *as recall*, decorrelated from memory by
   attacking different indexes: synonym-ring keyword queries, semantic nearest-neighbour, author-
   resolved pulls, and concept-tag traversal across OpenAlex / Semantic Scholar / PubMed / arXiv
   (throwaway scripts in `temp/arNNN/`). Dedup against `corpus.jsonl`, relevance-filter, DOI-verify.
   Tag `mechanism: [search]`. This is sample **B**. Log every query. (No citation-graph traversal
   here — that's the phase-6 escalation, held until the measure step says it's warranted.)

6. **Measure (unattended).** Estimate the true corpus size and recall from the overlap between the
   two independent samples (Lincoln–Petersen capture-recapture: with `n_A` from memory, `n_B` from
   search, and `m` in both, the true size is about `n_A · n_B / m`). Write `numbers.json`, and plot
   cumulative-unique-papers against queries-fired to show saturation. If recall is below target,
   emit a `❓` proposing either more query angles or the citation-graph escalation — don't silently
   declare victory. Exit on saturation, or on the user's stop/continue answer.

7. **Hand off.** Regenerate `writings/arNNN.typ` from the record — confidence header (size,
   estimated true size, recall %, and the coverage caveats from preflight), the bibliography, and a
   provenance histogram showing which mechanism carried which papers. `demolab build`, open the page
   and PDF, and report the honest number: how big, how complete, and which silos memory versus
   search each reached. Offer the citation-graph pass as the next step if recall fell short.

---

## Agent contract
- **Triggers** — `LITERATURE-SEARCH`, **"literature search"**, "find all the papers on…",
  "exhaustive paper list", "how much is written on…".
- **Gates** — a scout-ready question is the input; step 0 produces it, and no anchors means stay in
  step 0. A **freeze tag must exist before any measured run** (steps 4-6) — the recall estimate is
  invalid without it. No database keys are required; preflight proposes them and proceeds keyless.
- **Report & apply** — interactive through the freeze (steps 0-3), unattended after (steps 4-6),
  honest hand-off at 7. **The machine is the sole editor of `artifacts/data/arNNN/`**; the user
  reviews and answers `❓[ID]` markers rather than editing the record. Log every query to
  `runlog.jsonl`; freeze the scope once per tag. State what the search *had* (sources, keys,
  reached silos) — a measured, caveated recall number is the deliverable, not a claim of
  completeness.
