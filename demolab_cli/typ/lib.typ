// Shared publishing helpers for the demolab Typst bundle.
// Imported (root-relative) by main.typ and by each writings/<id>.typ.
// The bundle emits three targets from one compile: web HTML, per-entry PDFs, and a book.

// --- brand defaults: overridden by the optional root demolab.yaml (see main.typ) ---
// The engine never hard-codes the site name; the resolved `brand` is threaded in from
// main.typ (which merges demolab.yaml over these defaults). Page functions default to
// these so they still render if called without a brand.
#let default-brand = (
  name: "Demolab",
  book-title: "Demolab — the book",
  contents-title: "Demolab — contents",
  description: none, // one-line site tagline shown under the homepage title (set in demolab.yaml)
  author: none,      // the lab's owner — shown as a byline on the homepage + <meta name="author">
  contact: none,     // optional email/url; if set, the byline links to it (mailto for an @, else href)
  links: (),         // optional homepage header links: ((label: "Docs", url: "docs.html"),)
)

#let homepage-links(brand) = {
  let links = brand.at("links", default: ())
  assert(type(links) == array, message: "demolab.yaml 'links' must be a list")
  for item in links {
    assert(type(item) == dictionary,
      message: "each demolab.yaml 'links' item must contain label and url")
    assert(type(item.at("label", default: none)) == str,
      message: "each demolab.yaml 'links' item needs a string label")
    assert(type(item.at("url", default: none)) == str,
      message: "each demolab.yaml 'links' item needs a string url")
  }
  links
}

// Internal compiler inputs keep source-demo content separate from generated runtime.
// Defaults preserve ordinary labs and direct Typst invocation.
#let content-root = sys.inputs.at("demolab-content-root", default: "")
#let preview-sources = if "demolab-preview-file" in sys.inputs {
  json(sys.inputs.at("demolab-preview-file"))
} else { (:) }
#let data-inputs = if "demolab-data-inputs" in sys.inputs {
  json(sys.inputs.at("demolab-data-inputs"))
} else { (:) }
#let build-sources = if "demolab-preview-file" in sys.inputs { (:) } else {
  data-inputs.at("sources", default: (:))
}
#let data-file(rel, sources: (:), article: none) = {
  // Optional authored key-to-directory mapping, relative to the data root.
  let key = rel.split("/").first()
  let selected = if article != none {
    preview-sources.at(article, default: build-sources.at(article, default: (:)))
  } else { (:) }
  if article != none and article in build-sources {
    assert(key in selected, message: "build inputs for " + article + " have no selection for data key '" + key + "'")
  }
  if key in selected {
    assert(rel.split("/").len() > 1
      and rel.split("/").all(part => part not in ("", ".", ".."))
      and not rel.contains("\\"), message: "selected data-file requires a safe key/filename")
    let directory = selected.at(key)
    // None is an explicit Latest input with no available runs, never a fallback.
    let path = if directory == none { none } else { directory + rel.slice(key.len()) }
    if path != none and article != none and article in build-sources {
      assert(path in data-inputs.files, message: "missing selected data file: " + path)
    }
    return path
  }
  let resolved = if key in sources {
    let source = sources.at(key)
    assert(type(source) == str and not source.starts-with("/")
      and source.split("/").all(part => part not in ("", ".", "..")),
      message: "data-file source for '" + key + "' must be a safe relative directory")
    source + rel.slice(key.len())
  } else { rel }
  sys.inputs.at("demolab-data-root", default: "/.artifacts") + "/" + resolved
}

// Opt-in empty-data readers. Native json/image stay strict and unchanged. Only the
// explicit no-run sentinel is tolerated; absent/corrupt files in real runs still fail.
#let data-json(path) = if path != none { json(path) }

// --- authored dates: validate and render creation/update metadata ---
// Demolab only renders dates supplied by the author. `date` remains a deprecated fallback for
// old writings; it is never combined with Git, filesystem, build, or deployment timestamps.
#let authored-date(value, field) = {
  let message = ("meta." + field + " must be an ISO calendar date (YYYY-MM-DD)"
    + " or datetime (YYYY-MM-DDTHH:MM[:SS[.fraction]] with Z or +/-HH:MM timezone)")
  assert(type(value) == str, message: message)
  assert(value.match(regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}(T.*)?$")) != none,
    message: message)
  let p = value.slice(0, 10).split("-").map(int)
  let hour = 0
  let minute = 0
  let second = 0
  let fraction = ""
  let offset = 0
  let clock = none
  let zone = none
  if value.len() > 10 {
    let time = value.slice(11).match(regex(
      "^([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\\.([0-9]+))?)?(Z|[+-][0-9]{2}:[0-9]{2})$",
    ))
    assert(time != none, message: message)
    let c = time.captures
    hour = int(c.at(0))
    minute = int(c.at(1))
    second = if c.at(2) == none { 0 } else { int(c.at(2)) }
    fraction = if c.at(3) == none { "" } else { c.at(3).trim("0", at: end) }
    zone = c.at(4)
    clock = value.slice(11, value.len() - zone.len())
    if zone != "Z" {
      let h = int(zone.slice(1, 3))
      let m = int(zone.slice(4, 6))
      assert(h <= 23 and m <= 59, message: "meta." + field + " has an invalid timezone offset")
      offset = (h * 3600 + m * 60) * if zone.starts-with("-") { -1 } else { 1 }
    }
  }
  // Typst validates calendar and clock components; offsets never use the machine timezone.
  let local = datetime(year: p.at(0), month: p.at(1), day: p.at(2),
    hour: hour, minute: minute, second: second)
  let epoch = datetime(year: 1970, month: 1, day: 1, hour: 0, minute: 0, second: 0)
  // Keep fractional digits separate so arbitrary authored precision sorts without float rounding.
  (key: (int((local - epoch).seconds()) - offset, fraction),
    date: local.display("[day padding:none] [month repr:long] [year]"),
    short-date: local.display("[day padding:none] [month repr:short] ") + value.slice(2, 4),
    clock: clock, zone: zone)
}

