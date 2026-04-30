---
name: wiki-update
description: Use when revising existing wiki pages because knowledge has changed, a new piece of information updates or contradicts existing content, or the user wants to directly edit wiki content with LLM assistance.
---

# Wiki Update

Revise existing wiki pages. Always show diffs before writing. Always log. Always cite the source of new information.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read it to get wiki root path and conventions.

## Process

### 1. Identify what to update

The user may provide:
- **Specific page names** — update those pages
- **New information** — read `wiki/index.md` to find affected pages, then read those pages
- **A lint report** — work through its recommendations item by item

### 2. For each page to update

Read the current content in full. Propose the change:

> **Current:** `<quote the existing text>`
> **Proposed:** `<replacement text>`
> **Reason:** `<why this change is warranted>`
> **Source:** `<URL, file path, or description of where this information comes from>`

**Always include Source.** An edit without a source citation creates untraceability — future you won't know why the change was made.

Ask for confirmation before writing each page. Do not batch-apply changes without per-page confirmation.

### 3. Check for downstream effects

After identifying the primary pages to update, grep for `[[slug]]` references to those pages across all of `wiki/pages/`. For each page that links to an updated page:

- Does the update change anything that page asserts?
- If yes: flag it explicitly — "[[other-page]] may also need updating based on this change"
- Offer to update it with the same confirm-before-write flow

### 4. Contradiction sweep

If the new information contradicts something in the wiki: search all pages for the contradicted claim before updating. It may appear in more than one place. Update all occurrences, not just the most obvious one.

### 5. Update `wiki/index.md`

If the one-line summary for any updated page has changed, update it in `index.md`. Update the `updated` date in the page's frontmatter.

### 6. Update `wiki/overview.md`

Re-read `overview.md`. If the updates shift the overall synthesis (new understanding, resolved open question, changed key claim), propose edits to overview.md using the same confirm-before-write flow.

### 7. Append to `wiki/log.md`

Always append — do not ask permission, do not skip if `log.md` exists:
```
## [<today>] update | <list of updated page slugs>
Reason: <brief description of what changed and why>
Source: <URL or description>
```

## Common Mistakes

- **Updating without citing the source** — Always include where the new information came from. This makes the wiki auditable.
- **Skipping the downstream check** — An update that contradicts a page's content while leaving pages that link to it unchanged creates silent inconsistency.
- **Skipping the log** — Every change must be logged. The log is append-only; if `log.md` doesn't exist, create it.
- **Batch-writing without confirmation** — Show each diff individually. The user may accept some changes and reject others.
- **Appending instead of updating** — Do not add `## [date] update` sections to page bodies. Edit the relevant section in-place, bump the `updated` frontmatter date, and log the change in `log.md`. If you find existing date-stamped sections, offer to integrate them in-place as part of the update.
