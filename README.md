# wiki-skills

A Claude Code plugin implementing [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a persistent, compounding knowledge base maintained by your LLM.

Instead of RAG (re-deriving answers from raw documents every time), this system builds and maintains a **wiki**: a structured, interlinked collection of markdown files that gets richer with every source you add and every question you ask.

## Why Wikis work well

The wiki format is remarkably similar to how the Claude Code Harness manages memory interally ([read about it here](https://kfchou.github.io/claude-code-memory-system/)). Since Claude is trained on the Claude Code Harness, that means Claude is already familiar with this structure. Unsure about other coding harnesses though.

## Installation

```bash
/plugin marketplace add kfchou/wiki-skills
/plugin install wiki-skills@wiki-skills
```

## Uninstallation

```bash
/plugin uninstall wiki-skills@wiki-skills
/plugin marketplace remove wiki-skills
```

## Requirements & setup

The skills run wherever Claude Code does. A wiki additionally relies on:

- **uv** — required. The `bin/` helper scripts (index generation, log rendering, and the
  deterministic lint and commit checks) run via `uv run`, and the pre-commit hook invokes them
  the same way. uv also provides Python: if Python 3 isn't already on the system, `uv` will
  download and manage it for you, so uv is the only thing you need to install.
- **Python 3** — standard library only, no `pip install`. Supplied by uv if not already present.
- **git** *(optional, recommended)* — if your wiki is a git repo, the operation log comes
  from git history and `wiki-init` installs the commit-time safety gates below. A non-git
  wiki works fine: it keeps a plain `wiki/log.md` and installs **no** scripts-as-hooks and
  **no** git config.
- **`codex` or `gemini` CLI** *(optional)* — enables a true cross-provider adversarial review
  in `wiki-audit strong` (see below). Without either, strong mode falls back to a same-provider
  Claude subagent and labels its findings as the weaker signal.

### Set up: `wiki-init`

When you initialize a wiki inside a git repo, run `wiki-init` to configures the following:

- **Helper scripts** copied into `bin/`: `generate-index.py`, `render-log.py`,
  `check-contradictions.py`, `lint-mechanical.py`.
- **A tracked pre-commit hook** (`bin/hooks/pre-commit`) wired up with one git config line:
  ```bash
  git config core.hooksPath bin/hooks
  ```
  It chains two deterministic, no-LLM gates that **block a commit** when a staged page has an
  unresolved contradiction flag or a structural problem (missing frontmatter, a broken
  `[[link]]`, or a slug collision).

Each wiki also records this in its own `SCHEMA.md`, so the configuration travels with the
wiki rather than living only here.

## Skills

| Skill | Description |
|---|---|
| `wiki-init` | Bootstrap a new wiki for any domain |
| `wiki-ingest` | Add a source (paper, URL, file, transcript) to the wiki |
| `wiki-query` | Ask a question against the wiki; optionally save the answer back |
| `wiki-lint` | Health audit: contradictions, orphans, broken links, coverage gaps |
| `wiki-update` | Revise existing pages when knowledge changes |
| `wiki-audit` | Per-page citation audit: verify every footnote against its source, flag uncited claims. `wiki-audit strong` adds a cross-model adversarial review |
| `wiki-merge` | Consolidate two pages that are the same concept (merge), or split one overloaded slug into qualified pages |

## How It Works

### Three Layers

```
<wiki-root>/
├── SCHEMA.md        # Conventions + wiki root path (how skills find the wiki)
├── bin/             # Helper scripts: generate-index, render-log, check-contradictions,
│                    #   lint-mechanical, and hooks/pre-commit (see Requirements & setup)
├── raw/             # Immutable source documents (you manage)
├── wiki/
│   ├── index.md     # GENERATED catalog (gitignored) — rebuilt from page frontmatter
│   ├── log.md       # Operation log — only for non-git wikis (git wikis use git history)
│   ├── overview.md  # Evolving synthesis of everything known
│   └── pages/       # All wiki pages, flat, slug-named
└── assets/          # Images, PDFs, attachments
```

### Typical Workflow

```
wiki-init          → bootstrap a new wiki
wiki-ingest        → add sources one at a time (repeat)
wiki-query         → ask questions; save good answers back as pages
wiki-audit         → fact-check a single page against its sources
wiki-lint          → periodic health check (every 5-10 ingests)
wiki-update        → revise pages when knowledge changes
wiki-merge         → merge duplicate concept pages, or split an overloaded slug
```

### Key Behaviors

- **`wiki-ingest`** surfaces key takeaways and asks what to emphasize *before* writing anything. After creating a source page, it runs a backlink audit — scanning existing pages to add bidirectional links.
- **`wiki-query`** always reads the wiki (never answers from memory). Always offers to file the answer back as a new page with `[[citations]]`.
- **`wiki-lint`** writes a severity-tiered report (`🔴 errors / 🟡 warnings / 🔵 info`) to `wiki/pages/lint-<date>.md`, offers concrete fixes, and logs unconditionally.
- **`wiki-audit`** fact-checks one page against its sources. Phase A flags uncited factual claims; Phase B dispatches one subagent per source in parallel to verify each footnote (quote citations are string-matched, `[synthesis]` citations are judged against the cited range). Writes a verdict report to `wiki/pages/audit-<page>-<date>.md` and offers concrete fixes. **Strong mode** (`wiki-audit strong`) adds Phase C: a different-provider model (`codex` or `gemini`, else a Claude subagent fallback) re-examines the same claims for overreach and contradiction, and disagreements with the normal pass become findings.
- **`wiki-update`** always shows diffs before writing, always cites the source of new information, sweeps all pages for the same stale claim, and logs unconditionally.
- **The index is generated, not hand-maintained.** `wiki/index.md` is a gitignored runtime artifact rebuilt from each page's `category` + `summary` frontmatter by `bin/generate-index.py`. Skills regenerate it before reading and after any page change, so it never drifts from the pages — no manual entry bookkeeping, no merge conflicts.
- **The operation log comes from git.** On a git wiki, each operation is recorded as a commit carrying a `Wiki-Op:` trailer (subject follows the repo's convention, defaulting to Conventional Commits). Skills suggest the commit and commit on your confirmation — they never auto-commit. `bin/render-log.py` renders the history as a human log on demand, so there's no growing `log.md`. Non-git wikis keep `log.md` as a fallback.
- **`wiki-merge`** treats the slug as a concept's identity. Merge folds a duplicate page into a survivor and rewrites every inbound `[[link]]`; split separates an overloaded slug into qualified pages (`mercury-planet` / `mercury-element`), repointing each link by meaning. Both end with a link-resolution sweep so no link is left dangling.

## Use Cases

Works for any domain where you're accumulating knowledge over time:

- **Research** — papers, articles, reports on a topic
- **Codebase documentation** — modules, APIs, architecture decisions, data flows
- **Reading notes** — books, papers, podcasts
- **Competitive analysis** — tracking companies, products, developments
- **Personal knowledge** — goals, health, self-improvement

## Inspired By

[Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (April 2026)

> "The wiki keeps getting richer with every source you add and every question you ask."

## Contributing

PRs, issues, and ideas are welcomed.

## License

MIT
