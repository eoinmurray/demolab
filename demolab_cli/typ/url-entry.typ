// One request, one article. No discovery, preview state, or publication writes.
#import "/.demolab/lib.typ": *
#let root = sys.inputs.at("demolab-url-root")
#let request = json(root + "/index.json")
#let config = if request.has_config { yaml(content-root + "/demolab.yaml") } else { (:) }
#let brand = default-brand + config
#let pdfs = config.at("pdfs", default: true)
#import request.source: meta, body

#for path in request.assets {
  asset(path, read(content-root + "/assets/" + path, encoding: none))
}
#for (source, url) in request.media { asset(url, read(source, encoding: none)) }
#for (url, source) in meta.at("assets", default: (:)) { asset(url, read(source, encoding: none)) }
#asset("favicon.svg", read("/.demolab/favicon.svg", encoding: none))
#asset("cite-popover.js", read("/.demolab/cite-popover.js", encoding: none))
#let page() = entry-page(meta, body, id: request.id, brand: brand,
  collection-meta: config.at("collections", default: (:)),
  annotations: config.at("annotations", default: none), pdfs-enabled: pdfs)
#document(request.id + ".html", title: [#meta.title])[#page()]
#if pdfs { document("pdfs/" + request.id + ".pdf", title: [#meta.title])[#numbered-pages(page())] }
