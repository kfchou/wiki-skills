---
name: wiki-ingest
description: Use when adding a new source to a wiki — a paper, article, URL, file, transcript, or any document. One ingest may touch 10-15 wiki pages.
---

# Wiki Ingest

Add a source to the wiki. Read it, discuss with the user, write a summary page, update entity/concept pages, and maintain the index, overview, and log.

## Pre-condition

Search for `SCHEMA.md` starting from the current directory and upward, or in common wiki locations (`~/wikis/`). If not found, tell the user to run `wiki-init` first.

Read `SCHEMA.md` to learn: wiki root path, page frontmatter format, cross-reference convention, log entry format, index category taxonomy.

**Link style.** Read `link_style:` from `SCHEMA.md`. If the field is missing or `<wiki-root>/config/link-style.md` does not exist, default to `obsidian` and use `[[slug]]` as the cross-reference form. Otherwise, read `<wiki-root>/config/link-style.md` for the exact emit and parse rules. Every cross-reference and citation slug-target you write below must follow that file's `## Emit` rule. Every scan of existing pages (the backlink audit in step 7) must follow its `## Parse` rule.

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
- Whether it contradicts anything already in the wiki (regenerate the index first — `python bin/generate-index.py` — then read `wiki/index.md` and relevant pages to check)

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
category: <one of the wiki's Index Categories — e.g. Sources>
summary: <one-line description for the index>
tags: [<relevant tags>]
sources: [<slug>]
created: <today>
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