#let iso-date(value, field) = {
  let _validated = authored-date(value, field)
  value
}

#let entry-dates(meta) = {
  let created-value = meta.at("created_at", default: meta.at("date", default: none))
  assert(created-value != none,
    message: "meta.created_at is required (deprecated meta.date is accepted for compatibility)")
  let created = iso-date(created-value,
    if "created_at" in meta { "created_at" } else { "date" })
  let updated = if "updated_at" in meta { iso-date(meta.updated_at, "updated_at") } else { none }
  assert(updated == none or authored-date(updated, "updated_at").key >= authored-date(created, "created_at").key,
    message: "meta.updated_at must not be earlier than meta.created_at")
  (created: created, updated: updated)
}

#let human-date(iso, compact: false) = {
  let parsed = authored-date(iso, "date")
  let date = if compact { parsed.short-date } else { parsed.date }
  if parsed.clock == none { return date }
  let parts = parsed.clock.split(":")
  let hour = int(parts.at(0))
  let hour12 = calc.rem(hour, 12)
  let clock = str(if hour12 == 0 { 12 } else { hour12 }) + ":" + parts.at(1)
  let period = if hour < 12 { " am" } else { " pm" }
  date + (if compact { ", " } else { " at " }) + clock + period
}

#let date-line(meta) = {
  let dates = entry-dates(meta)
  context {
    if target() == "html" {
      [Created ]
      html.elem("time", attrs: (datetime: dates.created), human-date(dates.created))
      if dates.updated != none {
        [ · Updated ]
        html.elem("time", attrs: (datetime: dates.updated), human-date(dates.updated))
      }
    } else {
      [Created #human-date(dates.created)]
      if dates.updated != none {
        [ · Updated #human-date(dates.updated)]
      }
    }
  }
}

// PDF list rows omit the inferable "Created" label while retaining an explicit label for
// updates, whose meaning is otherwise ambiguous beside the authored date.
#let row-date-line(meta) = {
  let dates = entry-dates(meta)
  context {
    if target() == "html" {
      html.elem("time", attrs: (datetime: dates.created), human-date(dates.created))
      if dates.updated != none {
        [ · Updated ]
        html.elem("time", attrs: (datetime: dates.updated), human-date(dates.updated))
      }
    } else {
      [#human-date(dates.created)]
      if dates.updated != none [ · Updated #human-date(dates.updated)]
    }
  }
}

// Browsing needs one recency date; article headers retain the complete authored history.
#let listing-date-line(meta) = context {
  let dates = entry-dates(meta)
  let updated = dates.updated != none
  let value = if updated { dates.updated } else { dates.created }
  let label = if updated { "Updated " } else { "Created " }
  if target() == "html" {
    html.elem("time", attrs: (datetime: value, title: label + human-date(value)),
      human-date(value, compact: true))
  } else {
    [#label#human-date(value, compact: true)]
  }
}

// --- web-styles: inject the stylesheet + head meta into HTML pages (ignored in the PDF pass) ---
#let web-styles(brand: default-brand, annotations: none, root-prefix: "") = context {
  if target() == "html" {
    html.elem("link", attrs: (rel: "icon", type: "image/svg+xml", href: root-prefix + "favicon.svg"))
    html.elem("style", read("/.demolab/style.css"))
    // provenance: which engine built this page (invisible, machine-readable)
    html.elem("meta", attrs: (name: "generator", content: "demolab " + read("/.demolab/VERSION").trim()))
    if brand.at("author", default: none) != none {
      html.elem("meta", attrs: (name: "author", content: brand.author))
    }
    // hover popovers for inline citations (no-op on pages without cites)
    html.elem("script", attrs: (src: root-prefix + "cite-popover.js", defer: ""))[]
    // fullscreen, keyboard- and swipe-navigable gallery for unlinked figure images
    html.elem("script", attrs: (src: root-prefix + "image-lightbox.js", defer: ""))[]
    // Optional collaborative web annotations. The hosted Hypothesis client owns accounts,
    // private groups, storage, anchoring, and threads; demolab only opts this page into it.
    if annotations == "hypothesis" {
      html.elem("script", attrs: (src: "https://hypothes.is/embed.js", async: ""))[]
    }
  }
}

// --- pending: a placeholder for a figure whose asset isn't ready yet (a re-run in flight, data
// withheld). Drops into a #figure in place of the image, so the figure still numbers and captions
// normally, and reserves the figure's footprint (default 16:9, H12) so the page doesn't reflow when
// the real plot lands. A tinted dashed panel with a small framed-image mark over the muted reason.
// `pending-figure(...)` is the one-call convenience that guarantees continuous "Figure N" numbering.
#let pending(body, ratio: 16 / 9) = context {
  if target() == "html" {
    html.elem(
      "div",
      attrs: (class: "fig-pending", style: "aspect-ratio:" + str(ratio)),
      {
        html.elem("span", attrs: (class: "fig-pending-mark"))[]
        html.elem("span", attrs: (class: "fig-pending-note"), body)
      },
    )
  } else {
    layout(size => block(
      width: 100%,
      height: size.width / ratio,
      fill: luma(249),
      radius: 5pt,
      stroke: (thickness: 0.75pt, paint: luma(203), dash: "dashed"),
      inset: 1.1em,
      align(center + horizon, grid(
        rows: (auto, auto),
        row-gutter: 0.7em,
        align: center,
        box(width: 1.7em, height: 1.2em, radius: 1.5pt, stroke: 0.7pt + luma(178)),
        text(size: 9pt, fill: luma(140), style: "italic", body),
      )),
    ))
  }
}

// A whole pending figure in one call: numbers as a "Figure N" (kind: image) alongside real figures.
#let pending-figure(caption: none, note: [figure pending], ratio: 16 / 9) = figure(
  pending(note, ratio: ratio),
  caption: caption,
  kind: image,
  supplement: [Figure],
)

// Accept data-file's no-run sentinel without swallowing real image errors.
#let data-image(path, ..args) = if path == none {
  pending([Image pending · no runs available])
} else { image(path, ..args) }

