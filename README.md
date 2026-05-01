# wiki-skills

A Claude Code plugin implementing [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a persistent, compounding knowledge base maintained by your LLM.

Instead of RAG (re-deriving answers from raw documents every time), this system builds and maintains a **wiki**: a structured, interlinked collection of markdown files that gets richer with every source you add and every question you ask.

## Why Wikis work well

The wiki format is remarkably similar to how the Claude Code Harness manages memory interally ([read about it here](https://kfchou.github.io/claude-code-memory-system/)). Since Claude is trained on the Claude Code Harness, that means Claude is already familiar with this structure. Unsure about other coding harnesses though.

## Installation

```bash
/plugin marketplace add kfchou/wiki-skills
/plugin install wiki-skills@kfchou/wiki-skills
```

## Skills

| Skill | Description |
|---|---|
| `wiki-init` | Bootstrap a new wiki for any domain |
| `wiki-ingest` | Add a source (paper, URL, file, transcript) to the wiki |
| `wiki-query` | Ask a question against the wiki; optionally save the answer back |
| `wiki-lint` | Health audit: contradictions, orphans, broken links, coverage gaps |
| `wiki-update` | Revise existing pages when knowledge changes |
| `wiki-audit` | Per-page citation audit: verify every footnote against its source, flag uncited claims |

## How It Works

### Three Layers

```
<wiki-root>/
├── SCHEMA.md        # Conventions + wiki root path (how skills find the wiki)
├── raw/             # Immutable source documents (you manage)
├── wiki/
│   ├── index.md     # Content catalog — every page, one-line summary
│   ├── log.md       # Append-only operation log
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
```

### Key Behaviors

- **`wiki-ingest`** surfaces key takeaways and asks what to emphasize *before* writing anything. After creating a source page, it runs a backlink audit — scanning existing pages to add bidirectional links.
- **`wiki-query`** always reads the wiki (never answers from memory). Always offers to file the answer back as a new page with `[[citations]]`.
- **`wiki-lint`** writes a severity-tiered report (`🔴 errors / 🟡 warnings / 🔵 info`) to `wiki/pages/lint-<date>.md`, offers concrete fixes, and logs unconditionally.
- **`wiki-audit`** fact-checks one page against its sources. Phase A flags uncited factual claims; Phase B dispatches one subagent per source in parallel to verify each footnote (quote citations are string-matched, `[synthesis]` citations are judged against the cited range). Writes a verdict report to `wiki/pages/audit-<page>-<date>.md` and offers concrete fixes.
- **`wiki-update`** always shows diffs before writing, always cites the source of new information, sweeps all pages for the same stale claim, and logs unconditionally.

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

## License

MIT
