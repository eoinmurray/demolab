# SLIDES — authoring decks

How to create slide decks (`writings/*.slide.typ`) and lay them out. Decks are talks:
paged PDFs built with [touying](https://typst.app/universe/package/touying), linked from
the site but never rendered into HTML or the book. For prose writeups see
[`HOUSESTYLE.md`](HOUSESTYLE.md); for what a *deck* is in one line see
[`GLOSSARY.md`](GLOSSARY.md). Rules are numbered `D<n>` so other docs can cite them.

## 1. What a deck is

**D1 — The `.slide.typ` marker.** A deck lives at `writings/<id>.slide.typ`. The filename
marks it: the build compiles it standalone to `artifacts/pdfs/<id>.pdf` and links it from
the site, but excludes it from the HTML and book passes (touying is paged-only and does
not survive HTML export).

**D2 — `meta` but no `body`.** Declare `#let meta = (title: …, date: …)` so the site can
list and link the deck. Never declare `#let body` — that would make it a bundle entry.

**D3 — Compile with `--root .`.** Always from the repo root:
`typst compile --root . writings/<id>.slide.typ artifacts/pdfs/<id>.pdf`, so absolute
paths like `/artifacts/data/...` resolve. Figures come from `artifacts/data/` — the same
committed run outputs the writeups use, never ad-hoc images.

**D4 — The skeleton.**

```typst
#import "@preview/touying:0.6.1": *
#import themes.simple: *

#let meta = (
  title: "…",
  date: "YYYY-MM-DD",
)

#show: simple-theme.with(aspect-ratio: "16-9")

#set text(font: "New Computer Modern", size: 22pt)
#show raw: set text(font: "DejaVu Sans Mono")

#title-slide[
  = Title
  #v(0.4em)
  Tagline.
]

== A content slide

- …
```

## 2. Sizing — budget the canvas in points

**D5 — The canvas is fixed: 842 × 474 pt (16:9).** A title header eats ~90 pt, footer
margin ~30 pt, leaving **~350 pt of usable height** on a titled slide. Budget layouts
against that number.

**D6 — Size images in absolute `pt`, never `%`.** Relative lengths resolve against the
enclosing region — inside grid cells that is rarely the slide, so percentage-sized images
come out unpredictably small *and* can overflow. `#image(..., height: 165pt)` does what
it says.

**D7 — Size each figure row to its aspect.** In multi-figure layouts, wide plots and tall
plots must not share one height — give each grid row its own: wide traces ~130 pt, taller
panels ~165 pt in a 2×2; a hero figure ~285 pt beside a stack of two ~135 pt. Sum rows +
gutters + captions and check it stays under ~350 pt.

**D8 — Fill or split.** If a slide is mostly whitespace, the figures are too small — grow
them to the budget or merge slides. If content doesn't fit at readable sizes, split the
slide; never shrink text below ~19 pt or captions below ~14 pt to force a fit.

## 3. Verify — overflow paginates silently

**D9 — Always check the page count after a layout change.** Oversized content does not
clip or error — touying silently spills it onto an extra page, and the deck grows without
warning. After every edit, compare pages against the intended slide count:

```sh
typst compile --root . --format png --ppi 36 writings/<id>.slide.typ "temp/check-{0p}.png"
ls temp/check-*.png | wc -l   # must equal the intended slide count
```

Do not trust Finder/Spotlight metadata (`mdls`) for the count — it caches stale values.

**D10 — Eyeball the risky slides.** Render the dense ones (figures, grids, math) at
`--ppi 96` and look: overflow, clipped captions, terms swallowed into subscripts. In
math, `$I_"ext"(t)$` puts the `(t)` in the subscript — write `$I_"ext" (t)$`.

## 4. Layout vocabulary

**D11 — One layout per slide, title + bullets and/or one visual.** The patterns, in the
order you'll reach for them (each is a `==` slide unless noted):

- **Bullets** — the workhorse. Bold the load-bearing phrase; two lines per bullet max;
  five bullets is the ceiling.
- **Two-column** — paired panels for comparisons (does/does-not, before/after). Keep the
  sides parallel: same count, same grammatical shape. A centered bold takeaway line below
  ties them together.
- **Code panel** — one fenced block in a `luma(245)` rounded box, one idea per snippet;
  trim imports and error handling.
- **Equation + terms** — the displayed equation, then `where:` and a bullet list defining
  *every* symbol.
- **Full-width figure** — one image, one gray caption. Let the plot do the talking.
- **Figure + bullets** — figure left (~55% width), ≤3 reading-notes right; the *so what*
  goes in the last bullet.
- **Figure pair** — two panels labelled (a)/(b), captions under each, comparison line
  below.
- **Figure grid (2×2)** — four panels max; beyond that it's a poster, not a slide. Per-row
  heights per D7.
- **Hero + stack** — the result you're arguing for large on the left, supporting evidence
  stacked right.
- **Table** — no grid lines: `stroke: none` with a single `table.hline` under the header.
  Numbers come from the run (`numbers.json`), never typed.
- **Big statement** — `#focus-slide[…]`, inverted, for the one line they must remember.
- **Closer** — big centered link, two or three parting bullets, tagline. Mirror the title
  slide so the deck bookends.

**D12 — A worked gallery beats a spec.** If the repo has a layout-gallery deck (this
repo's source ships one as `writings/ar005.slide.typ`), copy-paste from it rather than
re-deriving layouts; tag each slide with its layout name via a small gray
`place(top + right)` label only in gallery decks, not in real talks.

## 5. Serving

**D13 — Decks hot-reload like entries.** The dev server rebuilds the whole bundle (via
`build.py`, which re-globs the filesystem) on every source change, so a **new** `.slide.typ`
appears and an **edited** deck reloads without restarting `task dev` — same as an ordinary
entry. A deck that fails to compile shows the Typst error as a full-screen overlay in the
browser, not just in the terminal.