// --- video: plays in HTML, omitted from PDF (a note points to the web edition) ---
// Files under assets/ are emitted by build.py and referenced here by relative path.
#let video(src, caption: none) = context {
  let media = data-inputs.at("media", default: (:))
  if type(src) == str and data-inputs.at("directories", default: ()).any(dir => src.starts-with(dir + "/")) {
    assert(src in media, message: "missing or unsupported run-backed video: " + src)
  }
  let url = if type(src) == str { media.at(src, default: src) } else { src }
  if src == none {
    pending([Video pending · no runs available])
    if caption != none { text(size: 9pt, fill: gray)[#caption] }
  } else if target() == "html" {
    html.elem("video", attrs: (src: url, controls: "", style: "max-width:100%;width:640px"))[]
    if caption != none { text(size: 9pt, fill: gray)[#caption] }
  } else {
    text(
      size: 9pt,
      style: "italic",
      fill: gray,
    )[[ Video#if caption != none [ — #caption] · view the web edition to play. ]]
  }
}

// --- citations: inline numbered cites + a DOI reference list ---
// Author-managed numbering (you pass the numbers), so it's dependency-free and works the same
// in the bundle's HTML and PDF. `#cite(1, 2)` renders "[1, 2]" (links to the refs on the web);
// `#reference-list((( text: "...", doi: "..." ), …))` renders the numbered References section,
// each entry linking out to https://doi.org/<doi>. On the web the inline cites jump to the entry.
#let cite(..ns) = {
  let nums = ns.pos()
  context {
    if target() == "html" {
      html.elem("span", attrs: (class: "cite"), {
        [\[]
        nums.map(n => html.elem("a", attrs: (href: "#ref-" + str(n)), str(n))).join(", ")
        [\]]
      })
    } else [#h(0.15em, weak: true)#text(weight: 600)[\[#nums.map(n => str(n)).join(", ")\]]]
  }
}

#let reference-list(items) = {
  heading(level: 2, "References")
  context {
    if target() == "html" {
      html.elem("ol", attrs: (class: "refs"), {
        for (i, r) in items.enumerate() {
          html.elem("li", attrs: (id: "ref-" + str(i + 1)), {
            r.text
            if r.at("doi", default: none) != none {
              [ ]
              html.elem("a", attrs: (class: "doi", href: "https://doi.org/" + r.doi, target: "_blank", rel: "noopener"), "doi:" + r.doi)
            }
          })
        }
      })
    } else {
      enum(..items.map(r => [
        #r.text#if r.at("doi", default: none) != none [ #link("https://doi.org/" + r.doi)[doi:#r.doi]]
      ]))
    }
  }
}

// --- collections: entries are grouped on the homepage by their meta.collection ---
// A slug title-cases by default; an optional `collections` map + `collection-order` list
// in demolab.yaml (threaded in from main.typ) override the label / description / order.
#let title-case(slug) = slug.split("-").map(w => if w.len() > 0 { upper(w.slice(0, 1)) + w.slice(1) } else { w }).join(" ")
#let collection-label(slug, meta) = meta.at(slug, default: (:)).at("label", default: title-case(slug))
#let collection-description(slug, meta) = meta.at(slug, default: (:)).at("description", default: none)
#let collection-children(slug, meta) = meta.at(slug, default: (:)).at("children", default: ())
#let collection-parents(slug, meta) = meta.keys().filter(parent => slug in collection-children(parent, meta))
#let collection-parent(slug, meta) = {
  let parents = collection-parents(slug, meta)
  if parents.len() == 0 { none } else { parents.first() }
}
#let collection-theme(slug, meta) = {
  let own = meta.at(slug, default: (:)).at("theme", default: none)
  let parent = collection-parent(slug, meta)
  if own != none { own } else if parent != none { collection-theme(parent, meta) } else { none }
}
#let collection-homepage-visible(slug, meta) = {
  let visible = meta.at(slug, default: (:)).at("homepage", default: true)
  assert(type(visible) == bool,
    message: "demolab.yaml collection '" + slug + "' homepage must be true or false")
  let parent = collection-parent(slug, meta)
  visible and (parent == none or collection-homepage-visible(parent, meta))
}
#let collection-root(slug, meta) = {
  let parent = collection-parent(slug, meta)
  if parent == none { slug } else { collection-root(parent, meta) }
}
#let collection-page-slugs(items, meta) = {
  let content = items.map(it => it.coll)
  let nested = meta.keys().filter(slug => collection-children(slug, meta).len() > 0 or collection-parent(slug, meta) != none)
  (content + nested).dedup()
}
#let validate-collection-path(slug, meta, trail: ()) = {
  assert(slug not in trail,
    message: "demolab.yaml collection cycle: " + (trail + (slug,)).join(" -> "))
  let parent = collection-parent(slug, meta)
  if parent != none { validate-collection-path(parent, meta, trail: trail + (slug,)) }
}
#let validate-collections(meta) = {
  assert(type(meta) == dictionary, message: "demolab.yaml 'collections' must be a mapping")
  for (slug, spec) in meta {
    assert(type(spec) == dictionary,
      message: "demolab.yaml collection '" + slug + "' must be a mapping")
    let children = spec.at("children", default: ())
    assert(type(children) == array,
      message: "demolab.yaml collection '" + slug + "' children must be a list")
    for child in children {
      assert(type(child) == str,
        message: "demolab.yaml collection '" + slug + "' children must be collection slugs")
      assert(child in meta,
        message: "demolab.yaml collection '" + slug + "' has unknown child '" + child + "'")
    }
  }
  for slug in meta.keys() {
    let parents = collection-parents(slug, meta)
    assert(parents.len() <= 1,
      message: "demolab.yaml collection '" + slug + "' has duplicate parentage: " + parents.join(", "))
    let _path = validate-collection-path(slug, meta)
    let _visible = collection-homepage-visible(slug, meta)
  }
}
#let theme-class(theme, base: none) = {
  let classes = if base == none { () } else { (base,) }
  (classes + if theme == none { () } else { ("theme-" + str(theme),) }).join(" ")
}
#let collection-rank(slug, order) = {
  let i = order.position(s => s == slug)
  if i == none { order.len() } else { i }
}

