---
name: wiki-init
description: Use when bootstrapping a new personal wiki for any knowledge domain — research, codebase documentation, reading notes, competitive analysis, or any long-term knowledge accumulation project.
---

# Wiki Init

Bootstrap a new LLM-maintained wiki at a user-specified path.

## Pre-flight

Check whether a `SCHEMA.md` already exists nearby. If yes, ask the user if they want to reinitialize or just continue with the existing wiki.

## Process

### 1. Gather configuration (one question at a time)

Ask:
1. **Where should the wiki live?** (absolute path, e.g. `~/wikis/ml-research`)
2. **What is the domain/purpose?** (one sentence)
3. **What types of sources will you add?** (papers, URLs, code files, transcripts, etc.)
4. **What categories should `index.md` use?**
   - Research default: `Sources | Entities | Concepts | Analyses`
   - Codebase default: `Modules | APIs | Decisions | Flows` — see `codebase.md` in this skill's directory for detailed codebase guidance
   - Or specify custom
5. **How will you primarily browse this wiki?**
   1. Obsidian (or another `[[wiki-link]]`-aware viewer) — uses `[[slug]]` syntax
   2. GitHub / VS Code preview / static-site generator / plain markdown — uses `[[slug](pages/slug.md)]` syntax

   The choice is recorded in `SCHEMA.md` as `link_style: obsidian` or `link_style: markdown` and applied by every other wiki skill.

### 2. Create directory structure

```
<wiki-root>/
├── SCHEMA.md         ← conventions + absolute path (how other skills find the wiki)
├── config/
│   └── link-style.md ← cross-reference emit/parse rules (copied from this skill)
├── raw/              ← immutable source documents (you add these, LLM never modifies)
├── wiki/
│   ├── index.md      ← content catalog: every page, one-line summary, by category
│   ├── log.md        ← append-only operation log
│   ├── overview.md   ← evolving synthesis of everything known
│   └── pages/        ← all wiki pages, flat, slug-named (NO subdirectories)
└── assets/           ← downloaded images, PDFs, attachments
```

**Critical:** `wiki/pages/` is flat. All pages live here as `<slug>.md`. No subdirectories. Slugs are lowercase, hyphen-separated.

Copy the chosen link-style rule file into the wiki:

- If user picked option 1 (Obsidian): copy this skill's `config/link-style-obsidian.md` to `<wiki-root>/config/link-style.md`.
- If user picked option 2 (markdown): copy this skill's `config/link-style-markdown.md` to `<wiki-root>/config/link-style.md`.

Only one file is copied — the chosen one — and it is renamed to `link-style.md` in the wiki. Every other wiki skill reads from `<wiki-root>/config/link-style.md` to know how to emit and parse cross-references.

### 3. Write `SCHEMA.md`

```markdown
# Wiki Schema

## Identity
- **Path:** <absolute path to wiki-root>
- **Domain:** <user's domain description>
- **Source types:** <list>
- **Created:** <YYYY-MM-DD>

## Page Frontmatter
Every wiki page must start with:
---
title: <page title>
tags: [tag1, tag2]
sources: [source-slug1]
updated: YYYY-MM-DD
---

## Cross-References
- **link_style:** <obsidian | markdown — the user's choice from step 1, question 5>
- **link_style_rules:** config/link-style.md
- See `config/link-style.md` for the exact emit and parse rules. Every wiki skill
  reads that file to decide how to write new cross-references and how to scan
  existing ones.

## Citations

Cite every non-common-knowledge factual claim. "Common knowledge" = uncontroversial,
undergraduate-level facts in this wiki's domain. Granularity is paragraph or claim,
never per-sentence. If you cannot produce a citation in one of the forms below,
find one, weaken the claim, or drop it.

Format: Markdown footnotes. Two citation kinds, three valid targets.
The slug-target form below follows the `link_style` declared above; the examples
shown here use that style.

**Quote citation** (preferred):
```
The model uses 8 attention heads.[^1]

