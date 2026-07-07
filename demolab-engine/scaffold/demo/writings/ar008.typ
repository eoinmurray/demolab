#let meta = (
  title: "Guides",
  date: "2026-07-07",
  description: "The always-on reference that defines how a demolab lab works — the rules, the house style, the deck conventions, the file structure, and the vocabulary.",
  collection: "documentation",
  status: "final",
)

#let base = "https://github.com/eoinmurray/demolab/blob/main/demolab-engine/guides"

#let body = [
  Guides are demolab's *reference layer* — the conventions you and the agent can lean on at any
  moment. They live inside the engine (`demolab-engine/guides/`), so they version with it and are
  always in force rather than run on demand. Ask the agent a guide's name in capitals and it walks
  you through the relevant part; the canonical text is the Markdown source, linked in each section
  below.

  == RULES — the contract

  #link(base + "/RULES.md")[RULES.md] is the law of a demolab repo: the toolchain, the
  engine-versus-content *firewall* (what updates wholesale, and what's yours), the schema a tool
  and an experiment must satisfy, and the step-by-step for adding a tool, an experiment, or a
  writing. When a convention has teeth it is numbered here as a §-rule, so everything else can
  cite it.

  == HOUSESTYLE — how a write-up reads

  #link(base + "/HOUSESTYLE.md")[HOUSESTYLE.md] governs the prose: sentence-level style, how math
  is set, how figures are captioned and cross-referenced, and how citations work — as numbered
  H-rules. You can extend or override any of it per-lab with a root `HOUSESTYLE.local.md`.

  == SLIDES — decks

  #link(base + "/SLIDES.md")[SLIDES.md] covers slide decks (`writings/*.slide.typ`): the Touying
  skeleton, sizing against the fixed canvas, the silent-overflow trap and the page-count check, and
  a named, liftable *layout catalog* you copy from rather than re-deriving a layout each time.

  == STRUCTURE — the file tree

  #link(base + "/STRUCTURE.md")[STRUCTURE.md] is the annotated map of the repository: what every
  directory and file is, and which rule governs it. It's the fastest way to answer "where does this
  live, and why here?"

  == GLOSSARY — the vocabulary

  #link(base + "/GLOSSARY.md")[GLOSSARY.md] defines the terms precisely — tool, experiment, writing,
  deck, collection, artifact, provenance — and draws the line between the ones that are easy to
  confuse, like a *tool* versus an *experiment*.

  == SUPPORT — reaching a human

  #link(base + "/SUPPORT.md")[SUPPORT.md] is the escape hatch: how to report a bug or ask a
  question when the agent and the guides don't settle it between them.

  Their on-demand counterpart — *runbooks* — has its own article in this collection.
]
