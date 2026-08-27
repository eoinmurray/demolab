# STRUCTURE

```text
my-presentation/
├── writings/          recursive Typst sources; override with writings: in demolab.yaml
├── assets/            images, video, downloads, and data read by writings
├── demolab.yaml       configuration and project-root marker
├── landing.typ        optional custom homepage body
├── .artifacts/        tracked publication evidence; travels with the repository
├── temp/              optional experiment scratch
└── .demolab/          engine-owned generated output
    ├── bundle/        private build staging
    ├── site/          generated static website
    ├── pdfs/          optional generated PDFs
    └── preview/       opt-in dev selections, build scratch, and isolated site
```

The installed `demolab-cli` package owns the renderer and theme. The presentation owns its
writings, assets, `.artifacts`, and configuration. Updating the package never overwrites those files.

Nested source folders do not change public URLs or imply collections. For example,
`writings/physics/gravity.typ` still publishes as `gravity.html`. Article/deck IDs must be unique
across the source tree. See AUTHORING for custom directory configuration and path validation.
