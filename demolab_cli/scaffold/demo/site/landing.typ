// The upstream landing page (demolab.eoinmurray.info) — a custom homepage body rendered
// instead of the collection directory (see lib.typ index-page). Lives under site/ so
// `demolab add-demo-content` never copies it into a user's lab (site/ is excluded from the
// overlay); the Pages deploy (.github/workflows/landing.yml) copies it to the repo root
// before building. Any lab can do the same: a root landing.typ exporting `#let body`
// takes over the homepage below the brand header.
//
// Web-only markup: the homepage is only emitted as HTML, so html.elem is safe here.
// The .welcome-* classes live in the engine's style.css (staged at /.demolab/style.css) — reuse or ignore them.
#let body = {
  html.elem("div", attrs: (class: "welcome"), {
    html.elem("p", attrs: (class: "welcome-body"), [
      Reproducible, provenance-stamped results — published to web and PDF, run by a coding
      agent instead of a build system.
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
      [, then paste this into your coding agent:]
    })
    html.elem("div", attrs: (class: "welcome-cmd"), {
      html.elem("pre", "Clone github.com/eoinmurray/demolab and follow its GETTING-STARTED.md strictly.")
    })
    html.elem("p", attrs: (class: "welcome-foot"), {
      link("https://github.com/eoinmurray/demolab/blob/main/LICENSE", "Open source, MIT licensed.")
    })
  })
}
