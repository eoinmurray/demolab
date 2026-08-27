#import "/.demolab/lib.typ": *

#let meta = (
  title: "Benchmark — awaiting its first run",
  created_at: "2026-08-27",
  description: "An experiment with no runs: empty selector, numerical results, image, and video.",
  collection: "data-source-demos",
)

// There are deliberately no benchmark-empty runs or publication inputs.
// Preview resolves the explicit empty input; ordinary builds author the same
// pending state directly, without trying to read nonexistent publication files.
#let resolve = data-file.with(article: "benchmark-empty")
#let data-file(path) = if "demolab-preview-file" in sys.inputs { resolve(path) }
#let result = data-json(data-file("benchmark-empty/numbers.json"))

#let body = [
  This experiment has no runs yet. Its explanation remains readable while the results,
  figure, and video wait for data. The preview selector above shows *No runs available*.

  == Results

  #if result == none [Awaiting a run. Numerical results will appear here.] else [
    Accuracy: *#result.accuracy_percent%*.
  ]

  #figure(
    data-image(data-file("benchmark-empty/accuracy.svg"), width: 100%, alt: "Benchmark accuracy."),
    caption: [The accuracy figure will appear when a run supplies it.],
    kind: image,
    supplement: [Figure],
  )

  == Demonstration

  #video(data-file("benchmark-empty/demo.mp4"), caption: [The demonstration video is awaiting a run.])

  == Meanwhile

  No results have been invented or borrowed from another experiment. The other
  #link("data-source-demos")[data-source demos] still have their usual runs and selectors.
]