// --- status-badge: an experiment's artifact-stage marker, as plain text ---
// Set `status:` to the canonical artifact noun: ExpScoutPlan, ExpScout, ExpStudyPlan, or
// ExpStudy. It is optional and every supplied stage is shown.
#let status-badge(status) = {
  if status != none {
    context {
      if target() == "html" { html.elem("span", attrs: (class: "status"), status) } else { text(status) }
    }
  }
}

// Artifact lifecycle order for sorting. Untyped and unknown values follow typed experiments.
#let status-rank(s) = {
  let i = ("ExpScoutPlan", "ExpScout", "ExpStudyPlan", "ExpStudy").position(x => x == s)
  if i == none { 4 } else { i }
}

// --- tags: optional many-to-many discovery metadata ---
// Tags are stable lowercase slugs; hyphens and dots may separate components. They never determine collection membership, lifecycle
// status, or ordering; generated pages simply gather items that explicitly name a tag.
#let entry-tags(meta, id: none) = {
  let tags = meta.at("tags", default: ())
  let owner = if id == none { "entry" } else { "entry '" + id + "'" }
  assert(type(tags) == array, message: owner + " meta.tags must be a list")
  for tag in tags {
    assert(type(tag) == str and tag.match(regex("^[a-z0-9]+([.-][a-z0-9]+)*$")) != none,
      message: owner + " meta.tags values must be lowercase slugs such as 'information-theory' or 'v35.0.0'")
  }
  assert(tags.sorted().dedup().len() == tags.len(), message: owner + " meta.tags must not contain duplicates")
  tags
}
#let tag-label(tag) = title-case(tag)
#let tag-link(tag, root-prefix: "") = context {
  if target() == "html" {
    html.elem("a", attrs: (class: "tag", href: root-prefix + "tags/" + tag), tag)
  } else { text(tag) }
}
#let tag-list(tags, root-prefix: "") = {
  for (i, tag) in tags.enumerate() {
    if i > 0 { [ ] }
    tag-link(tag, root-prefix: root-prefix)
  }
}
#let tag-slugs(items) = items.fold((), (tags, item) => tags + item.tags).sorted().dedup()
#let validate-tag-paths(items) = {
  if tag-slugs(items).len() > 0 {
    assert(not items.any(item => item.id == "tags"),
      message: "writing ID 'tags' is reserved when meta.tags are used")
  }
}

// Flatten entries + decks into one uniform list of link rows. Decks (paged-only) link to
// their PDF and fall into the `slides` collection unless their meta says otherwise;
// entries link to their HTML page.
#let collect-items(entries, decks, pdfs-enabled: true) = {
  entries.map(e => (
    id: e.id,
    kind: e.kind,
    title: e.meta.title,
    meta: e.meta,
    status: e.meta.at("status", default: none),
    tags: entry-tags(e.meta, id: e.id),
    coll: e.meta.at("collection", default: "uncategorized"),
    order: e.meta.at("order", default: none), // optional curated rank within the collection
    href: e.id,
    pdf: if pdfs-enabled and not e.at("broken", default: false) { "pdfs/" + e.id + ".pdf" } else { none },
    deck: false,
    broken: e.at("broken", default: false),
    has-date: "created_at" in e.meta or "date" in e.meta,
  )) + decks.map(d => (
    id: d.id,
    kind: "deck",
    title: d.meta.title,
    meta: d.meta,
    status: d.meta.at("status", default: none),
    tags: entry-tags(d.meta, id: d.id),
    coll: d.meta.at("collection", default: "slides"),
    order: d.meta.at("order", default: none),
    href: "pdfs/" + d.id + ".pdf",
    pdf: "pdfs/" + d.id + ".pdf",
    deck: true,
    broken: false,
    has-date: true,
  ))
}

// Curated reading order for a collection's items: entries with an `order:` in their meta rank
// by it (ascending), unranked ones trail in id order. Used by the collection page when any of
// its items is ranked (see is-curated), so a documentation arc reads top to bottom.
// Body wrapped in a code block: at markup top level a `#let f(x) = items` binding ends at
// the line break, so a leading-dot method chain on the next line would be parsed as markup,
// not a continuation — silently returning `items` unsorted. The block keeps the chain in code.
#let reading-order(items) = {
  items
    .sorted(key: x => x.id)
    .sorted(key: x => if x.order == none { 1000000 } else { x.order })
}
#let is-curated(items) = items.any(x => x.order != none)

