# STRUCTURE

```text
my-presentation/
├── writings/          Typst pages and optional .slide.typ decks
├── assets/            images, video, downloads, and data read by writings
├── demolab.yaml       configuration and project-root marker
├── landing.typ        optional custom homepage body
├── .artifacts/        tracked publication evidence; travels with the repository
├── temp/              optional experiment scratch
└── .demolab/          engine-owned generated output
    ├── bundle/        private build staging
    ├── site/          generated static website
    └── pdfs/          optional generated PDFs
```

The installed `demolab-cli` package owns the renderer and theme. The presentation owns its
writings, assets, `.artifacts`, and configuration. Updating the package never overwrites those files.
