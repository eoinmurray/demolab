# Demolab

Demolab is a small presentation system for Typst. Put pages under `writings/`, static inputs under
`assets/`, and publish a website with optional PDFs.

```sh
mkdir my-presentation && cd my-presentation
uvx demolab-cli init
uv sync
uv run demolab dev
```

Each writing exports `meta` and `body`; its filename becomes its URL. Collections, themes,
citations, video, a custom landing page, and standalone decks are available without an application
server or JavaScript build chain. Set `pdfs: false` in `demolab.yaml` for web-only output.
Generated output lives under `.demolab/`; `.artifacts/` is tracked user-owned publication
evidence and travels with the repository.

Demolab 3 deliberately does not run experiments, track provenance, validate numbers, or orchestrate
research. Version 2 remains available for existing computational-lab projects.

Run `demolab docs` for the complete guide menu. Source documentation lives under
[`demolab_cli/guides/`](demolab_cli/guides/).

## License

[MIT](LICENSE)
