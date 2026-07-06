// ar005: the layout-gallery deck — one slide per layout in SLIDES.md (D11), each tagged with
// its layout name (D12). Copy-paste from here rather than re-deriving a layout. It's a *deck*
// (`.slide.typ`), so it declares `#let meta` but no `#let body`: compiled standalone to a PDF
// and linked from the homepage, excluded from the HTML/book passes. Compile with `--root .`
// so /artifacts/... resolves (D3).
#import "@preview/touying:0.6.1": *
#import themes.simple: *

#let meta = (
  title: "Slide layout gallery",
  date: "2026-07-06",
)

#show: simple-theme.with(aspect-ratio: "16-9")

#set text(font: "New Computer Modern", size: 22pt)
#show raw: set text(font: "DejaVu Sans Mono")

// Real run data for the table + figure slides — read from the record, never typed (D11 table).
#let run = json("/artifacts/data/exp000/numbers.json")

// Gallery-only tag naming each layout (D12 says: only in gallery decks, never real talks).
#let layout-name(name) = place(top + right, text(size: 13pt, fill: luma(150))[#name])
#let cap(body) = text(size: 14pt, fill: gray)[#body]

// ── Title (mirror the closer so the deck bookends) ─────────────────────────
#title-slide[
  = Slide layout gallery
  #v(0.4em)
  A worked example of every demolab slide layout.
  #v(1.4em)
  #text(size: 17pt, fill: gray)[Demolab · SLIDES.md D11]
]

// ── Bullets — the workhorse ────────────────────────────────────────────────
== Bullets
#layout-name[Bullets]

- *Bold the load-bearing phrase* so the eye lands on it first.
- Two lines per bullet, maximum — past that it's prose, not a slide.
- Five bullets is the ceiling; split the slide before a sixth.
- Nested points are fine *once*, for a short aside.
- The last bullet is the *so what* — say what it means.

// ── Two-column — comparisons ───────────────────────────────────────────────
== Two-column
#layout-name[Two-column]

#grid(columns: (1fr, 1fr), gutter: 28pt,
  [
    *What a tool does*
    - Holds reusable computation.
    - Writes `numbers.json` + data.
    - Stays language-agnostic.
  ],
  [
    *What a tool does not*
    - Render plots.
    - Import a runner.
    - Hard-code a result.
  ],
)
#v(1em)
#align(center)[*Parallel sides, one takeaway: tools compute, runners narrate.*]

// ── Code panel — one idea per snippet ──────────────────────────────────────
== Code panel
#layout-name[Code panel]

#v(1fr)
#align(center)[
  #block(fill: luma(245), stroke: 0.75pt + luma(210), radius: 12pt, inset: 24pt)[
    #set align(left)
    #text(size: 20pt)[
      ```python
      def cmd_lif(args):
          v, spikes = simulate(args.current, args.tau_m)
          write_output(run_dir,
              {"firing_rate_hz": rate(spikes)},
              manifest={"headline_metrics": ["firing_rate_hz"]})
      ```
    ]
  ]
]
#v(1fr)

// ── Equation + terms — define every symbol ─────────────────────────────────
== Equation + terms
#layout-name[Equation + terms]

$ tau_m (dif V) / (dif t) = -(V - V_"rest") + R_m thin I_"ext" (t) $

#v(0.6em)
where:
- $V$ — membrane potential (mV)
- $tau_m$ — membrane time constant (ms)
- $V_"rest"$ — resting potential (mV)
- $R_m$ — membrane resistance (MΩ)
- $I_"ext" (t)$ — external input current (nA); the space keeps $(t)$ out of the subscript (D10)

// ── Full-width figure — let the plot talk ──────────────────────────────────
== Full-width figure
#layout-name[Full-width figure]

#v(0.5em)
#align(center)[
  #image("/artifacts/data/exp000/lif.svg", height: 250pt)
  #cap[Membrane potential of a single LIF neuron under tonic input; it charges and resets at threshold, firing at #run.lif.firing_rate_hz Hz.]
]

