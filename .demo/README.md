# Internal Demolab demo

These are tiny, hand-authored synthetic presentation inputs for this checkout's
internal demo, not scientific results.
No Pinglab files, dependencies, or real runs are used. All demo configuration,
articles, data, and discovery script live here; all generated runtime stays in the repository's
`.demolab/`. Ordinary user labs keep their existing layout.

Run `uv run demolab dev` from the repository root. The homepage's data-source
collection and the welcome page link to all three cases:

| Article | Case | Initial Latest preview | Ordinary build |
| --- | --- | --- | --- |
| `/benchmark-a` | One run | 88%, one figure | 64% |
| `/benchmark-gallery` | Multiple experiments | 88% and 92%, two figures | 64% and 92% |
| `/benchmark-comparison` | Paired comparisons | 88% / 88% and 92% / 92%, zero differences | 64% / 88% (+24 pp), 72% / 92% (+20 pp) |

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

`scripts/discover_runs.py` reads this metadata and emits the generic discovery protocol;
`data_key` identifies the fixture experiment, not article aliases. This is not a synthetic
Pingstore store or a Pingstore contract validator.

## Try the selectors

1. Open `benchmark-comparison`. Both groups initially follow Latest. Choose A run 001
   for `baseline.benchmark-a`: its prose and figure become 64%, and the difference becomes
   24 percentage points. Choose B run 001 for `baseline.benchmark-b`: its difference becomes 20.
2. Open `benchmark-a` and `benchmark-gallery`: both still use A run 002, independently.
3. Choose Published/default for the single-run article: it returns to the authored 64%.
4. Reload or restart dev: explicit choices remain. Reset all selections to Latest starts over.
5. Run `uv run demolab build`: ordinary `.demolab/site/` and PDFs retain authored defaults,
   regardless of local preview choices. No controls are written into publication output.

Each article binds `data-file.with(article: "<its-id>", sources: sources)` before reading
inputs. Comparison keys are `baseline.benchmark-a`, `candidate.benchmark-a`, and equivalent
B keys; its `sources` dictionary defines the separate publication choices. Hardcoded paths
are deliberately not used for selectable demo inputs.

Dev watches configuration, writings, source data, and the discovery script. It reads run
inputs directly. Preview state/output stay under `.demolab/preview/`; errors leave the last
successful site visible with a warning and usable selectors. `uv run demolab clean` removes
generated state/output, never this directory. See AUTHORING for the full optional protocol.
