---
name: wiki-lint
description: Use when auditing a wiki for health issues — contradictions between pages, orphan pages, broken cross-references, stale claims, missing pages, or coverage gaps. Run after every 5-10 ingests.
---

# Wiki Lint

Audit the wiki as a four-phase pipeline that keeps page bodies out of the main context: a
deterministic script (Phase 1) and per-cluster subagents (Phase 2) do the heavy reading; the
main thread only assembles findings. Produce a categorized report, offer concrete fixes, log
the operation.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read it to get wiki root path and conventions.

**Link style.** Read `link_style:` from `SCHEMA.md`. If the field is missing or `<wiki-root>/config/link-style.md` does not exist, default to `obsidian` (`[[slug]]`). Otherwise, read `<wiki-root>/config/link-style.md`. All link scanning below uses the `## Parse` rule from that file (which may match more than one form). The lint report you write is itself a wiki page, so its cross-references use the `## Emit` rule.

## Why the pipeline

The old whole-wiki pass loaded every page body into one context — it nuked the context window
as the wiki grew. Instead:

- **Phase 1** runs `bin/lint-mechanical.py`, which computes the deterministic checks (graph
  and string properties) with **no LLM and no bodies in your context**, and emits the
  tag-cluster list for Phase 2.
- **Phase 2** dispatches one subagent per tag cluster. Each reads only its cluster's pages
  (bodies live in the *subagent's* context, discarded on return) and reports the cross-page
  and body-level findings. You aggregate compact findings, never bodies.

Phase 1 checks are whole-wiki exhaustive. Phase 2 checks are **cluster-scoped**: a page that
shares no tag with any other page is not body-checked (approach A's accepted recall limit —
see *Phase 2*). Run lint periodically (every 5–10 ingests) so the scoped passes accumulate
coverage.

## Process

### Phase 0 — regenerate the index

`python bin/generate-index.py` so the index reflects current page frontmatter.

### Phase 1 — deterministic checks (script, no LLM)

Run `python bin/lint-mechanical.py` and parse its JSON. It returns:

```json
{ "findings": { "broken_links": [...], "missing_frontmatter": [...], "orphans": [...],
                "slug_collisions": [...], "stale_date": [...], "missing_concept": [...] },
  "clusters": [ {"pages": ["slug-a", "slug-b"], "split": false}, ... ] }
```

These map to report sections directly:

- **🔴 Broken links** — `broken_links` (`{page, link}`).
- **🔴 Missing frontmatter** — `missing_frontmatter` (`{page, missing:[...]}`). `overview.md`
  lives in `wiki/`, not `wiki/pages/`, and is exempt.
- **🟡 Orphan pages** — `orphans` (`{page}`): zero inbound `[[slug]]` links.
- **🟡 Colliding slugs** — `slug_collisions` (`{token, pages:[...]}`): a bare slug clashing
  with qualified ones (`mercury` vs `mercury-element`). Flag the pair; never auto-rename —
  renaming is a `wiki-merge` split.
- **🟡 Stale claims** — `stale_date` (`{page}`): not updated in 90 days and the body still
  says `current`/`latest`/`recent`/`state-of-the-art` or names a year ≥2 years old.
- **🔵 Missing concept pages** — `missing_concept` (`{slug, count}`): a `[[slug]]` referenced
  3+ times with no page.

Do **not** re-derive these by reading pages yourself — the script is the source of truth.

### Phase 2 — cluster subagents (contradictions + body-level checks)

For each cluster in the Phase 1 `clusters` list, dispatch a subagent (parallel fan-out,
batched to bound concurrency). Give it the cluster's page paths and this instruction:

> Read these pages. Report, **within these pages only**, as a compact list — each finding as
> `{type, pages:[slug,...], detail}`, or `clean` if none:
> - `contradiction` — two pages describe the same entity with conflicting dates, counts,
>   names, or relationships.
> - `missing-xref` — two pages clearly discuss the same entity but don't `[[link]]` each
>   other.
> - `merge-candidate` — two pages describe the *same concept under different slugs*
>   (near-duplicate titles / near-identical Description sections).
> - `chronological-section` — a page body carries date-stamped journal headers (`## [Month]`,
>   `**[Month] N update`) that should be integrated in-place.
> - `addable-line-range` — a footnote citing a *text-addressable* raw file (markdown /
>   plaintext / code / cached HTML) with no `L<start>-<end>` token. Exempt: PDFs, transcripts,
>   live URLs — never flag those.
> Return findings only — no page bodies.

**Aggregate** all subagent findings in the main thread and **dedup** on
`(type, sorted(pages), detail-entity)` — a page in K tags sits in K clusters, so the same
finding can surface more than once.

**Coverage note:** because subagents only see their cluster, body-level findings are
cluster-scoped. Pages sharing no tag with any other page are not body-checked. This is the
accepted limit of tag-cluster scoping; Phase 1 (graph/string checks) still covers every page.

### Phase 3 — coverage gaps, then assemble the report

First, the one body-level check that needs no page bodies: read `wiki/overview.md` and flag
**🔵 Coverage gaps** — open questions that a web search or a new ingest could answer.

Then write `wiki/pages/lint-<today>.md` (do not ask permission — always write this), merging
Phase 1 findings, the deduped Phase 2 findings, and the coverage gaps. The template below
shows slug references in obsidian form for readability; in the actual report you write, every
slug reference must follow the `## Emit` rule from `config/link-style.md`:

```markdown
---
title: Lint Report <today>
category: Maintenance
summary: <N> errors, <N> warnings, <N> info
tags: [lint, maintenance]
sources: []
created: <today>
updated: <today>
---

# Lint Report — <today>

## Summary
- 🔴 Errors: N
- 🟡 Warnings: N
- 🔵 Info: N
<!-- note here if any cluster was split (Phase 1 `split: true`): contradiction recall is
     reduced for those pages — they were too large a tag group to check together -->

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

## 🟡 Chronological Update Sections
- [[page]] has date-stamped journal headers — integrate the updates in-place

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

The lint report carries `category: Maintenance` in its frontmatter, so it lands in the index
automatically — do not hand-edit `index.md`. Run `python bin/generate-index.py`.

### Offer concrete fixes

For each fixable category, offer:
- **Broken links:** "Remove the broken slug references? (I'll show each change before writing)"
- **Missing cross-references:** "Add the missing links between these page pairs?" (emit in the wiki's link_style)
- **Colliding slugs / merge candidates:** "These look like the same concept (or a homonym needing disambiguation) — want to run `wiki-merge` to consolidate or split them?" Do not fix these in `wiki-lint`; hand off to `wiki-merge`.
- **Orphan page tags:** "Add `status: orphan` to frontmatter of orphan pages?"
- **Missing frontmatter:** "Add missing frontmatter fields with placeholder values?"

Show the exact diff for each change before writing. Apply only after confirmation.

### Record the operation

Per SCHEMA's **Operation Log & Commit Convention**:
- **Git wiki:** suggest a commit (default Conventional Commits `fix:` when fixes were
  applied, `chore:` for a report-only run, plus the trailer); commit on confirmation.
  ```
  fix: resolve <what lint fixed>

  Wiki-Op: lint
  ```
- **Non-git wiki:** append to `wiki/log.md`:
  ```
  ## [<today>] lint | <N errors> errors, <N warnings> warnings, <N info> info
  Report: <slug reference to lint-<today>, in the wiki's link_style>
  Fixed: <list what was auto-fixed, or "none">
  ```
