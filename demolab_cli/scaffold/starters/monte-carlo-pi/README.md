# Starter: Monte Carlo estimate of π

Engine reference data for the **universal backup** starter in
[`../../../runbooks/GETTING-STARTED.md`](../../../runbooks/GETTING-STARTED.md) step 2 —
the one offered when a user has no idea of their own. **Read it, model the user's
`experiments/exp000.py` + `writings/exp000.typ` on it, never overlay it** (same status as
`scaffold/demo/`).

Throw `N` random points at the unit square, count how many fall inside the quarter circle,
estimate `π ≈ 4 · inside / N`. One obvious knob (`N` → a tighter estimate), seeded so it
reproduces bit-for-bit, and it shows off the provenance machinery cleanly.

## The two figures — always produce both

This is the "nice plot every time" contract. A Monte Carlo π experiment renders exactly
these two, styled from `helpers/style.py` (HOUSESTYLE H10–H16):

1. **Scatter** (`scatter.png`) — a readable subsample of the thrown points, coloured
   **inside** (`style.INK`) vs **outside** (`style.BAND` grey), with the quarter-circle arc
   `x² + y² = 1` drawn in `style.ACCENT`. Equal aspect, axes `[0, 1]`. This is the case H13
   allows colour for: two categories sharing one axis.
2. **Convergence** (`convergence.svg`) — the running estimate `4·cumsum(inside)/n` against
   `n` on a **log x-axis**, with `π` as a dashed `style.ACCENT` reference line. Shows the
   estimate wandering, then settling toward π.

Both are computed from the sampled points in the runner — never hand-drawn, never
hand-typed into the write-up.

## Collection

The write-up declares `collection: "monte-carlo"`. A `collection:` that isn't in the root
`demolab.yaml` registry still renders, but title-cases with **no description**. When you
land this starter, **register the collection** (RULES §6.5) — add to `demolab.yaml`:

```yaml
collection-order: [..., monte-carlo]
collections:
  monte-carlo:
    label: Monte Carlo
    description: Estimation by random sampling — throw darts, count fractions, watch the estimate converge.
```
