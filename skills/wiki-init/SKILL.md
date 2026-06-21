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

### 2. Create directory structure

```
<wiki-root>/
├── SCHEMA.md         ← conventions + absolute path (how other skills find the wiki)
├── .gitignore        ← local-only / generated artifacts (audit reports, index) excluded from version control
├── bin/
│   └── generate-index.py  ← regenerates wiki/index.md from page frontmatter (stdlib only)
├── raw/              ← immutable source documents (you add these, LLM never modifies)
├── wiki/
│   ├── index.md      ← GENERATED catalog (gitignored) — never hand-edit; run bin/generate-index.py
│   ├── log.md        ← append-only operation log
│   ├── overview.md   ← evolving synthesis of everything known
│   └── pages/        ← all wiki pages, flat, slug-named (NO subdirectories)
└── assets/           ← downloaded images, PDFs, attachments
```

**Critical:** `wiki/pages/` is flat. All pages live here as `<slug>.md`. No subdirectories. Slugs are lowercase, hyphen-separated.

Ensure `<wiki-root>/.gitignore` excludes generated and local-only artifacts (audit
reports and the generated index) — if the wiki is or later becomes a git repo, this keeps
disposable artifacts out of version control. **Do not clobber an existing `.gitignore`**
— a reinitialized wiki, or a wiki root nested in an existing git repo, may already have
one:
- If `<wiki-root>/.gitignore` does not exist, create it with the block below.
- If it exists but is missing either ignore line, append whichever line(s) it lacks.
- If it already ignores both, leave it untouched.

```
# Audit reports are regenerated local-only artifacts (wiki-audit). The committed record
# of an audit is the `review:` frontmatter token on the audited page, not the report.
wiki/pages/audit-*.md
# index.md is generated from page frontmatter by bin/generate-index.py — a runtime
# artifact, regenerated on demand. The source of truth is each page's frontmatter.
wiki/index.md
```

This is the same create-or-append discipline `wiki-audit` uses to self-heal (Task 4).

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
category: <one of the Index Categories below>
summary: <one-line description — becomes this page's index entry>
tags: [tag1, tag2]
sources: [source-slug1]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

`category` and `summary` drive index generation (see **Index Generation** below);
`category` must match one of the wiki's Index Categories. `created` is set once when the
page is first written and never changes; `updated` bumps on every edit.

## Cross-References
Use `[[slug]]` where slug = filename without `.md`.
Example: `[[transformer-architecture]]` → `wiki/pages/transformer-architecture.md`

## Concept Identity

The slug **is** the concept's identity — there is no separate id. A concept is the
page at `wiki/pages/<slug>.md`; everything that links to it uses `[[slug]]`. This only
works if the link graph is trustworthy, so two rules hold everywhere links are written:

1. **Links are verified, never invented.** Before writing any `[[slug]]`, the slug must
   resolve to an existing `wiki/pages/<slug>.md` **or** to a page being created in the
   same operation. List the existing page set first (`ls wiki/pages/`); never emit a
   link to a slug you have not confirmed. A `[[slug]]` that resolves to nothing is a
   hallucinated link — the failure this discipline exists to prevent.

2. **Homonyms get qualified slugs.** When a new concept collides with an existing slug
   for a *different* sense, qualify both with a discriminator rather than overloading
   one page:
   - `mercury-planet` / `mercury-element` / `mercury-mythology`
   - `transformer-ml` / `transformer-electrical`

   Pick the narrowest discriminator that disambiguates. `wiki-lint` warns when slugs
   sharing a base token look like an unintended collision.

Consolidating two pages that turn out to be the same concept (merge), or separating one
overloaded page into qualified pages (split), is the job of the `wiki-merge` skill.

## Citations

Cite every non-common-knowledge factual claim. "Common knowledge" = uncontroversial,
undergraduate-level facts in this wiki's domain. Granularity is paragraph or claim,
never per-sentence. If you cannot produce a citation in one of the forms below,
find one, weaken the claim, or drop it.

Format: Markdown footnotes. Two citation kinds, three valid targets.

**Quote citation** (preferred):
```
The model uses 8 attention heads.[^1]

[^1]: [[attention-is-all-you-need]] §3.2.2 L142-143 — "We employ h = 8 parallel attention layers"
```

