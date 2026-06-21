---
name: wiki-lint
description: Use when auditing a wiki for health issues — contradictions between pages, orphan pages, broken cross-references, stale claims, missing pages, or coverage gaps. Run after every 5-10 ingests.
---

# Wiki Lint

Audit the wiki. Produce a categorized report. Offer concrete fixes. Log the operation.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read it to get wiki root path and conventions.

## Process

### 1. Build the page inventory

Read `wiki/index.md`, `wiki/overview.md`, and all files in `wiki/pages/`. Build a map of:
- All existing slugs (filenames without `.md`)
- All `[[slug]]` references found in any page
- All `sources` listed in frontmatter

### 2. Run all checks

**🔴 Errors (must fix)**

- **Broken links** — `[[slug]]` references where no corresponding `wiki/pages/<slug>.md` exists
- **Missing frontmatter** — pages without required `title`, `tags`, `sources`, or `updated` fields

**🟡 Warnings (should fix)**

- **Orphan pages** — pages with zero inbound `[[slug]]` links from any other page (excluding index.md and overview.md)
- **Contradictions** — claims in one page that directly conflict with claims in another (look for the same entity described differently: dates, counts, names, relationships)
- **Stale claims** — pages not updated within 90 days that contain "current", "latest", "recent", "state-of-the-art", or year literals two or more years old
- **Chronological update sections** — page bodies containing date-stamped headers matching patterns like `## [Month]`, `## [Month] \d+`, or `**[Month] \d+ update` — these are journal entries that should be integrated in-place
- **Colliding slugs (homonyms)** — pages whose slugs share a base token in a way that suggests an unintended collision or an undisambiguated homonym (e.g. a bare `mercury` alongside `mercury-element`, or two pages competing for the same sense). Per the Concept Identity convention in `SCHEMA.md`, distinct senses should carry qualified slugs (`mercury-planet` / `mercury-element`). Flag the pair; do not auto-rename — renaming is a `wiki-merge` split.

**🔵 Info (consider addressing)**

- **Missing concept pages** — `[[slug]]` references that appear 3+ times across the wiki but have no dedicated page
- **Coverage gaps** — open questions listed in `overview.md` that could be answered by a web search or new ingest
- **Missing cross-references** — two pages that discuss the same entity but don't link to each other
- **Merge candidates** — two pages that appear to describe the *same concept under different slugs* (near-duplicate titles, near-identical Description sections, or each defining the other as its primary subject). Distinct from a missing cross-reference: these likely should be one page, not two linked pages. Route to `wiki-merge`; never merge automatically — consolidation rewrites inbound links and deletes a page, which needs confirmation.
- **Addable line-ranges** — footnotes whose target resolves to a text-addressable raw file (markdown / plaintext / code / cached HTML) but carry no `L…` line-range. These are legacy citations: still valid, but a line-range would let `wiki-audit` verify them deterministically. Never an error — only a suggestion. PDFs, transcripts, and live URLs are exempt and must NOT be flagged.

### 3. Write the lint report

Write `wiki/pages/lint-<today>.md` (do not ask permission — always write this):

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

## 🟡 Colliding Slugs
- [[mercury]] and [[mercury-element]] share base token "mercury" — possible undisambiguated homonym
  Fix: qualify the bare slug via wiki-merge split (e.g. mercury → mercury-planet)

## 🔵 Missing Concept Pages
- [[slug]] referenced N times but no page exists
  Fix: run wiki-ingest or create a stub

## 🔵 Coverage Gaps
- Open question from overview.md: "<question>"
  Suggestion: search for <X> or ingest <source type>

## 🔵 Missing Cross-References
- [[page-a]] and [[page-b]] both discuss <entity> but don't link to each other

## 🔵 Merge Candidates
- [[page-a]] and [[page-b]] appear to describe the same concept under two slugs
  Fix: run wiki-merge to consolidate into one page (rewrites inbound links)

## 🔵 Addable Line-Ranges
- [[page]] [^3] cites text source [[markdown-source]] with no line-range
  Fix: add an `L<start>-<end>` token so wiki-audit can verify it deterministically
```

Add the lint report to `wiki/index.md` under a Maintenance category (create it if it doesn't exist).

### 4. Offer concrete fixes

For each fixable category, offer:
- **Broken links:** "Remove the broken `[[slug]]` references? (I'll show each change before writing)"
- **Missing cross-references:** "Add the missing links between these page pairs?"
- **Colliding slugs / merge candidates:** "These look like the same concept (or a homonym needing disambiguation) — want to run `wiki-merge` to consolidate or split them?" Do not fix these in `wiki-lint`; hand off to `wiki-merge`.
- **Orphan page tags:** "Add `status: orphan` to frontmatter of orphan pages?"
- **Missing frontmatter:** "Add missing frontmatter fields with placeholder values?"

Show the exact diff for each change before writing. Apply only after confirmation.

### 5. Append to `wiki/log.md`

Always append — do not ask permission:
```
## [<today>] lint | <N errors> errors, <N warnings> warnings, <N info> info
Report: [[lint-<today>]]
Fixed: <list what was auto-fixed, or "none">
```
