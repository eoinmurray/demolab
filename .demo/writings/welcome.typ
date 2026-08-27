#import "/.demolab/lib.typ": *

#let meta = (
  title: "Welcome",
  created_at: "2026-08-26",
  updated_at: "2026-08-27",
  description: "A minimal working page in the example site.",
  collection: "pages",
  order: 1,
)

#let body = [
  This is a small working Demolab site. Each file under `.demo/writings/` becomes a web page and,
  when PDF output is enabled, a PDF.

  == A deliberately small fixture

  The checkout keeps only enough example content to exercise listings, navigation, assets, and
  builds. Run `demolab dev` to preview it or `demolab build` to produce the static output.

  == Data-source demos

  Four articles exercise presentation inputs through `data-file()`:

  - #link("benchmark-a")[One run]: one experiment's prose and figure from one run.
  - #link("benchmark-gallery")[Multiple inputs]: one article assembles runs from two experiments.
  - #link("benchmark-comparison")[Paired comparisons]: baseline and candidate runs for each experiment.
  - #link("benchmark-empty")[No runs yet]: an empty selector, pending figure, and pending video.

  All data is synthetic. Local preview offers independent run selectors; ordinary builds retain
  the fixed authored inputs. Initial preview selections follow Latest.
]
