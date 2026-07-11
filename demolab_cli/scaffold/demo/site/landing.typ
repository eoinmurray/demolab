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
    html.elem("p", attrs: (class: "welcome-body"), [
      Demolab is a lab notebook for computational science. You write an experiment once as a
      small program; a coding agent runs it, stamps every result with the exact code version
      it came from, and publishes it — figures, live numbers, real maths — to web and PDF.
    ])
    html.elem("p", attrs: (class: "welcome-body"), [
      This site is itself a demolab lab, built and published by the engine it documents.
    ])
    html.elem("p", attrs: (class: "welcome-links"), {
      link("https://github.com/eoinmurray/demolab", "GitHub")
      [ · ]
      link("ar018.html", "Introduction")
      [ · ]
      link("documentation.html", "Documentation")
    })

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
        ([Start], (
          ("ar018.html", "Introduction"),
          ("ar019.html", "Why demolab"),
          ("ar017.html", "Getting started"),
        )),
        ([Concepts], (
          ("ar012.html", "The vocabulary"),
          ("ar013.html", "The folder structure"),
          ("ar016.html", "The contract"),
        )),
        ([Build], (
          ("ar023.html", "Anatomy of an experiment"),
          ("ar024.html", "Writing a writeup"),
          ("ar015.html", "Writing style"),
          ("ar014.html", "Authoring slides"),
        )),
        ([Operate], (
          ("ar010.html", "Runbooks"),
          ("ar022.html", "The command line"),
          ("ar025.html", "Configuring your lab"),
          ("ar020.html", "Publishing your lab"),
          ("ar021.html", "Updating the engine"),
          ("ar011.html", "Getting help"),
        )),
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

    html.elem("p", attrs: (class: "welcome-kicker"), [How it works])
    html.elem("p", attrs: (class: "welcome-body"), [
      One decoupled loop: _a tool computes → drops data → an experiment writes it up → the
      site publishes it._
    ])
    html.elem("p", attrs: (class: "welcome-body"), {
      [Every run records its parameters and the git commit it came from, stamped on the page.
        Tables read their numbers straight from the run, so prose and results can't disagree.
        One Typst pass emits the website, a PDF per entry, and a book — all sharing the same
        numbers. The full rules are in ]
      link("ar016.html", "The contract")
      [.]
    })

    html.elem("p", attrs: (class: "welcome-kicker"), [What you can ask your agent])
    html.elem("p", attrs: (class: "welcome-body"), [
      Open your lab in your agent and say a runbook's name — it follows it step by step:
    ])
    html.elem("dl", attrs: (class: "welcome-runbooks"), {
      for (name, desc) in (
        ("FROM-JUPYTER", [launder a notebook into a seeded, reproducible experiment]),
        ("FROM-PAPER", [reproduce a paper's key result in your stack]),
        ("RED-TEAM", [adversarially check a result before you publish it]),
        ("STEELMAN", [build the strongest honest case, so you don't under-sell it]),
        ("NEXT", [read your whole arc and propose the next experiments]),
        ("NIGHT-SHIFT", [work the queued experiments overnight, unattended]),
      ) {
        html.elem("div", attrs: (class: "welcome-runbook"), {
          html.elem("dt", name)
          html.elem("dd", desc)
        })
      }
    })
    html.elem("p", attrs: (class: "welcome-note"), {
      link("ar010.html", "Runbooks")
      [ lists all seventeen.]
    })

    html.elem("p", attrs: (class: "welcome-foot"), {
      link("https://github.com/eoinmurray/demolab/blob/main/LICENSE", "Open source, MIT licensed.")
    })
  })
}
