---
name: wiki-query
description: Use when asking a question against a personal wiki built with wiki-init and wiki-ingest. Do not answer from general knowledge — always read the wiki pages first.
---

# Wiki Query

Ask a question. Read the wiki. Synthesize with citations. Offer to file the answer back.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read it to get wiki root path and cross-reference convention.

**Link style.** Read `link_style:` from `SCHEMA.md`. If the field is missing or `<wiki-root>/config/link-style.md` does not exist, default to `obsidian` (`[[slug]]`). Otherwise, read `<wiki-root>/config/link-style.md` for the emit and parse rules. Follow cross-references in pages using the `## Parse` rule. When you write the answer back as a wiki page (step 4), emit citations and cross-references using the `## Emit` rule.

## Process

### 1. Read `wiki/index.md` first

Scan the full index to identify which pages are likely relevant. Do NOT answer from general knowledge — the wiki is the source of truth here, even if you think you know the answer.

### 2. Read relevant pages

Read the identified pages in full. Follow one level of cross-reference links (matched via the `## Parse` rule from `config/link-style.md`) if they point to pages that seem relevant to the question.

### 3. Synthesize the answer

Write a response that:
- Is grounded in the wiki pages you read
- Cites inline using a cross-reference (in the wiki's `link_style`) for every claim sourced from a specific page
- Notes agreements and disagreements between pages
- Flags gaps: "The wiki has no page on X" or "<page slug> doesn't cover Y yet"
- Suggests follow-up sources to ingest or questions to investigate

Format for the question type:
- Factual → prose with citations
- Comparison → table
- How-it-works → numbered steps
- What-do-we-know-about-X → structured summary with open questions

### 4. Always offer to save

After answering, say:

> "Worth saving as `wiki/pages/<suggested-slug>.md`?"

If yes:
- Write the page with frontmatter: `tags: [query, analysis]`, `sources: [all cited slugs]`
- Add entry to `wiki/index.md` under the correct category (Analyses or similar), using the wiki's link_style for the new slug
- Append to `wiki/log.md`:
  ```
  ## [<today>] query | <question summary>
  Filed as: <slug-reference to the new slug, in the wiki's link_style>
  ```

If no:
- Append to `wiki/log.md`:
  ```
  ## [<today>] query | <question summary>
  Not filed.
  ```

## Common Mistakes

- **Answering from memory** — Always read the wiki pages. The wiki may contradict what you think you know, and that contradiction is valuable signal.
- **Skipping the save offer** — Good query answers compound the wiki's value. Always offer.
- **No citations** — Every factual claim should trace back to a slug reference (in the wiki's `link_style`).
