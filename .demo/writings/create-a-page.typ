#import "/.demolab/lib.typ": *

#let meta = (
  title: "Create a page",
  created_at: "2026-09-03",
  description: "The smallest useful guide to adding a writing.",
  collection: "guides",
  order: 1,
  tags: ("authoring",),
)

#let body = [
  Add a `.typ` file under `writings/` and export `meta` and `body`.

  ```typ
  #let meta = (
    title: "My page",
    created_at: "2026-09-03",
    collection: "notes",
  )

  #let body = [Write the page here.]
  ```

  The filename becomes the page ID and URL.
]
