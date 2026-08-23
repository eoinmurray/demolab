# Developing demolab

This repository is the source of `demolab-cli`. The package is installed editable, so
`uv run demolab` executes the working tree.

Preview the shipped presentation with `demolab dev --demo`; add `--landing` for the marketing
homepage. The demo under `demolab_cli/scaffold/demo/` is also the end-to-end build fixture.

Run `uv run pytest` for tests and `uv build` to produce the wheel and source distribution. A wheel
must contain `typ/`, `guides/`, and `scaffold/`, but not engine tests or generated demo output.

`demolab_cli/VERSION` is authoritative. A push to `main` that changes it publishes to PyPI through
trusted publishing and creates the matching `v<VERSION>` tag.
