---
name: wiki-lint
description: Use when auditing a wiki for health issues — contradictions between pages, orphan pages, broken cross-references, stale claims, missing pages, or coverage gaps. Run after every 5-10 ingests.
---

# Wiki Lint

Audit the wiki. Produce a categorized report. Offer concrete fixes. Log the operation.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read it to get wiki root path and conventions.

**Link style.** Read `link_style:` from `SCHEMA.md`. If the field is missing or `<wiki-root>/config/link-style.md` does not exist, default to `obsidian` (`[[slug]]`). Otherwise, read `<wiki-root>/config/link-style.md`. All link scanning below uses the `## Parse` rule from that file (which may match more than one form). The lint report you write is itself a wiki page, so its cross-references use the `## Emit` rule.

## Process

### 1. Build the page inventory

Read `wiki/index.md`, `wiki/overview.md`, and all files in `wiki/pages/`. Build a map of:
- All existing slugs (filenames without `.md`)
- All slug references found in any page (use the `## Parse` rule from `config/link-style.md`)
- All `sources` listed in frontmatter

### 2. Run all checks

**🔴 Errors (must fix)**

- **Broken links** — slug references where no corresponding `wiki/pages/<slug>.md` exists
- **Missing frontmatter** — pages without required `title`, `tags`, `sources`, or `updated` fields

**🟡 Warnings (should fix)**

- **Orphan pages** — pages with zero inbound slug references from any other page (excluding index.md and overview.md)
- **Contradictions** — claims in one page that directly conflict with claims in another (look for the same entity described differently: dates, counts, names, relationships)
- **Stale claims** — pages not updated within 90 days that contain "current", "latest", "recent", "state-of-the-art", or year literals two or more years old
- **Chronological update sections** — page bodies containing date-stamped headers matching patterns like `## [Month]`, `## [Month] \d+`, or `**[Month] \d+ update` — these are journal entries that should be integrated in-place

**🔵 Info (consider addressing)**

- **Missing concept pages** — slug references that appear 3+ times across the wiki but have no dedicated page
- **Coverage gaps** — open questions listed in `overview.md` that could be answered by a web search or new ingest
- **Missing cross-references** — two pages that discuss the same entity but don't link to each other

### 3. Write the lint report

Write `wiki/pages/lint-<today>.md` (do not ask permission — always write this). The template below shows slug references in obsidian form for readability; in the actual report you write, every slug reference must follow the `## Emit` rule from `config/link-style.md`.

```markdown
---
title: Lint Report <today>
tags: [lint, maintenance]
sources: []
updated: <today>
---

# Lint Report — <today>

## Summary
- 🔴 Errors: N
- 🟡 Warnings: N
- 🔵 Info: N

## 🔴 Broken Links
- [[source-page]] references [[missing-slug]] — does not exist
  Fix: create the page or remove the reference

## 🔴 Missing Frontmatter
- [[page]] is missing: title, updated

## 🟡 Orphan Pages
- [[slug]] — no inbound links
  Fix: add link from [[related-page]], or delete if no longer relevant

## 🟡 Contradictions
- [[page-a]] says: "<claim>"
- [[page-b]] says: "<conflicting claim>"
  Recommendation: <which to trust, or "investigate further">

## 🟡 Stale Claims
- [[page]] last updated <date>, contains "latest" — may be outdated
  Fix: re-verify claims or add a "as of <date>" qualifier

## 🔵 Missing Concept Pages
- [[slug]] referenced N times but no page exists
  Fix: run wiki-ingest or create a stub

## 🔵 Coverage Gaps
- Open question from overview.md: "<question>"
  Suggestion: search for <X> or ingest <source type>

## 🔵 Missing Cross-References
- [[page-a]] and [[page-b]] both discuss <entity> but don't link to each other
```

Add the lint report to `wiki/index.md` under a Maintenance category (create it if it doesn't exist).

### 4. Offer concrete fixes

For each fixable category, offer:
- **Broken links:** "Remove the broken slug references? (I'll show each change before writing)"
- **Missing cross-references:** "Add the missing links between these page pairs?" (emit in the wiki's link_style)
- **Orphan page tags:** "Add `status: orphan` to frontmatter of orphan pages?"
- **Missing frontmatter:** "Add missing frontmatter fields with placeholder values?"

Show the exact diff for each change before writing. Apply only after confirmation.

### 5. Append to `wiki/log.md`

Always append — do not ask permission:
```
## [<today>] lint | <N errors> errors, <N warnings> warnings, <N info> info
Report: <slug-reference to lint-<today>, in the wiki's link_style>
Fixed: <list what was auto-fixed, or "none">
```
