#import "/.demolab/lib.typ": *

#let meta = (
  title: "Organise collections",
  created_at: "2026-09-03",
  description: "A short example of grouping related writings.",
  collection: "guides",
  order: 2,
  tags: ("authoring", "navigation"),
)

#let body = [
  Give related writings the same `collection` value. Register that collection in
  `demolab.yaml` when it needs a friendly label, description, theme, or homepage order.

  Collections provide the site's primary navigation. Source folders only organise files;
  they do not change page URLs or infer collection membership.
]
