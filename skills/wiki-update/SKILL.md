---
name: wiki-update
description: Use when revising existing wiki pages because knowledge has changed, a new piece of information updates or contradicts existing content, or the user wants to directly edit wiki content with LLM assistance.
---

# Wiki Update

Revise existing wiki pages. Always show diffs before writing. Always log. Always cite the source of new information.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read it to get wiki root path and conventions.

**Link style.** Read `link_style:` from `SCHEMA.md`. If the field is missing or `<wiki-root>/config/link-style.md` does not exist, default to `obsidian` (`[[slug]]`). Otherwise, read `<wiki-root>/config/link-style.md` for the emit and parse rules. Use the `## Parse` rule when scanning existing pages for cross-references; use the `## Emit` rule whenever you write new cross-references or citations.

## Process

### 1. Identify what to update

The user may provide:
- **Specific page names** — update those pages
- **New information** — regenerate the index (`python bin/generate-index.py`), read `wiki/index.md` to find affected pages, then read those pages
- **A lint report** — work through its recommendations item by item

### 2. For each page to update

Read the current content in full. Propose the change:

> **Current:** `<quote the existing text>`
> **Proposed:** `<replacement text>`
> **Reason:** `<why this change is warranted>`
> **Source:** `<URL, file path, or description of where this information comes from>`

**Always include Source.** An edit without a source citation creates untraceability — future you won't know why the change was made.

**If a proposed edit introduces a new `[[slug]]`,** the target must resolve to an
existing `wiki/pages/<slug>.md` (or a page being created in this operation) before you
write it — see the Concept Identity rule in `SCHEMA.md`. Never edit in a link to a slug
you have not confirmed.

Ask for confirmation before writing each page. Do not batch-apply changes without per-page confirmation.

### 3. Check for downstream effects

After identifying the primary pages to update, scan all of `wiki/pages/` for cross-references to those pages using the `## Parse` rule from `config/link-style.md`. For each page that links to an updated page:

- Does the update change anything that page asserts?
- If yes: flag it explicitly — "<other-page slug> may also need updating based on this change"
- Offer to update it with the same confirm-before-write flow

### 4. Contradiction sweep

If the new information contradicts something in the wiki: search all pages for the contradicted claim before updating. It may appear in more than one place. Update all occurrences, not just the most obvious one.

### 5. Regenerate `wiki/index.md`

Never hand-edit the index. If the page's one-line summary or category changed, edit the
`summary` / `category` **frontmatter** on the page itself. Always bump the page's
`updated` date (leave `created` untouched). Then regenerate:

```
python bin/generate-index.py
```

### 6. Update `wiki/overview.md`

Re-read `overview.md`. If the updates shift the overall synthesis (new understanding, resolved open question, changed key claim), propose edits to overview.md using the same confirm-before-write flow.

### 7. Record the operation

Per SCHEMA's **Operation Log & Commit Convention**:
- **Git wiki:** stage the changes and suggest a commit (default Conventional Commits
  `docs:` for an update, plus the trailer); commit on the user's confirmation.
  ```
  docs: <what changed, briefly>

  Wiki-Op: update
  ```
- **Non-git wiki:** append to `wiki/log.md` (do not skip if it exists):
  ```
  ## [<today>] update | <list of updated page slugs>
  Reason: <brief description of what changed and why>
  Source: <URL or description>
  ```

## Common Mistakes

- **Updating without citing the source** — Always include where the new information came from. This makes the wiki auditable.
- **Skipping the downstream check** — An update that contradicts a page's content while leaving pages that link to it unchanged creates silent inconsistency.
- **Skipping the log** — Every change must be recorded: a git wiki commits it (with the `Wiki-Op:` trailer); a non-git wiki appends to `log.md`.
- **Batch-writing without confirmation** — Show each diff individually. The user may accept some changes and reject others.
- **Appending instead of updating** — Do not add `## [date] update` sections to page bodies. Edit the relevant section in-place, bump the `updated` frontmatter date, and log the change in `log.md`. If you find existing date-stamped sections, offer to integrate them in-place as part of the update.
- **Inventing `[[slug]]` links in an edit** — A revision must not introduce a cross-reference to a slug that resolves to nothing. Confirm the target exists (or create it); see the Concept Identity rule in `SCHEMA.md`.
