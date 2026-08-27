# Internal Demolab demo

These are tiny, hand-authored synthetic presentation inputs for this checkout's
internal demo, not scientific results or a new Demolab configuration format.
No Pinglab files, dependencies, or real runs are used. All demo configuration,
articles, and data live here; all generated runtime stays in the repository's
`.demolab/`. Ordinary user labs keep their existing layout.

Run `uv run demolab dev` from the repository root. The homepage's data-source
collection and the welcome page link to all three cases:

| Article | Case | Fixed inputs | Expected result |
| --- | --- | --- | --- |
| `/benchmark-a` | One run | `benchmark-a` → A run 001 | 64%, one figure |
| `/benchmark-gallery` | Multiple experiments | `benchmark-a` → A run 001; `benchmark-b` → B run 002 | 64% and 92%, two figures |
| `/benchmark-comparison` | Paired comparisons | `baseline-a` / `candidate-a` → A runs 001 / 002; `baseline-b` / `candidate-b` → B runs 001 / 002 | 64% / 88% (+24 pp) and 72% / 92% (+20 pp), four figures |

## Run data

| Fixture experiment | Run | Timestamp (UTC) | Result | Presentation directory |
| --- | --- | --- | --- | --- |
| benchmark-a | benchmark-a-run-001 | 2026-08-25T10:00:00Z | 16/25 correct, 64% | `.demo/data/benchmark-a-run-001/` |
| benchmark-a | benchmark-a-run-002 | 2026-08-26T10:00:00Z | 22/25 correct, 88% | `.demo/data/benchmark-a-run-002/` |
| benchmark-b | benchmark-b-run-001 | 2026-08-25T11:00:00Z | 18/25 correct, 72% | `.demo/data/benchmark-b-run-001/` |
| benchmark-b | benchmark-b-run-002 | 2026-08-26T11:00:00Z | 23/25 correct, 92% | `.demo/data/benchmark-b-run-002/` |

The four run directories are peers: no `default/`, `runs/`, or experiment nesting.
All contain the same filenames and JSON fields. Each SVG has a 0–100% scale and a
bar whose width agrees with the JSON. Run IDs, labels, and timestamps in
`numbers.json` describe these fixtures only, not the Pingstore contract.

## Current behaviour

- Every article reads JSON and SVG through `data-file()`, with explicit Typst
  bindings. For example, the comparison article binds:

  ```typ
  #let sources = (
    "baseline-a": "benchmark-a-run-001",
    "candidate-a": "benchmark-a-run-002",
    "baseline-b": "benchmark-b-run-001",
    "candidate-b": "benchmark-b-run-002",
  )
  #let data-file = data-file.with(sources: sources)
  ```

  This maps each data key to a directory beneath the data root; it does not
  discover runs, infer Latest, or introduce a browser selector. Omitting the
  optional mapping preserves ordinary labs' `.artifacts/<key>/` resolution.
- Each pair refers to runs of the same fixture experiment.
  The `data_key` field in the fixture JSON identifies the experiment, not the
  article's aliases. No new discovery metadata contract is introduced here.
- Dev and ordinary builds show the same authored choices listed above. Each input
  supplies its own figure and numerical prose; no direct-path reads bypass the keys.
- The single-run article's ID equals its experiment and key, exercising the proposed
  automatic-match convention. The gallery and comparison require explicit attachments
  in the future selector. No unimplemented preview configuration is added here.
- The gallery shares `benchmark-a` with the single-run article. Changing its local
  binding must leave the other article unchanged. Comparison cells are likewise
  independent; differences are calculated from the selected JSON inputs, never hardcoded.
- Dev watches `.demo/writings/`, `.demo/data/` (including alternative metadata),
  optional `.demo/assets/`, configuration, and the engine sources. It does not
  watch generated `.demolab/` output.
- `uv run demolab clean` removes generated output, never this directory.
  `uv run demolab build` recreates output from these inputs without modifying them.
- No run selection or automatic Latest policy is implemented.

## Later increments, not implemented here

Use these fixtures to add source selection, a Latest policy, and isolated
preview output. Add a separately validated synthetic Pingstore store when those behaviours are
implemented. Do not mutate or replace the defaults merely to simulate a selector.