// A list of link rows, shared by the homepage and the all-entries index. On the web each row
// stacks: title + optional status, with one recency date at the right; full id, collection,
// and the PDF link share a quiet metadata line below. In the PDF the
// same rows stay as a plain prose bullet list.
#let entry-list(items, show-collection: false, collection-meta: (:), show-date-heading: true,
  root-prefix: "") = context {
  if target() == "html" {
    if show-date-heading and items.len() > 0 {
      html.elem("div", attrs: (class: "entry-list-heading",
        title: "Update date, or creation date when no update is supplied."), "Last changed")
    }
    html.elem("ul", attrs: (class: "entry-list"), {
      for it in items {
        html.elem("li", attrs: (class: "entry-row"), {
          html.elem("div", attrs: (class: "row-heading"), {
            html.elem("div", attrs: (class: "row-title-group"), {
              html.elem("a", attrs: (class: "row-title", href: root-prefix + it.href), it.title)
              if it.status != none { status-badge(it.status) }
              if it.broken { html.elem("span", attrs: (class: "entry-error"), [build error]) }
            })
            if it.has-date {
              html.elem("span", attrs: (class: "row-date"), listing-date-line(it.meta))
            }
          })
          html.elem("div", attrs: (class: "row-meta"), {
            html.elem("span", attrs: (class: "row-identity"), {
              html.elem("span", attrs: (class: "row-id"), "#" + it.id)
              if show-collection {
                [ · ]
                html.elem("a", attrs: (class: "row-collection", href: root-prefix + it.coll),
                  collection-label(it.coll, collection-meta))
              }
              if it.pdf != none {
                [ · ]
                html.elem("a", attrs: (class: "row-pdf", href: root-prefix + it.pdf,
                  aria-label: "PDF: " + it.title), "PDF")
              }
              if it.tags.len() > 0 {
                [ · ]
                html.elem("span", attrs: (class: "row-tags"), tag-list(it.tags, root-prefix: root-prefix))
              }
            })
          })
        })
      }
    })
  } else {
    for it in items {
      [- #link(it.href, it.title) \
        #text(fill: gray, size: 9pt)[#if it.has-date { row-date-line(it.meta) }#if show-collection [ · #link(it.coll, collection-label(it.coll, collection-meta))]#if it.status != none [ · #status-badge(it.status)]#if it.broken [ · build error]#if it.tags.len() > 0 [ · #tag-list(it.tags)]#if it.pdf != none [ · #link(it.pdf)[pdf]]]]
    }
  }
}

// Render items grouped by kind — Articles, then Experiments, then Slides — each a level-2
// section (empty groups dropped). Shared by the all-entries page and each collection page.
// Group order: Articles, then Experiments, then Slides. Within a group, rows sort by **status**
// (ExpScoutPlan → ExpScout → ExpStudyPlan → ExpStudy) then by **id** descending
// (newest first). A stable two-pass gives the id-desc tiebreak within each status.
// A collection where any item carries `order:` is *curated*: it lists in reading order
// (by that rank) instead of the status/newest sort, so a documentation arc reads in sequence.
#let grouped-entry-lists(items, show-collection: false, collection-meta: (:), root-prefix: "") = {
  let groups = (("page", "Writings"), ("deck", "Slides"))
  let curated = is-curated(items)
  let show-date-heading = true
  for (k, title) in groups {
    let g = items.filter(x => x.kind == k)
    g = if curated { reading-order(g) } else {
      g.sorted(key: x => x.id).rev()               // id descending
        .sorted(key: x => status-rank(x.status))    // status ascending, stable → id-desc kept within a status
    }
    if g.len() > 0 {
      heading(level: 2, title)
      entry-list(g, show-collection: show-collection, collection-meta: collection-meta,
        show-date-heading: show-date-heading, root-prefix: root-prefix)
      show-date-heading = false
    }
  }
}


// The homepage directory: one row per collection — label (links to its page) · entry
// count · description underneath. The entries themselves live on the per-collection
// pages, mirroring pinglab's home → collection → entry drill-down.
#let collection-index(colls, collection-meta) = context {
  if target() == "html" {
    html.elem("ul", attrs: (class: "coll-list"), {
      for c in colls {
        let desc = collection-description(c, collection-meta)
        html.elem("li", attrs: (class: "coll-row"), {
          html.elem("a", attrs: (class: "coll-title", href: c), collection-label(c, collection-meta))
          if desc != none { html.elem("p", attrs: (class: "coll-desc"), desc) }
        })
      }
    })
  } else {
    for c in colls {
      let desc = collection-description(c, collection-meta)
      [- #link(c, collection-label(c, collection-meta))]
      if desc != none { block(inset: (left: 1em), below: 0.6em, text(size: 9pt, fill: gray, desc)) }
    }
  }
}

#let collection-entry-count(slug, items, collection-meta) = {
  collection-children(slug, collection-meta).fold(
    items.filter(it => it.coll == slug).len(),
    (total, child) => total + collection-entry-count(child, items, collection-meta),
  )
}

// A nested collection parent owns no inferred content or order. Its authored `children` list is
// rendered verbatim as linked rows; counts include each child's descendants.
#let child-collection-index(parent, items, collection-meta) = context {
  let children = collection-children(parent, collection-meta)
  if children.len() > 0 {
    heading(level: 2, [Collections])
    html.elem("ul", attrs: (class: "coll-list child-coll-list"), {
      for child in children {
        let desc = collection-description(child, collection-meta)
        let count = collection-entry-count(child, items, collection-meta)
        html.elem("li", attrs: (class: "coll-row child-coll-row"), {
          html.elem("div", attrs: (class: "child-coll-head"), {
            html.elem("a", attrs: (class: "coll-title", href: child),
              collection-label(child, collection-meta))
            html.elem("span", attrs: (class: "coll-count"),
              str(count) + if count == 1 { " entry" } else { " entries" })
          })
          if desc != none { html.elem("p", attrs: (class: "coll-desc"), desc) }
        })
      }
    })
  }
}

// Expanded-homepage configuration and ordering are deliberately separate from collection-page
// ordering: status and curated `order` never influence these homepage writing lists.
#let index-options(index) = {
  assert(type(index) == dictionary, message: "demolab.yaml 'index' must be a mapping")
  let mode = index.at("mode", default: "directory")
  assert(mode in ("directory", "expanded"),
    message: "demolab.yaml 'index.mode' must be 'expanded' when set")
  let recent = index.at("recent", default: 0)
  assert(type(recent) == int and recent >= 0,
    message: "demolab.yaml 'index.recent' must be a non-negative integer")
  (mode: mode, recent: recent)
}

#let id-desc(items) = items.sorted(key: x => x.id).rev()
#let effective-work-date(item) = {
  let dates = entry-dates(item.meta)
  authored-date(if dates.updated != none { dates.updated } else { dates.created }, "date").key
}
#let recent-writings(items, limit) = {
  items
    .filter(x => not x.deck and x.has-date)
    .sorted(key: x => x.id)
    .sorted(key: effective-work-date)
    .rev()
    .slice(0, calc.min(limit, items.filter(x => not x.deck and x.has-date).len()))
}
#let existing-slide-order(slides, collection-items) = {
  if is-curated(collection-items) { reading-order(slides) } else {
    slides.sorted(key: x => x.id).rev().sorted(key: x => status-rank(x.status))
  }
}

