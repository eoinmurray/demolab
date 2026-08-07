#let meta = (
  title: "Discussing a writeup inline",
  date: "2026-08-07",
  description: "Optional Hypothesis annotations let collaborators highlight a passage in a web article or experiment and discuss it in a private, threaded margin conversation.",
  collection: "documentation",
  status: "final",
  order: 17,
  annotations: "hypothesis",
)

#let hypothesis = "https://web.hypothes.is"

#let body = [
  A published result often needs a conversation before it needs another revision. Hypothesis adds
  that conversation directly to a demolab web page: select a passage, attach a comment, and reply
  in a shared thread. The annotation stays outside the scientific record, while the experiment,
  figures, and PDF remain reproducible and unchanged.

  This page is itself an example. Its `meta` block contains `annotations: "hypothesis"`, so the
  Hypothesis control appears at the right edge of the web edition. Select this sentence and attach
  a private note to test the complete path.

  == Set up a private reading group

  + Create free Hypothesis accounts for each collaborator.
  + #link(hypothesis + "/help/how-to-create-a-private-group/")[Create a private group], then send
    its invitation link to the people who should read and reply.
  + Open an annotated demolab page, sign in through the sidebar, and select that private group
    before posting. The public layer is a different destination; check the group name on every
    new top-level comment when the discussion must remain private.

  Replies form a thread beneath the selected passage. Hypothesis also supports page notes for
  comments about the whole experiment and LaTeX between double dollar signs for mathematical
  discussion.

  == Enable annotations

  To annotate every article and experiment, add one field to the root `demolab.yaml`:

  ```yaml
  annotations: hypothesis
  ```

  To enable only selected entries, omit the root field and add the provider to a writing's
  metadata instead:

  ```typ
  #let meta = (
    title: "A result to review",
    date: "2026-08-07",
    annotations: "hypothesis",
  )
  ```

  Entry metadata wins over the lab setting. Set `annotations: none` on one entry to keep it
  unannotated when the rest of the lab has Hypothesis enabled.

  == What gets published

  The setting adds the hosted Hypothesis client to web entry pages only. It does not add scripts
  to the homepage, collection listings, standalone PDFs, or the combined book. Comments and group
  membership live in Hypothesis rather than the git repository, so rebuilding the site does not
  publish a private discussion or alter a recorded result.

  An annotation targets the page URL and records several descriptions of the selected text. Small
  layout changes and unrelated edits usually leave it attached. Moving the page to another URL,
  deleting the selected passage, or substantially rewriting its context can orphan it. Keep entry
  IDs stable and resolve important review comments before replacing the prose they target.

  == Operational boundary

  This option loads JavaScript from `hypothes.is` and sends annotation content to the Hypothesis
  service. That is an intentional external dependency, not part of demolab's committed research
  record. Do not enable it for material whose hosting or data policy forbids that service. Review
  #link(hypothesis + "/privacy/")[Hypothesis privacy information] with your collaborators before
  using it for sensitive or unpublished work.
]
