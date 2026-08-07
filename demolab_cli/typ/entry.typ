// Standalone entry-PDF root used by `demolab build <id>`.
#import "/.demolab/lib.typ": *

#let entry-id = sys.inputs.entry
#let has-brand = sys.inputs.at("has-brand", default: "false") == "true"
#let config = if has-brand { yaml("/demolab.yaml") } else { (:) }
#let brand = default-brand + config
#import "/writings/" + entry-id + ".typ" as writing

#set document(title: writing.meta.title)
#numbered-pages(entry-page(writing.meta, writing.body, id: entry-id, brand: brand))
