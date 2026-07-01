"""nb004 — a Typst publisher.

Same tool + committed bundle as the web entries, but the document is Typst and
the output is a PDF. Staging is shared (helpers.stage); only the publish step
(typst compile) differs.
"""

import typst

from helpers import ROOT, stage

if __name__ == "__main__":
    stage("nb004", [("neuron", "lif")])
    doc = ROOT / "entries" / "nb004.typ"
    pdf = ROOT / "temp" / "nb004.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    typst.compile(str(doc), output=str(pdf), root=str(ROOT))
    print(f"wrote {pdf}")
