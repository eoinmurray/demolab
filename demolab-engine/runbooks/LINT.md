# Runbook: Lint against the house style

Triggers: **"lint"**, "lint the writings", "lint the repo against the house style", "check the house style", "does this read like an LLM wrote it". Goal: check a repo's writings against [`HOUSESTYLE.md`](../guides/HOUSESTYLE.md) (H1–H23), report each violation with the H-rule it breaks and a `file:line`, and fix only what the user approves.

This is the **style** pass — one of three: *Doctor* audits the structural RULES, *Lint* (here) audits the prose, and *Red-team* audits whether the result is true and defensible. Run all three for a full check. `HOUSESTYLE.md` is the source of truth for every rule: this runbook cites it, it does not restate it. Scope is `writings/*.typ` (the published prose); the framework docs are reference material and out of scope unless the user asks.

**Lint against the *effective* style.** First check for a root `HOUSESTYLE.local.md`. If it's absent, use these defaults. In `extend` mode (default) its rules override or add to the defaults — apply the merged set, and where the two conflict the local file wins. In `replace` mode (its first line is `<!-- mode: replace -->`) lint against **only** the local file and ignore the H-rules entirely. Report against whichever set is in force. The checks below are for the default style; drop or adjust any the local file overrides.

Drive it interactively: run the mechanical checks, read each writing for the judgment ones, collect the hits, present one report grouped by rule, then offer to fix.

## 0. Build is green
`task build` must compile first. Linting broken Typst is noise.

## 1. Mechanical checks (grep — each hit is a candidate, not a verdict)

```sh
# H7 — no em-dashes in prose. Titles, headings, and labels are fine, so read each hit in
# context before flagging it.
grep -nE '—' writings/*.typ

# H6 — tilde misuse. In Typst prose `~` is a non-breaking space; for "approximately" use ≈.
grep -nE '~' writings/*.typ

# Voice: LLM-tell vocabulary. A hit is a smell, not proof — read the sentence.
grep -inE 'delve|leverage|utiliz|seamless|robust|comprehensive|nuanced|multifaceted|underscore|pivotal|tapestry|realm|landscape|in today.?s|it.?s (important|worth) (to note|noting|mentioning)|game.?chang|revolutioniz|unlock the' writings/*.typ

# Voice: antithesis / false-balance scaffolding ("not just X but Y", "while … also").
grep -inE 'not (just|only) .* but( also)?|while .*, .* (also|there)' writings/*.typ

# H24 — hand-typed citations. A bracketed number in the source that isn't a `#cite(...)` gets no
# link + no hover popover. Math intervals/indices ([0,1], matrix delims) are false positives — read
# each hit, and check it isn't a manually written references list either.
grep -nE '\[[0-9]+( *, *[0-9]+)*\]' writings/*.typ
```

## 2. Judgment checks (read each writing — no grep suffices)

- **§H1 titles.** `meta.title` is a bare sentence, no id prefix.
- **§H2–H4 prose.** Reports partial/negative results honestly; leads with the claim; no repo bookkeeping in the body.
- **§H5 define every symbol.** After each equation, every symbol is defined (a list for dense blocks; the Hodgkin–Huxley sheet is the model).
- **§H7 em-dashes in prose.** For each grep hit from §1, confirm it is running prose (a violation) rather than a title / heading / label (fine).
- **§H16–H20 captions.** Each caption is standalone, follows the lead → axes-with-units + panels → takeaway anatomy, uses present tense, and pulls its numbers from the run (`#run…`) rather than a hand-typed literal.
- **§H9 numbers.** Every run number in prose, captions, and tables traces to `numbers.json`, never a typed literal that can drift.
- **§H24 citations.** Inline cites use `#cite(...)` and the reference list `#reference-list(...)` — not hand-typed brackets or a manual list (which get no link, popover, or auto-numbering). Each reference carries a DOI where one exists.
- **Voice (the real one).** Sentence rhythm varies (not every sentence the same medium length); no rule-of-three-everything; it takes a position rather than hedging both sides. Does it read like a person or a model?

## 3. Report
Present one report grouped by severity:

- **Prose tells** (em-dashes in prose, LLM vocabulary, false balance) — fix; they're the loudest giveaways.
- **Can't-drift** (hand-typed run numbers, §H9/H16–H20) — fix before publishing.
- **Advisory** (voice, structure, define-terms consistency) — the user's call.

For each finding: name the rule (link `../guides/HOUSESTYLE.md`), the `file:line`, and the rewrite. Apply only what the user approves, then re-run the relevant checks to confirm.
