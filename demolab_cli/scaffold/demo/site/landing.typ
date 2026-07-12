// The upstream landing page (demolab.eoinmurray.info) — a custom homepage body rendered
// instead of the collection directory (see lib.typ index-page). Lives under site/, kept
// separate from the writeups the rest of the demo dir holds; the Pages deploy
// (.github/workflows/landing.yml) copies it to the repo root before building. Any lab can do
// the same: a root landing.typ exporting `#let body` takes over the homepage below the brand header.
//
// Web-only markup: the homepage is only emitted as HTML, so html.elem is safe here.
// The .welcome-* classes live in the engine's style.css (staged at /.demolab/style.css) — reuse or ignore them.
#let body = {
  html.elem("div", attrs: (class: "welcome"), {
    // Hero: the problem, the pitch, and the proof — this very site is a demolab lab.
    html.elem("p", attrs: (class: "welcome-links"), {
      link("documentation.html", "Documentation")
      [ · ]
      link("https://github.com/eoinmurray/demolab", "GitHub")
    })
    html.elem("p", attrs: (class: "welcome-body"), [
      Demolab is a lab notebook for computational science that keeps coding agents on rails.
      You say what to compute; the agent writes and runs the experiment — in Python by default,
      though any stack works. Demolab stamps every result with the exact code version it came
      from, reads the numbers straight from the run so nothing drifts, and typesets it all with
      Typst — figures, live numbers, real maths — to web and PDF.
    ])
    html.elem("p", attrs: (class: "welcome-body"), [
      This site is itself a demolab lab, built and published by the engine it documents.
    ])

    html.elem("p", attrs: (class: "welcome-kicker"), [Get started])
    html.elem("p", attrs: (class: "welcome-body"), {
      [Install ]
      link("https://docs.astral.sh/uv/getting-started/installation/", "uv")
      [ and ]
      link("https://github.com/typst/typst#installation", "typst")
      [, then open your coding agent in an empty folder and paste:]
    })
    html.elem("div", attrs: (class: "welcome-cmd"), {
      html.elem("pre", "Run `uvx demolab-cli init` here, then follow its GETTING-STARTED runbook strictly.")
    })
    html.elem("p", attrs: (class: "welcome-note"), {
      [Prefer to set it up by hand? See ]
      link("ar017.html", "Getting started")
      [.]
    })

    html.elem("p", attrs: (class: "welcome-kicker"), [Documentation])
    // The four tiers mirror the documentation collection's curated reading order
    // (each writing's meta `order:`): evaluate → start → understand/build → operate.
    html.elem("div", attrs: (class: "welcome-docs"), {
      for (tier, entries) in (
        (
          [Start],
          (
            ("ar018.html", "Introduction"),
            ("ar019.html", "Why demolab"),
            ("ar017.html", "Getting started"),
          ),
        ),
        (
          [Concepts],
          (
            ("ar012.html", "The vocabulary"),
            ("ar013.html", "The folder structure"),
            ("ar016.html", "The contract"),
            ("ar026.html", "Using another language"),
          ),
        ),
        (
          [Build],
          (
            ("ar023.html", "Anatomy of an experiment"),
            ("ar024.html", "Writing a writeup"),
            ("ar015.html", "Writing style"),
            ("ar014.html", "Authoring slides"),
          ),
        ),
        (
          [Operate],
          (
            ("ar010.html", "Runbooks"),
            ("ar022.html", "The command line"),
            ("ar025.html", "Configuring your lab"),
            ("ar020.html", "Publishing your lab"),
            ("ar021.html", "Updating the engine"),
            ("ar011.html", "Getting help"),
          ),
        ),
      ) {
        html.elem("div", attrs: (class: "welcome-docs-tier"), {
          html.elem("p", attrs: (class: "welcome-docs-label"), tier)
          html.elem("ul", {
            for (href, label) in entries {
              html.elem("li", link(href, label))
            }
          })
        })
      }
    })

    html.elem("p", attrs: (class: "welcome-foot"), {
      link("https://github.com/eoinmurray/demolab/blob/main/LICENSE", "Open source, MIT licensed.")
    })
  })
}
