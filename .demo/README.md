# Internal Demolab demo

These are tiny, hand-authored synthetic presentation inputs for this checkout's
internal demo, not scientific results.
No Pinglab files, dependencies, or real runs are used. All demo configuration,
articles, data, and discovery script live here; all generated runtime stays in the repository's
`.demolab/`. Ordinary user labs keep their existing layout.

Run `uv run demolab dev` from the repository root. The homepage's data-source
collection and the welcome page link to all four cases:

| Article | Case | Initial Latest preview | Ordinary build |
| --- | --- | --- | --- |
| `/benchmark-a` | One run | 88%, one figure | 64% |
| `/benchmark-gallery` | Multiple experiments | 88% and 92%, two figures | 64% and 92% |
| `/benchmark-comparison` | Paired comparisons | 88% / 88% and 92% / 92%, zero differences | 64% / 88% (+24 pp), 72% / 92% (+20 pp) |
| `/benchmark-empty` | No runs yet | Empty selector, pending image/video, awaiting results | Discovered empty input, pending content |

## Authored timestamps

The welcome article uses explicit example creation and update datetimes to demonstrate
hours and minutes in compact listings, the article header, and PDFs. They are authored
fixture values, not file or build timestamps. Other articles keep date-only metadata so
both presentations can be checked together.

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
3. Choose run 001 for the single-run article: it shows 64%, independently of the gallery.
4. Selections update immediately and are stored in the URL fragment. Refresh the same URL
   to restore them. Reset to default returns only this article's inputs to Latest.
5. Run `uv run demolab build`: ordinary `.demolab/site/` and PDFs use the committed build pins,
   regardless of local preview choices. No controls are written into publication output.

Each article binds `data-file.with(article: "<its-id>", sources: sources)` before reading
inputs. Comparison keys are `baseline.benchmark-a`, `candidate.benchmark-a`, and equivalent
B keys. `build.sources` in `demolab.yaml` pins the ordinary build's run directories; the Typst
`sources` dictionaries remain the fallback only when neither pins nor discovery bind an input.
Remove build pins to use Latest in ordinary builds. Hardcoded paths
are deliberately not used for selectable demo inputs.

## Try a fixed build

Run `uv run demolab build`: the three populated examples use the fixed runs in the table above,
regardless of preview selections. Change only `build.sources.benchmark-a.benchmark-a` to
`data/benchmark-a-run-002` and build again: that article becomes 88%, without changing the gallery
or paired comparison. Restore `data/benchmark-a-run-001` for the baseline. Paths are relative to
this directory; inputs are read directly, not copied into another publication-data directory.
The no-runs demo is intentionally unpinned and resolves an empty Latest input.

## Try the empty state

Open `/benchmark-empty`: no configuration changes are needed. Its explicitly attached
`benchmark-empty` experiment has no run directories. The article demonstrates the disabled
selector, awaiting numerical results, and themed image/video placeholders alongside readable
prose. Ordinary builds resolve the same empty input without adding selectors or reading absent files.

Temporarily change `preview.discover` in `.demo/demolab.yaml` to
`[python, -c, "print('[]')"]`, then Reset to default in any article with a pinned selection.
The other three articles also retain their prose and headings, show pending figures and awaiting-run
numerical results, and have disabled **No runs available** selectors. No data files need moving
or deleting. Restore `[python, scripts/discover_runs.py]` to populate Latest again.
The single-input article is explicitly attached in YAML so it also works with an empty catalogue
on the very first build. Without that declaration, automatic matching begins with the first run.
`data-json()` / `data-image()` plus native conditionals implement these states; `video()` accepts
the same missing-input sentinel for articles with videos.

Dev watches configuration, writings, source data, the discovery script, and its project-owned
dependencies. It reads run inputs directly. Preview state/output stay under `.demolab/preview/`; errors leave the last
successful site visible with a warning and usable selectors. `uv run demolab clean` removes
generated state/output, never this directory. See AUTHORING for the full optional protocol.
