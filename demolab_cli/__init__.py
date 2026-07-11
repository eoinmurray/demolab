"""demolab-cli — the demolab engine as a normal Python package.

A lab is a plain directory of user content (writings/, experiments/, tools/, artifacts/,
demolab.yaml); the engine lives here, in site-packages. The CLI materialises the few files
Typst must read from inside the lab tree into a gitignored `.demolab/` staging dir, and
stages `typ/main.typ` into temp/bundle/ per build — everything else (runbooks, guides,
scaffold, demo) ships only in the wheel. `demolab init` lays a new lab down; updating is a
normal dependency bump (`uv lock --upgrade-package demolab-cli && uv sync`).
"""
from ._paths import VERSION as __version__  # noqa: F401
