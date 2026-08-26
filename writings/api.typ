#import "/.demolab/lib.typ": *

#let meta = (
  title: "Reading a JSON asset",
  created_at: "2026-08-26",
  description: "A small API-style page using the developer documentation theme.",
  collection: "pinglab-docs",
  order: 1,
)

#let body = [
  Use Typst's `json` function to read structured data stored under `assets/`.

  == Example

  ```typ
  #let data = json("/assets/example.json")
  The value is #data.value.
  ```

  == Input

  - *Path:* a root-relative path under `assets/`
  - *Returns:* the decoded JSON value
  - *Example value:* `42`

  The asset is bundled into the generated static site alongside the rendered page.
]
