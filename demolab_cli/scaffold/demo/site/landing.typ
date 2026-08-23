#import "/.demolab/lib.typ": *

#let body = html.elem("main", attrs: (class: "welcome"), {
  html.elem("section", attrs: (class: "welcome-hero"), {
    html.elem("p", attrs: (class: "welcome-kicker"), "Typst presentation system")
    html.elem("h1", "Write pages. Publish a site.")
    html.elem("p", attrs: (class: "welcome-lead"), [
      Demolab turns Typst writings and ordinary assets into a static website with optional PDFs.
    ])
    html.elem("pre", "uvx demolab-cli init\nuv sync\nuv run demolab dev")
  })
  html.elem("section", attrs: (class: "welcome-section"), {
    html.elem("h2", "One small pipeline")
    html.elem("p", [
      Put pages in `writings/`, inputs in `assets/`, and run `demolab build`. Collections,
      citations, themes, video, decks, and deployment are presentation features—not a research
      framework.
    ])
    html.elem("p", link("welcome.html", "Read the three-page guide →"))
  })
})
