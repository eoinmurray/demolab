#import "/.demolab/lib.typ": *

#let meta = (
  title: "Benchmark A — one run",
  created_at: "2026-08-27",
  description: "One experiment article reads its numerical prose and figure from one run.",
  collection: "data-source-demos",
)

// Article ID, experiment, and data key agree: the ordinary one-input case.
#let sources = ("benchmark-a": "benchmark-a-run-001")
#let data-file = data-file.with(article: "benchmark-a", sources: sources)
#let result = json(data-file("benchmark-a/numbers.json"))

#let body = [
  *Synthetic demo data, not experimental evidence.* Case 1: one article, one data key, one run.
  The `benchmark-a` key supplies both the numerical prose and the figure below.
  In local preview the selector chooses the run; ordinary builds use the authored default.

  == Current result

  Run *#result.run_id* (#result.label), created #result.created_at, correctly classifies
  *#result.correct of #result.total* examples: *#result.accuracy_percent% accuracy*.

  #figure(
    image(data-file("benchmark-a/accuracy.svg"), width: 100%, alt: "Synthetic benchmark A accuracy: " + str(result.accuracy_percent) + " percent."),
    caption: [Accuracy from the same run as the numerical prose, through `benchmark-a`.],
  )

  Initial preview follows Latest; select run 001 to see the baseline. Reset to default returns to Latest.
  Also see the #link("benchmark-gallery")[multi-run gallery] and
  #link("benchmark-comparison")[paired comparison].
]