<list of entities/concepts as cross-reference links — emit each in the wiki's link_style; see config/link-style.md>

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
  <slug-reference>     — a source wiki page, written in the wiki's link_style
                         (preferred for the source you're ingesting)
  raw/<file>           — a path, for drive-by citations to other local files
  <URL>                — a live URL or post
```

For the source being ingested, the slug-reference target is `<this-source-slug>` written in the form prescribed by `config/link-style.md`. `wiki-ingest` is creating that page now, so the target exists by the time the page is read.

**Line-range provenance — required for text-addressable sources.** If the raw file
you are citing is markdown, plaintext, code, or cached HTML, every footnote to it must
carry a line-range token after the semantic locator: `L<start>-<end>` (or `L<n>` for a
single line). As you read the raw file, note the line numbers of the passage you are
citing — for a quote, the lines the quote is taken from; for a `[synthesis]` claim, the
block of lines being summarized. Example:

```
[^1]: [[<this-source-slug>]] §3.2 L142-143 — "We employ h = 8 parallel attention layers"
[^2]: [[<this-source-slug>]] §3.2-5.3 [synthesis] L138-202 — encoder/decoder + attention describe the architecture
```

Sources WITHOUT stable line numbers — PDFs, transcripts, and live URLs with no local
cached copy — are exempt: keep the semantic locator (`p.N`, `[HH:MM:SS]`, URL anchor)
and omit `L…`.

If you cannot produce either citation kind for a claim, you do not have a
citation. Find one, weaken the claim ("the paper suggests..."), or drop it.

Footnotes go at the bottom of the page, below all sections. Number them
sequentially in order of first reference.

### 5c. Self-check before continuing

Re-read the draft once. Three passes:

1. **Unfootnoted claims** — scan for factual claims with no footnote (the most common
   failure mode in long ingest sessions). For each, add a footnote or revise the wording.
2. **Missing line-ranges** — for every footnote whose target is a text-addressable raw
   file (markdown / plaintext / code / cached HTML), confirm an `L…` token is present.
   A text-source footnote with no line-range is incomplete: go back to the raw file,
   find the lines, and add the token. Exempt sources (PDF / transcript / live URL) are
   fine without one.
3. **Link resolution** — collect every `[[slug]]` you wrote in this page and confirm
   each resolves to an existing `wiki/pages/<slug>.md` or to a page you are creating in
   this same ingest. See the **Concept Identity** rule in `SCHEMA.md`. Any `[[slug]]`
   that resolves to neither is a hallucinated link: remove it, or create the page it
   points to. This is the inline version of the broken-link check `wiki-lint` runs
   wiki-wide — catching it now keeps the link graph trustworthy by construction.

Only when all three passes are clean do you move on to entity pages.

### 6. Update entity and concept pages

For each entity/concept touched by this source:

- **Page exists:** Read it, add to or update the relevant section, add this source to frontmatter `sources` list, update `updated` date
- **Page doesn't exist:** Create it:

```markdown
---
title: <Entity or Concept Name>
category: <one of the wiki's Index Categories — e.g. Entities or Concepts>
summary: <one-line description for the index>
tags: [entity | concept]
sources: [<this-source-slug>]
created: <today>
updated: <today>
---

# <Name>

## Description

<synthesis across all sources that discuss this>

## Appearances in Sources

- <slug-reference to source-slug, in the wiki's link_style> — <one-line note>

## Related Concepts

- <slug-reference to related-slug, in the wiki's link_style> — <relationship>
```

### 7. Backlink audit — do not skip

Scan ALL existing pages in `wiki/pages/` for any that mention this source's entities/concepts but don't yet link to the new page. Use the `## Parse` regex from `config/link-style.md` to detect existing references. Add new cross-references to the new page using the `## Emit` form from the same file.

This is the step most commonly skipped. A compounding wiki's value comes from bidirectional links.

**Before adding each `[[slug]]`, apply the Concept Identity rule:** the target must
resolve to a real page. When you mention an entity that *should* have a page but doesn't,
create the page (step 6) rather than linking to a slug that resolves to nothing.

**Final link-resolution sweep.** Once every page this ingest touched is written
(summary, entity/concept pages, backlinks), collect all `[[slug]]` references across
*those* pages and confirm each resolves to an existing `wiki/pages/<slug>.md`. This
extends the step 5c check to the links written after it. Fix any unresolved link before
moving on — remove it or create its page.

### 7b. Contradiction check — do not skip

Now that every page this ingest touched is written and you have its neighbors in context,
check for contradictions **before** committing. Read the **Contradiction Check** section in
`SCHEMA.md` for the full convention. This is a gate, not an annotation: a clean ingest
leaves no contradiction metadata on any page.

**Scope — what to compare (do NOT re-read the whole wiki):**
- each page you wrote/edited against itself (internal contradictions), and
- each page you wrote/edited against the pages you already read this ingest — the
  entity/concept pages from step 6 and the neighbor pages from the step 7 backlink audit.

A conflict with some distant page you never opened is out of scope here — the periodic
`wiki-lint` sweep is the backstop for that.

**Classify each contradiction you find:**

1. **Blocking** — a real factual conflict on the same entity under the same scope:
   incompatible dates, counts, names, or mutually-exclusive claims (e.g. the new source page
   says a model launched in 2024 but `[[that-model]]` already says 2023). For each blocking
   contradiction, write a single line into the affected page's frontmatter — the page you
   touched that carries the *newer* claim:
   ```yaml
   contradiction-check: failed — launch year conflicts with [[that-model]] (2024 vs 2023)
   ```
   Use `internal` in place of the `[[slug]]` for a within-page conflict. Then **stop — do
   not proceed to the commit step (step 10).** Surface the conflict (both claims, both
   locations) and offer the user these resolutions:
   - correct the newly-written page,
   - correct the counterpart page,
   - reconcile both with a scope qualifier,
   - or confirm it is not actually a conflict (it was a soft tension — see below).

   When a conflict is resolved, **remove the `contradiction-check` line** from the page.
   Only once no `contradiction-check: failed` line remains on any touched page do you
   continue.

2. **Soft** — a tension that is not a true conflict: differing emphasis, values within
   plausible version/measurement variance, or claims that hold under different scope. Do
   **not** write anything to any page and do **not** block. Note it for the step 11 summary
   so the user can act if they wish; the periodic `wiki-lint` sweep is the backstop.

### 8. Regenerate `wiki/index.md`

Do **not** hand-edit the index. Every page you wrote this ingest already carries
`category`, `summary`, and `created` in its frontmatter — that is the index's source of
truth. Regenerate it:

```
python bin/generate-index.py
```

The new source, entity, and concept pages now appear under their categories
automatically. If the generator warns about a page with no frontmatter or a page lands in
`Uncategorized`, fix that page's frontmatter and rerun.

### 9. Update `wiki/overview.md`

Re-read the current overview. If this source:
- Introduces a significant concept: add it to "Key Entities / Concepts"
- Shifts the overall understanding: update "Current Understanding"
- Raises a new question: add it to "Open Questions"

Update the frontmatter `updated` date.

### 10. Record the operation

**Gate first:** do not suggest a commit while any page touched this ingest still carries a
`contradiction-check: failed` line (step 7b). Resolve the blocking contradiction and remove
the line first — committed pages are always clean.

Per SCHEMA's **Operation Log & Commit Convention**:
- **Git wiki:** stage the wiki changes and suggest a commit (subject follows the repo's
  convention — default Conventional Commits `docs:` for an ingest — plus the trailer).
  Commit on the user's confirmation; never auto-commit.
  ```
  docs: summarize <source title>

  Wiki-Op: ingest
  ```
- **Non-git wiki:** append to `wiki/log.md`:
  ```
  ## [<today>] ingest | <source title>
  Pages written: <slug>
  Pages updated: <comma-separated list>
  ```

## Common Mistakes

- **Appending chronological updates instead of editing in-place** — Wiki pages are living documents, not journals. Do not add sections like `## April 27 update:` or `**Update:**` followed by new content. Update the relevant section in-place, bump the `updated` frontmatter date, and record what changed in the operation log (a commit on a git wiki, or `log.md` otherwise). The log is the historical record; pages are the current truth.
- **Skipping the backlink audit (step 7)** — A wiki's value compounds through bidirectional links. Always scan existing pages for entities this source introduces.
- **Inventing `[[slug]]` links** — Never write a cross-reference to a slug you have not confirmed exists or are creating now. A link that resolves to nothing is a hallucinated link. Verify against the existing page set (`ls wiki/pages/`); see the Concept Identity rule in `SCHEMA.md`.
- **Summarizing the abstract instead of synthesizing** — The Summary section should reflect your own synthesis, not a rephrased abstract.

### 11. Report to user

- Summary page: `wiki/pages/<slug>.md`
- Entity/concept pages created or updated: <list>
- Pages that received backlinks: <list>
- Index and overview updated
- Soft tensions noted (step 7b): <list any non-blocking tensions, or "none"> — not recorded on any page; act on them if you want
