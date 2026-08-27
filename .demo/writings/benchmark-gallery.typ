#import "/.demolab/lib.typ": *

#let meta = (
  title: "Benchmark gallery — multiple inputs",
  created_at: "2026-08-27",
  description: "One article assembles results from two experiments, with one run per data key.",
  collection: "data-source-demos",
)

// A synthesis article: one independently bound run for each experiment.
#let sources = (
  "benchmark-a": "benchmark-a-run-001",
  "benchmark-b": "benchmark-b-run-002",
)
#let data-file = data-file.with(article: "benchmark-gallery", sources: sources)
#let result-a = json(data-file("benchmark-a/numbers.json"))
#let result-b = json(data-file("benchmark-b/numbers.json"))

#let body = [
  *Synthetic demo data, not experimental evidence.* Case 2: one article assembles presentation
  data from multiple experiments. Each key supplies its own prose and figure. Local preview
  selects each input independently; ordinary builds retain the authored choices.

  == Benchmark A

  Run *#result-a.run_id* (#result-a.label) correctly classifies
  *#result-a.correct of #result-a.total* examples: *#result-a.accuracy_percent% accuracy*.

  #figure(
    image(data-file("benchmark-a/accuracy.svg"), width: 100%, alt: "Gallery benchmark A accuracy: " + str(result-a.accuracy_percent) + " percent."),
    caption: [Benchmark A: #result-a.accuracy_percent% accuracy, read through `benchmark-a`.],
  )

  == Benchmark B

  Run *#result-b.run_id* (#result-b.label) correctly classifies
  *#result-b.correct of #result-b.total* examples: *#result-b.accuracy_percent% accuracy*.

  #figure(
    image(data-file("benchmark-b/accuracy.svg"), width: 100%, alt: "Gallery benchmark B accuracy: " + str(result-b.accuracy_percent) + " percent."),
    caption: [Benchmark B: #result-b.accuracy_percent% accuracy, read through `benchmark-b`.],
  )

  These are separate benchmark results, not a before/after comparison or a combined score.
  The `benchmark-a` key also appears in #link("benchmark-a")[the single-run article];
  preview selections stay independent between the two articles.
  For two runs per experiment, see the #link("benchmark-comparison")[paired comparison].
]
