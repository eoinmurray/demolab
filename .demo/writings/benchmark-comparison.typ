#import "/.demolab/lib.typ": *

#let meta = (
  title: "Benchmark comparison — paired runs",
  created_at: "2026-08-27",
  description: "Two experiments, each comparing a baseline and candidate run with independent inputs.",
  collection: "data-source-demos",
)

// Four independent inputs, grouped into two comparisons by the article's layout.
#let sources = (
  "baseline-a": "benchmark-a-run-001",
  "candidate-a": "benchmark-a-run-002",
  "baseline-b": "benchmark-b-run-001",
  "candidate-b": "benchmark-b-run-002",
)
#let data-file = data-file.with(sources: sources)

#let body = [
  *Synthetic demo data, not experimental evidence.* Case 3: one article compares multiple runs.
  Each experiment has independent baseline and candidate data keys. These are fixed authored
  choices; grouping them visually does not introduce a campaign selector or automatic Latest policy.

  #for (suffix, title) in (("a", "Benchmark A"), ("b", "Benchmark B")) {
    let baseline-key = "baseline-" + suffix
    let candidate-key = "candidate-" + suffix
    let baseline = json(data-file(baseline-key + "/numbers.json"))
    let candidate = json(data-file(candidate-key + "/numbers.json"))
    let difference = candidate.accuracy_percent - baseline.accuracy_percent
    [
      == #title

      #table(
        columns: (1fr, 1fr),
        gutter: 8pt,
        inset: 4pt,
        [*Baseline* · #raw(baseline-key)], [*Candidate* · #raw(candidate-key)],
        [#baseline.run_id (#baseline.label)], [#candidate.run_id (#candidate.label)],
        [#image(data-file(baseline-key + "/accuracy.svg"), width: 100%, alt: title + " baseline accuracy: " + str(baseline.accuracy_percent) + " percent.")],
        [#image(data-file(candidate-key + "/accuracy.svg"), width: 100%, alt: title + " candidate accuracy: " + str(candidate.accuracy_percent) + " percent.")],
        [*#baseline.correct of #baseline.total* correct: *#baseline.accuracy_percent% accuracy*.],
        [*#candidate.correct of #candidate.total* correct: *#candidate.accuracy_percent% accuracy*.],
      )

      Candidate minus baseline: *#difference percentage points*, calculated from this pair's JSON inputs.
    ]
  }

  Each cell's prose and figure come from the same run. Changing one input must update that
  cell and its calculated difference, without changing the other inputs or either of the
  #link("benchmark-a")[single-run] and #link("benchmark-gallery")[gallery] articles.
]