#let expanded-index(colls, items, recent: 0, collection-meta: (:)) = {
  let recent-items = recent-writings(items, recent)
  if recent > 0 and recent-items.len() > 0 {
    heading(level: 2, [Recent])
    entry-list(recent-items, show-collection: true, collection-meta: collection-meta,
      show-date-heading: false)
  }
  for c in colls {
    let collection-items = items.filter(x => x.coll == c)
    let writings = id-desc(collection-items.filter(x => not x.deck))
    let slides = existing-slide-order(collection-items.filter(x => x.deck), collection-items)
    heading(level: 2, link(c, collection-label(c, collection-meta)))
    let desc = collection-description(c, collection-meta)
    if desc != none { html.elem("p", attrs: (class: "coll-desc"), desc) }
    if writings.len() > 0 {
      entry-list(writings, collection-meta: collection-meta, show-date-heading: false)
    }
    if slides.len() > 0 {
      heading(level: 3, [Slides])
      entry-list(slides, collection-meta: collection-meta, show-date-heading: false)
    }
  }
}

// --- heading anchors: a slug id on every heading so any section is deep-linkable (page#slug) ---
// to-string flattens a heading's content to plain text; slugify lowercases it to a-z0-9-hyphens.
#let to-string(c) = {
  if c == none { "" }
  else if type(c) == str { c }
  else if c.has("text") { c.text }
  else if c.has("children") { c.children.map(to-string).join() }
  else if c.has("body") { to-string(c.body) }
  else if c == [ ] { " " }
  else { "" }
}
#let slugify(s) = lower(s).replace(regex("[^a-z0-9]+"), "-").trim("-")

// --- numbered-pages: centered footer page numbers for the paged (PDF) documents ---
// main.typ wraps each entry PDF and the book in this. Not applied to the web pages
// (nothing to number) or to decks (slides stay unnumbered).
#let numbered-pages(body) = {
  set page(numbering: "1", number-align: center)
  body
}

// The paged reading surface shared by standalone entry PDFs and book chapters. Technical prose
// stays ragged-right so inline code and long identifiers don't open rivers in justified lines;
// slightly increased leading keeps the 11pt body comfortable on screen and paper. PDF code is
// monochrome (print-safe), a touch larger than Typst's 0.8em raw default, and short blocks move as
// a unit instead of splitting without a continuation cue. Long blocks remain breakable so a user
// can never create an unplaceable element taller than a page.
#let paged-body(body) = {
  set par(justify: false, leading: 0.76em)
  set raw(theme: none)
  show heading.where(level: 2): set text(size: 14pt)
  show heading.where(level: 2): set block(above: 1.25em, below: 0.4em, breakable: false)
  show raw.where(block: true): set text(0.84em / 0.8)
  show raw.where(block: true): it => {
    let lines = it.text.split("\n").len()
    block(
      width: 100%,
      fill: luma(248),
      stroke: (left: 2pt + rgb("#222222")),
      inset: (x: 11pt, y: 8pt),
      breakable: lines > 18,
      it,
    )
  }
  body
}

// --- page templates (one per output document) ---

