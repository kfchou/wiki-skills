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
├── .gitignore        ← local-only / generated artifacts (audit reports, index) excluded from version control
├── bin/                  ← helper scripts (copied verbatim from this skill's assets/bin/)
│   ├── generate-index.py  ← regenerates wiki/index.md from page frontmatter (stdlib only)
│   ├── render-log.py      ← renders the operation log from git history (stdlib only)
│   ├── check-contradictions.py ← pre-commit gate: blocks staged pages flagged as contradicting
│   ├── lint-mechanical.py ← deterministic lint checks; full mode (JSON for wiki-lint) + --staged gate
│   └── hooks/pre-commit   ← tracked git hook chaining both gates (wired via core.hooksPath)
├── raw/              ← immutable source documents (you add these, LLM never modifies)
├── wiki/
│   ├── index.md      ← GENERATED catalog (gitignored) — never hand-edit; run bin/generate-index.py
│   ├── log.md        ← operation log — ONLY for non-git wikis (git wikis use git history)
│   ├── overview.md   ← evolving synthesis of everything known
│   └── pages/        ← all wiki pages, flat, slug-named (NO subdirectories)
└── assets/           ← downloaded images, PDFs, attachments
```

**Critical:** `wiki/pages/` is flat. All pages live here as `<slug>.md`. No subdirectories. Slugs are lowercase, hyphen-separated.

Copy the chosen link-style rule file into the wiki:

- If user picked option 1 (Obsidian): copy this skill's `config/link-style-obsidian.md` to `<wiki-root>/config/link-style.md`.
- If user picked option 2 (markdown): copy this skill's `config/link-style-markdown.md` to `<wiki-root>/config/link-style.md`.

Only one file is copied — the chosen one — and it is renamed to `link-style.md` in the wiki. Every other wiki skill reads from `<wiki-root>/config/link-style.md` to know how to emit and parse cross-references.

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
- **link_style:** <obsidian | markdown — the user's choice from step 1, question 5>
- **link_style_rules:** config/link-style.md
- See `config/link-style.md` for the exact emit and parse rules. Every wiki skill
  reads that file to decide how to write new cross-references and how to scan
  existing ones.

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
The slug-target form below follows the `link_style` declared above; the examples
shown here use that style.

**Quote citation** (preferred):
```
The model uses 8 attention heads.[^1]

<if link_style: obsidian>
[^1]: [[attention-is-all-you-need]] §3.2.2 L142-143 — "We employ h = 8 parallel attention layers"
<if link_style: markdown>
[^1]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2.2 L142-143 — "We employ h = 8 parallel attention layers"
```

**Synthesis citation** (when no single quote captures the claim):
```
The architecture is fundamentally an encoder-decoder with attention.[^2]

<if link_style: obsidian>
[^2]: [[attention-is-all-you-need]] §3.2-3.4 [synthesis] L138-202 — encoder, decoder, and
      attention sections together describe the full multi-head architecture
<if link_style: markdown>
[^2]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2-3.4 [synthesis] L138-202 — encoder, decoder, and
      attention sections together describe the full multi-head architecture
```

`L142-143` / `L138-202` are line ranges in the raw source file. For a quote they mark
the lines the quote is taken from; for a synthesis they mark the block being summarized.

Three rules for every footnote:

1. **The cited target is one of three forms:**
   - A slug reference to a source-type wiki page, written in the wiki's
     `link_style` (preferred for sources you've ingested via `wiki-ingest`)
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

## Contradiction Check

`wiki-ingest` runs a cheap contradiction check on the pages each ingest touches, before it
commits. It is a **gate, not an annotation**: every page that lands in git is clean.

- **Scope — touched neighbors only.** The check compares the pages an ingest wrote or
  edited against (a) themselves and (b) the pages that ingest already read (the entity /
  concept pages it updated and the neighbor pages from its backlink audit). It does NOT
  re-read the whole wiki — a conflict with a distant, untouched page is left to the
  periodic `wiki-lint` sweep.
- **Blocking vs. soft.** A **blocking** contradiction is a real factual conflict on the same
  entity under the same scope — incompatible dates, counts, names, or mutually-exclusive
  claims. A **soft** tension (differing emphasis, values within plausible version /
  measurement variance, claims that hold under different scope) is not a conflict.
- **The transient blocker flag.** When a blocking contradiction is found, a single line is
  written to the affected page's frontmatter and the ingest stops before committing:
  ```yaml
  contradiction-check: failed — <one-line reason naming the counterpart [[slug]] or "internal">
  ```
  The machine-readable token is the literal `contradiction-check: failed`. It exists ONLY
  while the conflict is unresolved; resolving the conflict **removes the line**. A committed
  page never carries it — there is no `passed` stamp, no severity history, nothing. Absence
  of the flag is the only "clean" state.
- **Soft tensions are surfaced, not recorded** — mentioned in the ingest summary so you can
  act if you wish, but never persisted and never blocking.

This flag is also what the **Pre-commit Gate** below scans staged files for.

## Pre-commit Gate

On a git wiki, `bin/hooks/pre-commit` (installed by `wiki-init` via
`git config core.hooksPath bin/hooks`) runs **two** deterministic gates before every commit —
no LLM:

1. **`bin/check-contradictions.py`** — scans the **staged** content of `wiki/pages/*.md`,
   frontmatter only, and **blocks the commit** if any page still carries a
   `contradiction-check: failed` flag. Backstop to the skill-level hold in `wiki-ingest`
   step 7b; on a healthy wiki it never fires. Resolve the contradiction and remove the
   `contradiction-check:` line, then re-stage.
2. **`bin/lint-mechanical.py --staged`** — scans the staged pages for **structural**
   problems and **blocks the commit** on any: missing required frontmatter, a broken
   `[[link]]`, or a slug collision (a bare slug clashing with a qualified one). Fix the page
   and re-stage.

- **Fresh clone:** `core.hooksPath` is repo-local config and is not cloned — re-run
  `git config core.hooksPath bin/hooks` once after cloning.
- **Override** an intentional commit with `git commit --no-verify`.

## Operation Log & Commit Convention
Operations: init, ingest, query, update, lint, audit, merge, split

**Git wiki — the git history is the operation log.** After an operation, the skill
suggests a commit message and commits on your confirmation (skills never auto-commit).
Render the human log on demand with `python bin/render-log.py`.

The suggested subject line follows the repo's commit convention:
1. **Detect an existing convention first** — scan recent `git log` and any `.gitmessage`,
   commitlint config, or `CONTRIBUTING.md`. If the repo already has a subject style,
   follow it.
2. **Default to Conventional Commits** when none is found, choosing the type by operation:

   | Operation        | Type                                  |
   |------------------|---------------------------------------|
   | init             | `chore`                               |
   | ingest           | `docs`                                |
   | update           | `docs`                                |
   | query (saved)    | `docs`                                |
   | lint             | `fix` if fixes applied, else `chore`  |
   | audit            | `fix` if fixes applied, else `chore`  |
   | merge / split    | `refactor`                            |

**Always append a `Wiki-Op:` trailer**, whatever the subject style — it is what
`render-log.py` keys on, decoupling the log from the subject convention. Which pages
changed is read from the commit diff, so no `Pages:` trailer is needed.
```
docs: summarize Attention Is All You Need

Wiki-Op: ingest
```

**Non-git wiki — fallback to `wiki/log.md`.** Append one entry per operation:
`## [YYYY-MM-DD] <operation> | <title>`.

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
- operation log: git wikis record each op as a commit (see Operation Log & Commit Convention) and render it with bin/render-log.py; non-git wikis append to log.md (append-only, never rewritten)
- index.md is GENERATED by bin/generate-index.py and is gitignored — never hand-edit it; set page frontmatter (category, summary) and regenerate instead
- All pages live flat in wiki/pages/ — no subdirectories
- overview.md reflects the current synthesis across all sources
- Cross-reference and citation slug-targets follow `config/link-style.md` —
  every skill reads it before writing or scanning links
- contradiction check: ingest gates on blocking contradictions in touched pages via a transient `contradiction-check: failed` flag, removed before commit — committed pages are always clean (see Contradiction Check)
- pre-commit gate: git wikis run bin/hooks/pre-commit (via core.hooksPath) → bin/check-contradictions.py, which blocks any commit staging a page that still carries the flag (see Pre-commit Gate); re-run `git config core.hooksPath bin/hooks` after a fresh clone
<if codebase domain>
- README boundary: wiki pages must not duplicate README content. Extract structural signals; link to the README for operational content (setup, contributing, running). When ingesting any README, also evaluate it for gaps and suggest edits.
</if>
```

### 4. Install the `bin/` helper scripts and generate the index

The wiki ships four stdlib-only helper scripts (no dependencies) plus a tracked git hook.
They are **bundled with this skill** at `assets/bin/` — copy them verbatim into
`<wiki-root>/bin/` (do not retype or regenerate them). From this skill's directory:

```sh
mkdir -p <wiki-root>/bin/hooks
cp assets/bin/generate-index.py       <wiki-root>/bin/
cp assets/bin/render-log.py           <wiki-root>/bin/
cp assets/bin/check-contradictions.py <wiki-root>/bin/
cp assets/bin/lint-mechanical.py      <wiki-root>/bin/
cp assets/bin/hooks/pre-commit        <wiki-root>/bin/hooks/
chmod +x <wiki-root>/bin/*.py <wiki-root>/bin/hooks/pre-commit
```

What each one does:

- **`bin/generate-index.py`** — `wiki/index.md` is generated from page frontmatter, never
  hand-written, so it can never drift from reality. After copying, run it once
  (`python bin/generate-index.py`) so a valid `index.md` exists.
- **`bin/render-log.py`** — renders the operation log from git history on demand (see the
  **Operation Log & Commit Convention** in `SCHEMA.md`). Harmless on a non-git wiki — it
  just reports that the log lives in `log.md`.
- **`bin/check-contradictions.py`** — a pre-commit gate (see the **Pre-commit Gate** and
  **Contradiction Check** sections in `SCHEMA.md`). It blocks a commit that stages a
  `wiki/pages/` file still carrying P8's `contradiction-check: failed` flag. Deterministic,
  no LLM. Harmless on a non-git wiki — it no-ops.
- **`bin/lint-mechanical.py`** — the deterministic health checks, two modes. Full mode
  (`python bin/lint-mechanical.py`) emits JSON for `wiki-lint`'s Phase 1 (broken links,
  orphans, missing frontmatter, slug collisions, stale-date, missing-concept) plus the
  tag-cluster list for its contradiction sweep. Staged mode (`--staged`) is the second
  pre-commit gate: it blocks a commit whose staged pages have missing frontmatter, a broken
  link, or a slug collision. No LLM; no-ops outside a git work tree.
- **`bin/hooks/pre-commit`** — the tracked git hook that chains both gates
  (`check-contradictions.py`, then `lint-mechanical.py --staged`) via `uv run` (so an
  interpreter is guaranteed). It is wired up in step 5.

### 5. Set up the operation log

How operations are logged depends on whether the wiki is a git repo. **Offer to run
`git init`** if it isn't one already — the git-history log is the better path.

- **Git repo:** the git history *is* the operation log (see SCHEMA's **Operation Log &
  Commit Convention**). Do **not** create `log.md`. First install the **pre-commit gates**
  (contradiction flag + structural validity): make the hook executable and point git at the
  tracked hooks directory —
  ```
  chmod +x bin/hooks/pre-commit
  git config core.hooksPath bin/hooks
  ```
  The hook is tracked (committed below), but `core.hooksPath` is repo-local config that does
  **not** survive a fresh clone — tell the user to re-run the `git config` line after
  cloning. Then suggest the initial commit and make it on the user's confirmation:
  ```
  chore: initialize <domain> wiki

  Wiki-Op: init
  ```
- **Not a git repo:** create `wiki/log.md` as the fallback operation log:
  ```markdown
  # Wiki Log

  Append-only fallback log (this wiki is not a git repo). Format:
  `## [YYYY-MM-DD] <operation> | <title>` — recent: `grep "^## \[" log.md | tail -10`

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
- For a git wiki, each operation is recorded as a commit; see the operation log with `python bin/render-log.py`
- `SCHEMA.md` is how all other skills locate this wiki — do not move or delete it
