# Developing demolab

This repository is the source of `demolab-cli`. The package is installed editable, so
`uv run demolab` executes the working tree.

This checkout is the internal demo lab: its root `demolab.yaml`, `writings/`, and `assets/` are the
end-to-end fixture. Preview it with `demolab dev`. That content is not packaged into projects;
`demolab init` still installs only the stub skeleton.

Run `uv run pytest` for tests and `uv build` to produce the wheel and source distribution. A wheel
must contain `typ/`, `guides/`, and `scaffold/`, but not engine tests or generated demo output.
An end-to-end build must write `.demolab/site/index.html` and must not create `artifacts/site/`.

`demolab_cli/VERSION` is authoritative. A push to `main` that changes it publishes to PyPI through
trusted publishing and creates the matching `v<VERSION>` tag.
