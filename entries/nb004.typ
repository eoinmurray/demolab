// nb004 — the document half of a Typst notebook.
// Reads the same committed bundle the web entries use (artifacts/nb004/), so the
// numbers below come straight from the run and cannot drift.
// Compiled with `--root` set to the repo root, so /artifacts/... resolves.

#set page(width: 16cm, height: auto, margin: 1.6cm)
#set text(font: "New Computer Modern", size: 11pt)
#set par(justify: true)

#let d = json("/artifacts/nb004/numbers.json").lif

= An LIF neuron, published to PDF with Typst

This is the *same* simulation as entry nb000 — a leaky integrate-and-fire neuron
under tonic current — but published as a PDF through Typst instead of the web.
The tool, the runner, and the committed bundle are identical; only the document
format and the build command change. That is the point: publishing is a
pluggable layer on top of the tool → artifacts contract.

The subthreshold dynamics are

$ tau_m (dif V) / (dif t) = -(V - V_"rest") + R_m I, $

with a spike-and-reset rule: when $V >= V_"th"$, record a spike and set
$V <- V_"reset"$.

#figure(
  image("/artifacts/nb004/lif.png", width: 100%),
  caption: [LIF membrane potential under a tonic input current.],
)

Every value in the table is read directly from `numbers.json` via Typst's native
`json()`, so the prose and the run can never disagree.

#table(
  columns: (auto, auto),
  align: (left, right),
  table.header([*Parameter*], [*Value*]),
  [Input current (nA)], [#d.config.current],
  [Duration (ms)], [#d.config.duration],
  [Timestep (ms)], [#d.config.dt],
  [Firing rate (Hz)], [#d.firing_rate_hz],
)