<if link_style: obsidian>
[^1]: [[attention-is-all-you-need]] §3.2.2 — "We employ h = 8 parallel attention layers"
<if link_style: markdown>
[^1]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2.2 — "We employ h = 8 parallel attention layers"
```

**Synthesis citation** (when no single quote captures the claim):
```
The architecture is fundamentally an encoder-decoder with attention.[^2]

<if link_style: obsidian>
[^2]: [[attention-is-all-you-need]] §3.2-3.4 [synthesis] — encoder, decoder, and
      attention sections together describe the full multi-head architecture
<if link_style: markdown>
[^2]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2-3.4 [synthesis] — encoder, decoder, and
      attention sections together describe the full multi-head architecture
```

Three rules for every footnote:

1. **The cited target is one of three forms:**
   - A slug reference to a source-type wiki page, written in the wiki's
     `link_style` (preferred for sources you've ingested via `wiki-ingest`)
   - `raw/<file>` or `assets/<file>` — a path to a local file (for drive-by
     citations where a synthesis page isn't worth creating)
   - `<URL>` — a live URL, tweet, or ephemeral source (no local copy required)

   Never cite entity, concept, or analysis pages — those are syntheses, not sources.

2. **A locator is present:** `§<section>`, `p.<n>`, `[HH:MM:SS]` for transcripts,
   URL anchor for web, or `(YYYY-MM-DD)` for dated posts.

3. **Either a verbatim quote, or the `[synthesis]` tag plus a description** of
   what the cited range supports. No third option.

**Drive-by citation examples:**
```
[^3]: raw/scaling-laws.pdf p.7 — "loss scales as a power law in compute"
[^4]: https://twitter.com/user/status/123 (2026-04-15) — "<tweet text>"
```

## Log Entry Format
## [YYYY-MM-DD] <operation> | <title>
Operations: init, ingest, query, update, lint, audit

## Index Categories
<one per line, matching the user's chosen taxonomy>

## Conventions
- raw/ is immutable — skills never modify it
- log.md is append-only — never rewritten, only appended
- index.md is updated on every operation that adds or changes pages
- All pages live flat in wiki/pages/ — no subdirectories
- overview.md reflects the current synthesis across all sources
- Cross-reference and citation slug-targets follow `config/link-style.md` —
  every skill reads it before writing or scanning links
<if codebase domain>
- README boundary: wiki pages must not duplicate README content. Extract structural signals; link to the README for operational content (setup, contributing, running). When ingesting any README, also evaluate it for gaps and suggest edits.
</if>
```

### 4. Write `wiki/index.md`

```markdown
# Wiki Index — <domain>

<for each category>
### <Category Name>
<!-- entries added by wiki-ingest -->
```

### 5. Write `wiki/log.md`

```markdown
# Wiki Log

Append-only. Format: `## [YYYY-MM-DD] <operation> | <title>`
Recent entries: `grep "^## \[" log.md | tail -10`

---

## [<today>] init | <domain>
```

### 6. Write `wiki/overview.md`

```markdown
---
title: Overview
tags: [overview, synthesis]
sources: []
updated: <today>
---

# <Domain> — Overview

> Evolving synthesis of everything in the wiki. Updated by wiki-ingest when sources shift the understanding.

## Current Understanding

*No sources ingested yet.*

## Open Questions

*Add questions here as they arise.*

## Key Entities / Concepts

*Populated as pages are created.*
```

### 7. Confirm

Tell the user:
- Wiki initialized at `<path>`
- Link style: `<obsidian | markdown>` — see `config/link-style.md` for the rule. To switch later, replace that file with the other variant from this skill's `config/` directory and update `link_style:` in `SCHEMA.md`. Existing pages will not be auto-converted.
- Add sources to `raw/` manually, or run `wiki-ingest` directly with a URL or file path
- Run `wiki-lint` periodically to keep the wiki healthy
- `SCHEMA.md` is how all other skills locate this wiki — do not move or delete it