// ── Figure + bullets — figure left, reading notes right ────────────────────
== Figure + bullets
#layout-name[Figure + bullets]

#grid(columns: (55%, 1fr), gutter: 22pt, align: horizon,
  image("/artifacts/data/exp000/lif.svg", height: 200pt),
  [
    - Each sweep is the membrane charging through its RC constant.
    - Every vertical drop is a *reset* after a spike.
    - *So what:* constant drive gives a fixed rate, #run.lif.firing_rate_hz Hz.
  ],
)

// ── Figure pair — (a)/(b) with a comparison line ───────────────────────────
== Figure pair
#layout-name[Figure pair]

#grid(columns: (1fr, 1fr), gutter: 20pt,
  [
    #align(center)[
      #image("/artifacts/data/exp000/lif.svg", height: 160pt)
      #cap[(a) LIF: linear integrate-and-fire.]
    ]
  ],
  [
    #align(center)[
      #image("/artifacts/data/exp001/eif.svg", height: 160pt)
      #cap[(b) EIF: exponential spike onset.]
    ]
  ],
)
#align(center)[*Same drive, sharper threshold: the EIF spike initiates faster.*]

// ── Figure grid (2×2) — four panels, per-row heights (D7) ──────────────────
== Figure grid (2×2)
#layout-name[Figure grid]

#grid(columns: (1fr, 1fr), rows: (auto, auto), column-gutter: 18pt, row-gutter: 10pt, align: center,
  image("/artifacts/data/exp000/lif.svg", height: 120pt),
  image("/artifacts/data/exp001/eif.svg", height: 120pt),
  image("/artifacts/data/exp000/net.png", height: 150pt),
  image("/artifacts/data/exp001/enet.png", height: 150pt),
)

// ── Hero + stack — the result large, evidence beside it ────────────────────
== Hero + stack
#layout-name[Hero + stack]

#grid(columns: (60%, 1fr), gutter: 20pt, align: horizon,
  [
    #align(center)[
      #image("/artifacts/data/exp000/net.png", height: 255pt)
      #cap[The network sustains irregular firing — the result being argued.]
    ]
  ],
  [
    #stack(spacing: 12pt,
      image("/artifacts/data/exp000/lif.svg", height: 105pt),
      image("/artifacts/data/exp001/eif.svg", height: 105pt),
    )
    #cap[Single-cell traces as supporting evidence.]
  ],
)

// ── Table — no grid lines, numbers from the run ────────────────────────────
== Table
#layout-name[Table]

#v(0.6em)
#align(center)[
  #table(
    columns: (auto, auto), stroke: none, align: (left, right), inset: 8pt,
    table.header([*Parameter*], [*Value*]),
    table.hline(),
    [Input current], [#run.lif.config.current nA],
    [Membrane time constant $tau_m$], [#run.lif.config.tau_m ms],
    [Threshold $V_"th"$], [#run.lif.config.v_thresh mV],
    [Firing rate], [#run.lif.firing_rate_hz Hz],
  )
]
#v(0.4em)
#align(center)[#cap[Every value read from `numbers.json`, so the slide can't drift from the run.]]

// ── Big statement — the one line to remember ───────────────────────────────
#focus-slide[
  One layout per slide.
  #v(0.3em)
  Title, plus bullets *or* one visual.
]

// ── Closer — mirror the title slide ────────────────────────────────────────
== Closer
#layout-name[Closer]

#v(1fr)
#align(center)[
  #text(size: 28pt)[*demolab-engine/guides/SLIDES.md*]
  #v(0.8em)
  - Copy a layout from this gallery; don't re-derive it.
  - Check the page count after every edit (D9) — overflow paginates silently.
  - Numbers and figures come from the run, never the keyboard.
  #v(1em)
  #text(size: 17pt, fill: gray)[Thirteen slides, thirteen layouts.]
]
#v(1fr)
