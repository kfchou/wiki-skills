---
name: wiki-ingest
description: Use when adding a new source to a wiki — a paper, article, URL, file, transcript, or any document. One ingest may touch 10-15 wiki pages.
---

# Wiki Ingest

Add a source to the wiki. Read it, discuss with the user, write a summary page, update entity/concept pages, and maintain the index, overview, and log.

## Pre-condition

Search for `SCHEMA.md` starting from the current directory and upward, or in common wiki locations (`~/wikis/`). If not found, tell the user to run `wiki-init` first.

Read `SCHEMA.md` to learn: wiki root path, page frontmatter format, cross-reference convention, log entry format, index category taxonomy.

## Process

### 1. Accept the source

The source can be:
- **File path** — read it directly; copy to `raw/<filename>` if not already there
- **URL** — use the `browse` skill to fetch it; save to `raw/<slug>.<ext>`
- **Pasted text** — use what was provided

### 2. Read the source in full

Read all content. For long sources, read in sections. Do not skip.

### 3. Surface takeaways — BEFORE writing anything

Tell the user:
- 3-5 bullet points of key takeaways
- What entities/concepts this introduces or updates
- Whether it contradicts anything already in the wiki (read `wiki/index.md` and relevant pages to check)

Ask: **"Anything specific you want me to emphasize or de-emphasize?"**

Wait for the user's response before proceeding.

### 4. Generate the slug

Lowercase, hyphens, no special characters.
Example: "Attention Is All You Need" → `attention-is-all-you-need`

### 5. Write the source summary page

Write `wiki/pages/<slug>.md`:

```markdown
---
title: <source title>
tags: [<relevant tags>]
sources: [<slug>]
updated: <today>
---

# <Source Title>

**Source:** <original URL or file path>
**Date ingested:** <today>
**Type:** <paper | article | transcript | code | other>

## Summary

<2-3 paragraph synthesis — your own words, not abstract copy-paste>

## Key Takeaways

- <bullet>

## Entities & Concepts

<list of entities/concepts as [[slug]] links>

## Relation to Other Wiki Pages

<how this connects to or updates existing knowledge>
```

### 5b. Cite as you write — do not skip

While drafting the Summary, Key Takeaways, and any other prose section, every
non-common-knowledge factual claim must carry a footnote. Read the **Citations**
section in `SCHEMA.md` for the full convention.

Two citation kinds, three valid targets:

```
Quote:     [^N]: <target> <locator> — "<verbatim quote>"
Synthesis: [^N]: <target> <locator> [synthesis] — <what supports the claim>

<target> is one of:
  [[source-slug]]      — a source wiki page (preferred for the source you're ingesting)
  raw/<file>           — a path, for drive-by citations to other local files
  <URL>                — a live URL or post
```

For the source being ingested, use `[[<this-source-slug>]]` — `wiki-ingest`
is creating that page now, so the target exists by the time the page is read.

If you cannot produce either citation kind for a claim, you do not have a
citation. Find one, weaken the claim ("the paper suggests..."), or drop it.

Footnotes go at the bottom of the page, below all sections. Number them
sequentially in order of first reference.

### 5c. Self-check before continuing

Re-read the draft once. Scan for unfootnoted factual claims — this is the most
common failure mode in long ingest sessions. For each, add a footnote or revise
the wording. Only then move on to entity pages.

### 6. Update entity and concept pages

For each entity/concept touched by this source:

- **Page exists:** Read it, add to or update the relevant section, add this source to frontmatter `sources` list, update `updated` date
- **Page doesn't exist:** Create it:

```markdown
---
title: <Entity or Concept Name>
tags: [entity | concept]
sources: [<this-source-slug>]
updated: <today>
---

# <Name>

## Description

<synthesis across all sources that discuss this>

## Appearances in Sources

- [[source-slug]] — <one-line note>

## Related Concepts

- [[related-slug]] — <relationship>
```

### 7. Backlink audit — do not skip

Scan ALL existing pages in `wiki/pages/` for any that mention this source's entities/concepts but don't yet link to the new page. Add `[[new-slug]]` references where appropriate.

This is the step most commonly skipped. A compounding wiki's value comes from bidirectional links.

### 8. Update `wiki/index.md`

Add an entry under the correct category:
```
- [[<slug>]] — <one-line summary> _(ingested <date>)_
```

For any new entity/concept pages created, add those too.

### 9. Update `wiki/overview.md`

Re-read the current overview. If this source:
- Introduces a significant concept: add it to "Key Entities / Concepts"
- Shifts the overall understanding: update "Current Understanding"
- Raises a new question: add it to "Open Questions"

Update the frontmatter `updated` date.

### 10. Append to `wiki/log.md`

```
## [<today>] ingest | <source title>
Pages written: <slug>
Pages updated: <comma-separated list>
```

## Common Mistakes

- **Appending chronological updates instead of editing in-place** — Wiki pages are living documents, not journals. Do not add sections like `## April 27 update:` or `**Update:**` followed by new content. Update the relevant section in-place, bump the `updated` frontmatter date, and record what changed in `log.md`. The log is the append-only record; pages are the current truth.
- **Skipping the backlink audit (step 7)** — A wiki's value compounds through bidirectional links. Always scan existing pages for entities this source introduces.
- **Summarizing the abstract instead of synthesizing** — The Summary section should reflect your own synthesis, not a rephrased abstract.

### 11. Report to user

- Summary page: `wiki/pages/<slug>.md`
- Entity/concept pages created or updated: <list>
- Pages that received backlinks: <list>
- Index and overview updated