// --- broken-entry-page: a visible stub for an entry that failed to build (a missing figure, a
// Typst error). build.py flags it after a failed compile and main.typ renders this instead of
// importing the entry, so one bad page fails on its own rather than taking down the whole site.
// HTML only (main.typ emits no PDF for a stub). ---
#let broken-entry-page(id, error, title: none, brand: default-brand) = {
  web-styles(brand: brand)
  set text(font: "New Computer Modern", size: 11pt)
  heading(level: 1, if title == none { id } else { title })
  html.elem("p", attrs: (class: "entry-meta"), [This entry failed to build, so it's a stub. The rest of the site built normally; fix the error below and rebuild to bring it back.])
  html.elem("pre", attrs: (class: "build-error"), error)
  html.elem("p", attrs: (class: "page-foot"), html.elem("a", attrs: (href: "."), [← back to all entries]))
}

#let entry-page(meta, body, id: none, kind: "page", brand: default-brand, annotations: none, collection-meta: (:), pdfs-enabled: true) = {
  // Entry metadata can override the lab-wide provider. `none` disables a global provider for
  // one entry; absent metadata inherits the root demolab.yaml setting.
  let annotation-provider = meta.at("annotations", default: annotations)
  web-styles(brand: brand, annotations: annotation-provider)
  // Collection themes are a light, web-only treatment for entries and their collection page.
  // PDFs, the combined book, and global listings retain the standard presentation.
  let theme = collection-theme(meta.at("collection", default: "uncategorized"), collection-meta)
  let tags = entry-tags(meta, id: id)
  context {
    if target() == "html" and theme != none {
      html.elem("div", attrs: (class: theme-class(theme), "aria-hidden": "true"))[]
    }
  }
  set text(font: "New Computer Modern", size: 11pt)
  // Restart figure numbering per entry: the whole bundle is one compile, so Typst's global
  // figure counter would otherwise carry across every document. Each entry (its page + its
  // standalone PDF) numbers its own figures from 1.
  counter(figure.where(kind: image)).update(0)
  // Left-align figure captions. In the PDF, align() does it; in HTML, style.css's
  // figcaption rule does — so the align (a paged-only fn) never runs during HTML export.
  show figure.caption: it => context { if target() == "html" { it } else { align(left, it) } }
  // outline() queries headings across the whole bundle; keep per-entry docs out of
  // the book's table of contents.
  set heading(outlined: false)
  // Heading anchors (web only): re-emit each heading with a slug id + a quiet permalink that
  // appears on hover, so any section is directly linkable (page#slug). The PDF/book keep
  // native headings. Typst maps a level-N heading to <h(N+1)>, so match that tag.
  show heading: it => context {
    if target() != "html" { it } else {
      let id = slugify(to-string(it.body))
      if id == "" { it } else {
        html.elem("h" + str(calc.min(it.level + 1, 6)), attrs: (id: id, class: "hx"), {
          it.body
          html.elem("a", attrs: (class: "permalink", href: "#" + id, "aria-label": "Link to this section"), "#")
        })
      }
    }
  }
  let status = meta.at("status", default: none)
  let coll = meta.at("collection", default: "uncategorized")
  let pdf-href = if pdfs-enabled and id != none { "pdfs/" + id + ".pdf" } else { none }
  context {
    if target() == "html" {
      html.elem("header", attrs: (class: "article-header"), {
        html.elem("div", attrs: (class: "row-heading"), {
          html.elem("div", attrs: (class: "row-title-group"), {
            heading(level: 1, meta.title)
          })
        })
        // Keep the preview controls' existing metadata attachment point.
        html.elem("div", attrs: (class: "entry-meta"), {
          html.elem("div", attrs: (class: "row-meta"), {
            if id != none {
              html.elem("span", attrs: (class: "row-id"), "#" + id)
              [ · ]
            }
            html.elem("a", attrs: (class: "entry-collection", href: coll),
              collection-label(coll, collection-meta))
            if status != none {
              [ · ]
              status-badge(status)
            }
            if tags.len() > 0 {
              [ · ]
              html.elem("span", attrs: (class: "entry-tags"), tag-list(tags))
            }
            if pdf-href != none {
              [ · ]
              html.elem("a", attrs: (class: "entry-pdf", href: pdf-href,
                aria-label: "PDF: " + meta.title), "PDF")
            }
          })
          html.elem("div", attrs: (class: "article-dates"), {
            let dates = entry-dates(meta)
            for (field, label) in (("created", "Created"), ("updated", "Updated")) {
              let value = dates.at(field)
              if value != none {
                html.elem("div", attrs: (class: "article-date"), {
                  [#label ]
                  html.elem("time", attrs: (datetime: value, title: label + " " + human-date(value)),
                    human-date(value, compact: true))
                })
              }
            }
          })
        })
      })
    } else {
      text(
        font: "DejaVu Sans Mono",
        size: 7.5pt,
        tracking: 0.12em,
        fill: rgb("#555555"),
        upper(meta.at("collection", default: "entry")),
      )
      v(8pt)
      show heading.where(level: 1): set text(size: 24pt)
      show heading.where(level: 1): set block(below: 0.15em)
      heading(level: 1, meta.title)
      text(size: 9pt, fill: rgb("#555555"), { if id != none [#id · ]; date-line(meta); if status != none [ · #status-badge(status)]; if tags.len() > 0 [ · #tag-list(tags)] })
      v(9pt)
      line(length: 100%, stroke: 0.6pt + rgb("#cccccc"))
      v(14pt)
    }
  }
  context { if target() == "html" { parbreak() } }
  context { if target() == "html" { body } else { paged-body(body) } }
  // a little breathing room below the last line on the web (the PDF has page margins)
  context { if target() == "html" { html.elem("div", attrs: (class: "entry-tail")) } }
}

// The homepage: a directory of collections (decks fall under `slides` by default), each a link to its
// own page. Order follows demolab.yaml's `collection-order`; unlisted collections sort
// after, by first appearance. Entry rows live on the per-collection pages.
// An optional landing.typ at the content root (see main.typ) passes its `body` in as
// `landing`; it replaces the collection directory below the brand header — a full custom
// landing page. The landing body owns its markup (html.elem); the .welcome-* classes in
// style.css are reusable building blocks.
#let index-page(entries, decks: (), brand: default-brand, collection-order: (), collection-meta: (:), index-config: (:), landing: none, pdfs-enabled: true, book-enabled: true, writings-dir: "writings") = {
  web-styles(brand: brand)
  set text(font: "New Computer Modern", size: 11pt)
  set heading(outlined: false) // keep the homepage out of the book's TOC
  let items = collect-items(entries, decks, pdfs-enabled: pdfs-enabled)
  let homepage-items = items.filter(it => collection-homepage-visible(it.coll, collection-meta))
  let configured-roots = collection-meta.keys().filter(c =>
    collection-parent(c, collection-meta) == none
      and collection-children(c, collection-meta).len() > 0
      and collection-homepage-visible(c, collection-meta))
  let colls = (homepage-items.map(it => collection-root(it.coll, collection-meta)) + configured-roots)
    .dedup().sorted(key: c => collection-rank(c, collection-order))
  let index = index-options(index-config)
  // .listing scopes the pinglab treatment: nav/index links unadorned, underline on hover
  // only (entry-body prose keeps the default underline). The homepage leads with the same
  // title + description header a collection page uses, so the two read as siblings.
  html.elem("div", attrs: (class: "listing"), {
    html.elem("header", attrs: (class: "site-head"), {
      let links = homepage-links(brand)
      html.elem("div", attrs: (class: "site-head-row"), {
        html.elem("div", attrs: (class: "site-head-copy"), {
          heading(level: 1, brand.name)
          if brand.at("description", default: none) != none {
            html.elem("p", attrs: (class: "entry-meta"), brand.description)
          }
          // Byline: the lab's owner under the title. Links to contact if given (mailto for an email).
          if brand.at("author", default: none) != none {
            let c = brand.at("contact", default: none)
            html.elem("p", attrs: (class: "byline"), {
              [by ]
              if c != none {
                link(if "@" in c and not c.starts-with("http") { "mailto:" + c } else { c }, brand.author)
              } else { brand.author }
            })
          }
        })
        if links.len() > 0 {
          html.elem("nav", attrs: (class: "site-links", "aria-label": "Site links"), {
            html.elem("ul", {
              for item in links {
                html.elem("li", html.elem("a", attrs: (href: item.url), item.label))
              }
            })
          })
        }
      })
    })
    if items.len() == 0 {
      // Freshly-scaffolded repo — no writings yet. This is the first thing a (often non-technical)
      // user sees, so keep it warm and jargon-free: point them at their coding agent, not at file
      // paths and demolab commands (those live in the README for anyone doing it by hand).
      html.elem("div", attrs: (class: "empty-state"), {
        html.elem("p", attrs: (class: "empty-lead"), [Your lab is ready.])
        html.elem("p", [
          Nothing is published here yet. Add a Typst file under #writings-dir/ and it will appear here.
        ])
      })
    } else if landing != none {
      landing
    } else if index.mode == "expanded" {
      expanded-index(colls, homepage-items, recent: index.recent, collection-meta: collection-meta)
      html.elem("p", attrs: (class: "page-foot"), {
        link("all", "Browse all entries")
        if tag-slugs(items).len() > 0 { [ · ]; link("tags", "Browse tags") }
        if book-enabled {
          [ · also available as a ]
          link("pdfs/book.pdf", "single pdf")
          [.]
        }
      })
    } else {
      collection-index(colls, collection-meta)
      html.elem("p", attrs: (class: "page-foot"), {
        link("all", "Browse all entries")
        if tag-slugs(items).len() > 0 { [ · ]; link("tags", "Browse tags") }
        if book-enabled {
          [ · also available as a ]
          link("pdfs/book.pdf", "single pdf")
          [.]
        }
      })
    }
  })
}

// A per-collection page: the collection's label + description, then its entries grouped by
// kind (Articles / Experiments / Slides), the same organisation as the all-entries page.
// Reached from the homepage directory; the foot link returns there.
#let collection-page(coll, items, all-items: none, brand: default-brand, collection-meta: (:)) = {
  web-styles(brand: brand)
  let all-items = if all-items == none { items } else { all-items }
  let theme = collection-theme(coll, collection-meta)
  context {
    if target() == "html" and theme != none {
      html.elem("div", attrs: (class: theme-class(theme), "aria-hidden": "true"))[]
    }
  }
  set text(font: "New Computer Modern", size: 11pt)
  set heading(outlined: false)
  let desc = collection-description(coll, collection-meta)
  html.elem("div", attrs: (class: "listing"), {
    heading(level: 1, collection-label(coll, collection-meta))
    if desc != none { html.elem("p", attrs: (class: "entry-meta"), desc) }
    child-collection-index(coll, all-items, collection-meta)
    grouped-entry-lists(items, collection-meta: collection-meta)
    html.elem("p", attrs: (class: "page-foot"), {
      link(".", "← all collections")
      if tag-slugs(all-items).len() > 0 { [ · ]; link("tags", "browse tags") }
    })
  })
}

// A tag directory plus one namespaced page per tag. Tags are derived only from explicit
// meta.tags values; they do not form a hierarchy or influence the order of any listing.
#let tags-page(items, brand: default-brand) = {
  web-styles(brand: brand)
  set text(font: "New Computer Modern", size: 11pt)
  set heading(outlined: false)
  html.elem("div", attrs: (class: "listing"), {
    heading(level: 1, [Tags])
    html.elem("p", attrs: (class: "entry-meta"), [Browse writings across collections by subject or method.])
    html.elem("ul", attrs: (class: "coll-list tag-directory"), {
      for tag in tag-slugs(items) {
        let count = items.filter(item => tag in item.tags).len()
        html.elem("li", attrs: (class: "coll-row child-coll-row"), {
          html.elem("div", attrs: (class: "child-coll-head"), {
            html.elem("a", attrs: (class: "coll-title tag", href: "tags/" + tag), tag)
            html.elem("span", attrs: (class: "coll-count"),
              str(count) + if count == 1 { " entry" } else { " entries" })
          })
        })
      }
    })
    html.elem("p", attrs: (class: "page-foot"), link(".", "← all collections"))
  })
}

#let tag-page(tag, items, brand: default-brand, collection-meta: (:)) = {
  web-styles(brand: brand, root-prefix: "../")
  set text(font: "New Computer Modern", size: 11pt)
  set heading(outlined: false)
  html.elem("div", attrs: (class: "listing"), {
    heading(level: 1, tag)
    html.elem("p", attrs: (class: "entry-meta"),
      str(items.len()) + if items.len() == 1 { " tagged entry" } else { " tagged entries" })
    grouped-entry-lists(items, show-collection: true, collection-meta: collection-meta,
      root-prefix: "../")
    html.elem("p", attrs: (class: "page-foot"), {
      link("../tags", "← all tags")
      [ · ]
      link("..", "all collections")
    })
  })
}

