// The demolab bundle root — the single source compiled to all three targets with
//   typst compile --format bundle --features bundle,html
//
// This file ships inside the demolab-cli package and is STAGED by build.py into the lab's
// .demolab/bundle/ before each compile (typst --root confines reads to the lab tree, so the
// compiled file must live under it). It holds no per-entry knowledge: build.py globs the
// filesystem (Typst can't list directories) and writes the discovered id/asset lists to
// .demolab/bundle/index.json; this file reads that manifest and does everything else —
// importing each writing, emitting every document, embedding every asset — in plain Typst.
// No generated source.
//
// Compiled with `--root` at the lab root, so `/writings/...`, `/.artifacts/...`,
// `/.demolab/bundle/...`, and the staged `/.demolab/...` all resolve. Run it by hand to debug:
//   uv run demolab build   # stages this file + .demolab/, writes the manifest + decks
// Use demolab build so the source checkout also receives its internal content/data paths.
#import "/.demolab/lib.typ": *

// The manifest build.py wrote: { entries: [{id, kind, source}], decks: [{id, source}],
// has_brand_config, has_landing }.
#let bundle-root = sys.inputs.at("demolab-bundle-root", default: "/.demolab/bundle")
#let manifest = json(bundle-root + "/index.json")

// The optional content-root demolab.yaml (build.py sets has_brand_config after checking it exists
// — Typst can't stat). Branding merges over engine defaults; collection label/order are
// read from it too. Absent ⇒ engine defaults + derivation-only collections.
#let config = if manifest.has_brand_config { yaml(content-root + "/demolab.yaml") } else { (:) }
#let brand = default-brand + config
#let annotations = config.at("annotations", default: none)
#let collection-order = config.at("collection-order", default: ())
#let collection-meta = config.at("collections", default: (:))
#let index-config = config.at("index", default: (:))
#let pdfs-enabled = manifest.at("pdfs_enabled", default: true)

// The optional custom landing page: a landing.typ at the content root (exporting `#let body`)
// replaces the homepage's collection directory with its own content. build.py sets has_landing
// (Typst can't stat). Absent unless the presentation author creates one.
#let landing = if manifest.at("has_landing", default: false) {
  import content-root + "/landing.typ": body
  body
} else { none }

// Import each *good* writing dynamically (import paths may be computed — no literal codegen).
// An entry contributes meta + body; a deck contributes only meta (touying is paged-only, so decks
// are compiled to standalone PDFs by build.py and embedded as assets below). An entry build.py
// flagged with an `error` (a missing figure, a Typst error) is NOT imported — it would fail the
// whole compile. build.py recovers its valid metadata independently, so it remains discoverable
// in listings while its own URL renders a diagnostic stub.
#let entries = manifest.entries.filter(e => "error" not in e).map(e => {
  import e.source: meta, body
  (id: e.id, kind: e.kind, meta: meta, body: body)
})
#let broken = manifest.entries.filter(e => "error" in e)
#let listing-entries = entries + broken.map(e => (
  id: e.id, kind: e.kind, meta: e.meta, broken: true,
))
#let decks = manifest.decks.map(d => {
  import d.source: meta
  (id: d.id, meta: meta)
})

// --- bundle assets ---
// Static files under assets/ are copied into the site at the same relative path.
#for path in manifest.at("assets", default: ()) {
  asset(path, read(content-root + "/assets/" + path, encoding: none))
}
// Run-backed videos receive collision-free public paths, never private filesystem URLs.
#for (source, url) in manifest.at("data_assets", default: (:)) {
  asset(url, read(source, encoding: none))
}
// User-owned attachments (for example videos selected by the article's own inputs).
// Merge first so shared attachments are emitted only once in a full-site bundle.
#let authored-assets = entries.fold((:), (files, entry) => {
  for (url, source) in entry.meta.at("assets", default: (:)) {
    assert(url not in files or files.at(url) == source, message: "conflicting authored asset: " + url)
    files.insert(url, source)
  }
  files
})
#for (url, source) in authored-assets { asset(url, read(source, encoding: none)) }
// deck PDFs, embedded at pdfs/<id>.pdf so the dev server serves them too
#for d in manifest.decks {
  asset("pdfs/" + d.id + ".pdf", read(bundle-root + "/decks/" + d.id + ".pdf", encoding: none))
}
// site favicon (a lab-notebook mark), linked from every page's <head> by lib.typ
#asset("favicon.svg", read("/.demolab/favicon.svg", encoding: none))
// hover popovers for inline citations (web-only), referenced by lib.typ's web-styles
#asset("cite-popover.js", read("/.demolab/cite-popover.js", encoding: none))
// fullscreen figure gallery (web-only), referenced by lib.typ's web-styles
#asset("image-lightbox.js", read("/.demolab/image-lightbox.js", encoding: none))

// --- documents (one compile emits them all into .demolab/site/) ---
// The homepage always exists; on a freshly-scaffolded repo (no entries) it shows a
// friendly empty state. Everything else is emitted only when there's content.
#let all-items = collect-items(listing-entries, decks, pdfs-enabled: pdfs-enabled)
#validate-collections(collection-meta)
#validate-tag-paths(all-items)
#document("index.html", title: [#brand.name])[#index-page(listing-entries, decks: decks, brand: brand, collection-order: collection-order, collection-meta: collection-meta, index-config: index-config, landing: landing, pdfs-enabled: pdfs-enabled, book-enabled: pdfs-enabled and entries.len() > 0, writings-dir: manifest.writings)]
#if all-items.len() > 0 {
  [#document("all.html", title: [#brand.name — all entries])[#all-page(listing-entries, decks: decks, brand: brand, collection-meta: collection-meta, pdfs-enabled: pdfs-enabled)]]
}
#if tag-slugs(all-items).len() > 0 {
  [#document("tags.html", title: [#brand.name — tags])[#tags-page(all-items, brand: brand)]]
  for tag in tag-slugs(all-items) {
    [#document("tags/" + tag + ".html", title: [#brand.name — #tag-label(tag)])[#tag-page(tag,
      all-items.filter(item => tag in item.tags), brand: brand, collection-meta: collection-meta)]]
  }
}
// Collection pages come from content plus explicit parent/child registration. This emits an empty
// parent (and empty registered children) without inventing writings or hierarchy from slugs.
#for c in collection-page-slugs(all-items, collection-meta) {
  [#document(c + ".html", title: [#brand.name — #collection-label(c, collection-meta)])[#collection-page(c, all-items.filter(x => x.coll == c), all-items: all-items, brand: brand, collection-meta: collection-meta)]]
}
#for e in entries {
  [#document(e.id + ".html", title: [#e.meta.title])[#entry-page(e.meta, e.body, id: e.id, kind: e.kind, brand: brand, annotations: annotations, collection-meta: collection-meta, pdfs-enabled: pdfs-enabled)]]
  if pdfs-enabled {
    [#document("pdfs/" + e.id + ".pdf", title: [#e.meta.title])[#numbered-pages(entry-page(e.meta, e.body, id: e.id, kind: e.kind, brand: brand, annotations: annotations, collection-meta: collection-meta))]]
  }
}
// Stub pages are web-only and excluded from the book; their recovered metadata keeps them listed.
#for e in broken {
  [#document(e.id + ".html", title: [#e.meta.title])[#broken-entry-page(e.id, e.error, title: e.meta.title, brand: brand)]]
}
#if pdfs-enabled and entries.len() > 0 {
  [#document("pdfs/book.pdf", title: [#brand.book-title])[#numbered-pages(book-page(entries, brand: brand))]]
}
