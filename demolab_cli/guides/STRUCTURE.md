# STRUCTURE

```text
my-presentation/
├── writings/          Typst pages and optional .slide.typ decks
├── assets/            images, video, downloads, and data read by writings
├── demolab.yaml       configuration and project-root marker
├── landing.typ        optional custom homepage body
├── artifacts/
│   ├── site/            generated static website
│   └── pdfs/           optional generated PDFs
├── temp/              optional experiment scratch
└── .demolab/          generated engine and private build staging
```

The installed `demolab-cli` package owns the renderer and theme. The presentation owns its
writings, assets, and configuration. Updating the package never overwrites those files.