// The flat everything index — every entry + deck, newest first, each tagged with its
// collection. Linked from the homepage.
#let all-page(entries, decks: (), brand: default-brand, collection-meta: (:), pdfs-enabled: true) = {
  web-styles(brand: brand)
  set text(font: "New Computer Modern", size: 11pt)
  set heading(outlined: false)
  let items = collect-items(entries, decks, pdfs-enabled: pdfs-enabled)
  html.elem("div", attrs: (class: "listing"), {
    heading(level: 1, [All entries])
    grouped-entry-lists(items, show-collection: true, collection-meta: collection-meta)
    html.elem("p", attrs: (class: "page-foot"), {
      link(".", "← grouped by collection")
      if tag-slugs(items).len() > 0 { [ · ]; link("tags", "browse tags") }
    })
  })
}

#let book-page(entries, brand: default-brand) = {
  set text(font: "New Computer Modern", size: 11pt)
  let chapter = state("demolab-book-chapter", none)
  set page(header: context {
    let current = chapter.get()
    if current != none {
      align(right, text(size: 8pt, fill: rgb("#666666"), current))
    }
  })
  show figure.caption: set align(left) // left-align captions (book is PDF-only)
  // The book is emitted after every entry document in the same compile, so reset the global
  // figure counter here too — the book then numbers figures continuously 1…N across all chapters.
  counter(figure.where(kind: image)).update(0)
  // Table of contents (page numbers auto-resolved from each entry's heading), no cover.
  outline(title: [#brand.contents-title], depth: 1)
  for e in entries {
    chapter.update(e.meta.title)
    pagebreak()
    heading(level: 1, e.meta.title)
    let tags = entry-tags(e.meta, id: e.id)
    text(size: 9pt, fill: rgb("#555555"))[#date-line(e.meta)#if tags.len() > 0 [ · #tag-list(tags)]]
    parbreak()
    paged-body(e.body)
  }
}