**Synthesis citation** (when no single quote captures the claim):
```
The architecture is fundamentally an encoder-decoder with attention.[^2]

[^2]: [[attention-is-all-you-need]] §3.2-3.4 [synthesis] L138-202 — encoder, decoder, and
      attention sections together describe the full multi-head architecture
```

`L142-143` / `L138-202` are line ranges in the raw source file. For a quote they mark
the lines the quote is taken from; for a synthesis they mark the block being summarized.

Three rules for every footnote:

1. **The cited target is one of three forms:**
   - `[[source-slug]]` — a source-type wiki page (preferred for sources you've
     ingested via `wiki-ingest`)
   - `raw/<file>` or `assets/<file>` — a path to a local file (for drive-by
     citations where a synthesis page isn't worth creating)
   - `<URL>` — a live URL, tweet, or ephemeral source (no local copy required)

   Never cite entity, concept, or analysis pages — those are syntheses, not sources.

2. **A locator is present.** Always a semantic locator: `§<section>`, `p.<n>`,
   `[HH:MM:SS]` for transcripts, URL anchor for web, or `(YYYY-MM-DD)` for dated posts.

   **Plus a line-range when the source is text-addressable.** If the resolved raw
   file is markdown, plaintext, code, or cached HTML, append a line-range token after
   the semantic locator:

   - `L<start>-<end>` — a range, e.g. `L142-145`
   - `L<n>` — a single line, e.g. `L142`
   - `L142-145,L201-203` — disjoint ranges

   The line range refers to lines in the **raw source file** resolved from the target
   (`[[slug]]` → its `**Source:**` raw path; or a direct `raw/<file>`/`assets/<file>`).
   `raw/` is immutable, so these line numbers are stable references.

   A line-range is **required** for text-addressable sources and applies to BOTH
   citation kinds — a `[synthesis]` footnote marks the block it summarizes with `L…`
   just as a quote marks the lines it quotes. **Exempt** (semantic locator only, no
   `L…`): PDFs, transcripts, and live URLs with no local cached copy.

3. **Either a verbatim quote, or the `[synthesis]` tag plus a description** of
   what the cited range supports. No third option.

**Drive-by citation examples:**
```
[^3]: raw/scaling-laws.pdf p.7 — "loss scales as a power law in compute"
[^4]: https://twitter.com/user/status/123 (2026-04-15) — "<tweet text>"
```

## Cross-Model Review

`wiki-audit strong` runs a second-opinion pass with a different-provider model and
stamps the audited page with an optional `review:` frontmatter block:
```
review:
  model: codex          # gemini | claude-sonnet
  provider: openai      # google | anthropic
  date: YYYY-MM-DD
  status: clean         # or: disputed
  findings: 2           # present only when status: disputed
```
- `status: clean` — the reviewer surfaced no disagreement with the normal audit.
- `status: disputed` — the reviewer flagged overreach or a contradiction the normal
  audit missed; `findings:` carries the count. The detail lives in the (local-only)
  audit report.
- `provider: anthropic` (the `claude-sonnet` fallback) means no different-provider CLI
  was available, so the check is same-provider and weaker.

This block is optional and is added only by `wiki-audit strong`. Pages never need it to
be valid.

## Log Entry Format
## [YYYY-MM-DD] <operation> | <title>
Operations: init, ingest, query, update, lint, audit, merge

## Index Generation
`wiki/index.md` is a generated, gitignored artifact — never hand-edit it. It is rebuilt
from page frontmatter by `bin/generate-index.py`:
- Run `python bin/generate-index.py` (or `python3`) **before reading the index**, and
  **after** any operation that adds, removes, renames, or re-categorizes a page.
- The generator groups pages by their `category` frontmatter, in the order categories are
  listed under **Index Categories** below; within a category it lists pages newest-first
  by `created`. Each entry is `- [[slug]] — summary _(created)_`.
- Pages whose filename matches `audit-*.md` are excluded (gitignored local-only
  artifacts). A page with an unrecognized or missing `category` lands in an
  `Uncategorized` section.

## Index Categories
<one per line, matching the user's chosen taxonomy>

## Conventions
- raw/ is immutable — skills never modify it
- log.md is append-only — never rewritten, only appended
- index.md is GENERATED by bin/generate-index.py and is gitignored — never hand-edit it; set page frontmatter (category, summary) and regenerate instead
- All pages live flat in wiki/pages/ — no subdirectories
- overview.md reflects the current synthesis across all sources
<if codebase domain>
- README boundary: wiki pages must not duplicate README content. Extract structural signals; link to the README for operational content (setup, contributing, running). When ingesting any README, also evaluate it for gaps and suggest edits.
</if>
```

### 4. Write `bin/generate-index.py` and generate the index

`wiki/index.md` is not hand-written — it is generated from page frontmatter so it can
never drift from reality. Write the generator to `<wiki-root>/bin/generate-index.py`
**exactly** as below (stdlib only, no dependencies), then run it once
(`python bin/generate-index.py`) so a valid `index.md` exists.

```python
#!/usr/bin/env python3
"""Generate wiki/index.md from page frontmatter.

index.md is a runtime-only, gitignored artifact. Run this before reading the index and
after any operation that adds, removes, renames, or re-categorizes a page. Never
hand-edit index.md — edit the page's frontmatter and rerun this script.
"""
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = WIKI_ROOT / "wiki" / "pages"
SCHEMA = WIKI_ROOT / "SCHEMA.md"
INDEX = WIKI_ROOT / "wiki" / "index.md"


def parse_frontmatter(text):
    """Return the page's frontmatter as a dict, or None if absent/unterminated.

    Only scalar `key: value` lines are needed (title, category, summary, created).
    List values like `tags: [...]` are ignored. No third-party deps.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    fm = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fm[key] = value
    return fm


def read_schema():
    """Return (domain, [categories]) parsed from SCHEMA.md."""
    domain, categories = "", []
    if not SCHEMA.exists():
        return domain, categories
    in_categories = False
    for line in SCHEMA.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "**Domain:**" in line:
            domain = line.split("**Domain:**", 1)[1].strip()
        if stripped.startswith("## "):
            in_categories = stripped[3:].strip().lower() == "index categories"
            continue
        if in_categories and stripped:
            cat = stripped.lstrip("-").strip()
            if cat and not cat.startswith("<"):
                categories.append(cat)
    return domain, categories


def main():
    if not PAGES_DIR.exists():
        sys.exit(f"no pages directory at {PAGES_DIR}")
    domain, schema_categories = read_schema()

    pages = []
    for path in sorted(PAGES_DIR.glob("*.md")):
        if path.name.startswith("audit-"):
            continue  # gitignored local-only artifacts
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            print(f"warning: {path.name} has no frontmatter; skipping", file=sys.stderr)
            continue
        pages.append({
            "slug": path.stem,
            "title": fm.get("title", path.stem),
            "category": fm.get("category", "Uncategorized"),
            "summary": fm.get("summary", ""),
            "created": fm.get("created", ""),
        })

    extras = sorted({p["category"] for p in pages
                     if p["category"] not in schema_categories
                     and p["category"] != "Uncategorized"})
    ordered = list(schema_categories) + extras
    if any(p["category"] == "Uncategorized" for p in pages):
        ordered.append("Uncategorized")

    out = [f"# Wiki Index — {domain}".rstrip(), "",
           "<!-- Generated by bin/generate-index.py. Do not edit by hand. -->", ""]
    for cat in ordered:
        entries = [p for p in pages if p["category"] == cat]
        if not entries:
            continue
        entries.sort(key=lambda p: p["title"])              # tiebreak: title asc
        entries.sort(key=lambda p: p["created"], reverse=True)  # primary: created desc
        out.append(f"### {cat}")
        for p in entries:
            summary = f" — {p['summary']}" if p["summary"] else ""
            date = f" _({p['created']})_" if p["created"] else ""
            out.append(f"- [[{p['slug']}]]{summary}{date}")
        out.append("")

    INDEX.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {INDEX} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
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
- Add sources to `raw/` manually, or run `wiki-ingest` directly with a URL or file path
- Run `wiki-lint` periodically to keep the wiki healthy
- `SCHEMA.md` is how all other skills locate this wiki — do not move or delete it
