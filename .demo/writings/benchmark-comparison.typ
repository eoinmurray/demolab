#import "/.demolab/lib.typ": *

#let meta = (
  title: "Benchmark comparison — paired runs",
  created_at: "2026-08-27",
  description: "Two experiments, each comparing a baseline and candidate run with independent inputs.",
  collection: "data-source-demos",
)

// Four independent inputs, grouped into two comparisons by the article's layout.
#let sources = (
  "baseline.benchmark-a": "benchmark-a-run-001",
  "candidate.benchmark-a": "benchmark-a-run-002",
  "baseline.benchmark-b": "benchmark-b-run-001",
  "candidate.benchmark-b": "benchmark-b-run-002",
)
#let data-file = data-file.with(article: "benchmark-comparison", sources: sources)

#let body = [
  *Synthetic demo data, not experimental evidence.* Case 3: one article compares multiple runs.
  Each experiment has independent baseline and candidate data keys. Both groups initially follow
  Latest in preview, so their differences start at zero. Choose an older baseline to compare runs.

  #for (suffix, title) in (("a", "Benchmark A"), ("b", "Benchmark B")) {
    let baseline-key = "baseline.benchmark-" + suffix
    let candidate-key = "candidate.benchmark-" + suffix
    let baseline = data-json(data-file(baseline-key + "/numbers.json"))
    let candidate = data-json(data-file(candidate-key + "/numbers.json"))
    let run-label(result) = if result == none [Awaiting a run.] else [#result.run_id (#result.label)]
    let accuracy(result) = if result != none [
      *#result.correct of #result.total* correct: *#result.accuracy_percent% accuracy*.
    ]
    [
      == #title

      #table(
        columns: (1fr, 1fr),
        gutter: 8pt,
        inset: 4pt,
        [*Baseline* · #raw(baseline-key)], [*Candidate* · #raw(candidate-key)],
        run-label(baseline), run-label(candidate),
        [#data-image(data-file(baseline-key + "/accuracy.svg"), width: 100%,
          alt: if baseline != none { title + " baseline accuracy: " + str(baseline.accuracy_percent) + " percent." })],
        [#data-image(data-file(candidate-key + "/accuracy.svg"), width: 100%,
          alt: if candidate != none { title + " candidate accuracy: " + str(candidate.accuracy_percent) + " percent." })],
        accuracy(baseline), accuracy(candidate),
      )

      #if baseline == none or candidate == none [
        Comparison pending · awaiting both runs.
      ] else [
        Candidate minus baseline: *#(candidate.accuracy_percent - baseline.accuracy_percent) percentage points*, calculated from this pair's JSON inputs.
      ]
    ]
  }

  Each cell's prose and figure come from the same run. Changing one input must update that
  cell and its calculated difference, without changing the other inputs or either of the
  #link("benchmark-a")[single-run] and #link("benchmark-gallery")[gallery] articles.
]
