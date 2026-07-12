# SUPPORT — getting help with demolab

Where to get help, and how to ask so it's answerable fast. Try self-service first: the
runbooks and the other guides (`demolab docs` lists them; `demolab docs <NAME>` prints a
file's path) cover most operating questions.

## Channels

| Channel | Use it for |
|--|--|
| **GitHub issues** — [github.com/eoinmurray/demolab/issues](https://github.com/eoinmurray/demolab/issues) | bugs, feature requests, and questions about the framework — anything the next person might hit too |

GitHub issues are searchable, so your question helps the next person and the fix lands in the open.

Install the [GitHub CLI](https://cli.github.com/) (`gh`, e.g. `brew install gh` then `gh auth login`) and your agent can file issues for you: describe the problem and ask it to submit — it will gather the details below, write the report, and post it with `gh issue create`.

> **Agent:** if `gh` is missing or unauthenticated, *suggest* it and stop — never install it or
> run `gh auth login` yourself. Installing tools and authenticating with GitHub are the user's
> call, made in their own terminal. And before posting: show the user the full issue text and
> get an explicit yes — `gh issue create` publishes to a public tracker.

## Before you open an issue

1. **Run the doctor.** Say *"doctor the repo"* — it checks the toolchain (`uv` / `typst` / `demolab`) and audits the repo against the conventions, often surfacing the problem directly with a RULES anchor and a `file:line`.
2. **Check the guides + runbooks.** [`STRUCTURE.md`](STRUCTURE.md) (the layout), [`RULES.md`](RULES.md) (the contract), [`HOUSESTYLE.md`](HOUSESTYLE.md) (authoring), and the runbooks cover most "how do I…" questions.
3. **Search existing issues.** Someone may have hit it already.

## Writing a report that gets answered

Include, in order:

1. **What you ran and what happened** — the exact command (e.g. `demolab build`) and the *full* error output, not a paraphrase.
2. **Toolchain versions** — `uv --version`, `typst --version`, `demolab version`.
3. **The commit.** demolab stamps every run's git SHA into `numbers.json` and the page/PDF footer (RULES §4.7), so you can say *exactly* which code produced the problem — paste the footer line, or `git rev-parse --short HEAD` for the repo state.
4. **Framework or content?** State whether it's the engine (the `demolab-cli` package — a demolab bug) or your own tool / experiment / writing (your code). The firewall (§3) is the dividing line; a framework bug is ours to fix, a content bug is usually yours — but ask if you're unsure.
5. **A minimal repro** if you can — the smallest writing or tool that triggers it.

## Scope

- **In scope** (please file it): the Typst engine, the tool ↔ experiment contract, publishing and CI, the runbooks and guides — everything the `demolab-cli` package ships.
- **Out of scope** (yours): the science in your tools, experiments, and writings. We can point you at the right pattern, but the models are yours by design (§3.4). "My simulation gives the wrong physics" is a you question; "the engine won't compile my writing" is an us question.
