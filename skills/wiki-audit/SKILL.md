---
name: wiki-audit
description: Use when fact-checking a single wiki page against its cited sources — verifies that every footnote actually supports its claim and surfaces uncited factual claims. Run after ingesting a high-stakes page or any time you want confidence in one page's accuracy.
---

# Wiki Audit

Verify a single wiki page against its cited sources. Two phases: detect uncited factual claims, then verify cited claims by dispatching one subagent per source in parallel. In **strong mode** (`wiki-audit strong`) a third phase adds a cross-model adversarial review: a different-provider model re-examines the same claims for overreach and contradiction, and disagreements with the normal pass become findings.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to run `wiki-init` first. Read `SCHEMA.md` for the wiki root path and the **Citations** section (the rules and footnote format the audit enforces).

**Link style.** Read `link_style:` from `SCHEMA.md`. If the field is missing or `<wiki-root>/config/link-style.md` does not exist, default to `obsidian` (`[[slug]]`). Otherwise, read `<wiki-root>/config/link-style.md`. Footnote slug-targets in audited pages may be in either obsidian or markdown form — use the `## Parse` rule to recognize them both. The audit report you write is a wiki page, so its own cross-references and slug-target examples emit using the `## Emit` rule.

**If `SCHEMA.md` has no Citations section** (older wiki, initialized before this skill existed): use the fallback convention below for this run, and offer at the end to append the Citations section to `SCHEMA.md` so future operations stay consistent.

```
Cite every non-common-knowledge factual claim. Granularity is paragraph or claim,
never per-sentence. Format: Markdown footnotes. Two citation kinds:

Quote:     [^N]: <target> <locator> — "<verbatim quote>"
Synthesis: [^N]: <target> <locator> [synthesis] — <what supports the claim>

Three rules:
1. Target is one of: a slug reference to a source-type wiki page (form per the
   wiki's link_style; fallback `[[source-slug]]`), raw/<file> or assets/<file>
   (a local file path), or a URL. Never an entity / concept / analysis page.
2. A semantic locator is present (§section, p.N, [HH:MM:SS], URL anchor, dated
   post). PLUS a line-range token (L142-145, L142, or L142-145,L201-203) when the
   resolved raw source is text-addressable (markdown / plaintext / code / cached
   HTML). The line-range points into the raw source file and is required for both
   citation kinds. Exempt (semantic locator only): PDFs, transcripts, live URLs
   with no local copy.
3. Either a verbatim quote, or the [synthesis] tag plus a description of what
   the cited range supports.
```

**Mode:** if the invocation arguments contain the word `strong` (e.g. `wiki-audit strong transformer-architecture`), enable strong mode — run Phase C (§3b) after Phase B. Otherwise run normal mode (Phases A and B only). The remaining argument token, if any, names the page.

If the user did not name a page, ask which page to audit. Accept slug, filename, or absolute path. Resolve to `wiki/pages/<slug>.md`. Audit one page per run.

## Process

### 1. Read the target page

Read the full page. Note:
- The frontmatter `sources:` list (which sources the page formally cites).
- All footnote definitions (`[^N]: ...`) and references (`[^N]` in body text).

If the page has zero footnotes but contains factual content, that is itself the audit result — every claim becomes a Phase A finding. Still run Phase A; skip Phase B.

### 2. Phase A — uncited claim detection (1 subagent)

Dispatch one subagent. Give it:
- The full page contents.
- The **Citations** section copied from `SCHEMA.md`.
- The page's `sources:` list.

Task: list every non-common-knowledge factual claim that lacks a footnote. Return a structured list of `(line number, claim text, suggested-source-from-the-sources-list-or-"unknown")`.

The subagent applies the SCHEMA.md "what to cite" rule: paragraph- or claim-level granularity, common knowledge exempt.

### 3. Phase B — cited claim verification (N subagents, parallel)

For every footnote definition in the page, parse:
- The **target** — one of a slug reference (matched via `## Parse` from `config/link-style.md` — extract the slug from either obsidian or markdown form), a path under `raw/`/`assets/`, or a URL.
- The **semantic locator** (§section, p.N, timestamp, URL anchor, dated post).
- The **line-range** `L<start>-<end>` if present (text-addressable sources carry one).
- Either the verbatim **quote** or the `[synthesis]` description.

**Resolve each target to readable content:**

- slug reference → read `wiki/pages/<slug>.md` to find the raw file path (in its `**Source:**` line). Then read that raw file from `raw/` or `assets/`.
- `raw/<file>` or `assets/<file>` → read the file directly.
- `<URL>` → check whether a cached copy exists in `assets/` (filename derived from URL). If yes, read it. If not, mark the footnote `🚫 source-missing` (do not re-fetch — that belongs in the fix step).

Any target that cannot be resolved gets verdict `🚫 source-missing`; do not dispatch a subagent for it.

**Fast path — footnotes carrying a line-range (`L…`):** Do not dispatch a subagent.
Resolve the target to its raw file and read only the cited lines (e.g. `sed -n
'142,143p' raw/<file>` or the Read tool with that offset/limit). Then:

- **Quote footnote:** string-match the verbatim quote against the text in that line
  range, ignoring leading/trailing whitespace and collapsing internal runs of
  whitespace to single spaces. Match → `✅ supported`. No match → `❌ unsupported`
  (note what the lines actually say).
- **Synthesis footnote (`[synthesis]` + `L…`):** dispatch a subagent, but give it ONLY
  the cited line slice (not the whole source) plus the synthesis description, and apply
  the verdict rubric below. This is the bounded-read case — far cheaper than reading the
  full source.

A footnote whose line-range cannot be read (range outside the file, file missing) gets
`🚫 source-missing`.

**Slow path — footnotes WITHOUT a line-range** (legacy citations and exempt sources:
PDFs, transcripts, live URLs):

**Group resolvable footnotes by their resolved file** (multiple footnotes against the same PDF read it once). Dispatch one subagent **per file, in parallel** using the `Agent` tool. Each subagent gets:
- The raw source content (from `raw/`, `assets/`, or cached URL).
- The list of footnotes against that source — for each: number, locator, and either the verbatim quote or the `[synthesis]` description.
- The verdict rubric below.

Each subagent returns, per footnote, one verdict and a 1-line note:

- `✅ supported` — quote string-matches the source at the cited locator (deterministic when an `L…` range is present), or the `[synthesis]` description honestly summarizes the cited range.
- `❌ unsupported` — quote not found at the cited locator/line-range, or the claim is contradicted by the source.
- `⚠️ partial` — quote is paraphrased rather than verbatim (and lacks the `[synthesis]` tag), or the synthesis description overstates the cited range.

For ❌ and ⚠️, the note must include what the source actually says, so the user can decide how to fix.

**Why per-source, not per-footnote:** PDFs are expensive to read. One read of a 30-page paper for five footnotes beats five reads.

### 3b. Phase C — cross-model adversarial review (strong mode only)

Run this section ONLY when the audit was invoked as `wiki-audit strong`. In normal mode, skip it entirely and go to step 4.

**1. Select a reviewer model (provider chain).** Detect an available different-provider CLI, in order:
- `command -v codex` succeeds → use codex (OpenAI). Label: model `codex`, provider `openai`.
- else `command -v gemini` succeeds → use gemini (Google). Label: model `gemini`, provider `google`.
- else fall back to a Claude subagent via the `Agent` tool (Sonnet). Label: model `claude-sonnet`, provider `anthropic`. Mark every finding `same-provider — weaker signal`, and tell the user that installing codex or gemini would enable a true cross-provider check.

**2. Assemble the bounded payload** — reuse Phase B's work; do NOT re-read raw sources:
- The full target page body.
- For each cited claim: the claim text plus the line-range excerpt Phase B already read.
- The body of each page directly linked from the target via `[[slug]]` (direct links only — not the whole wiki).

Write the payload followed by the instruction block below to a temp file, `$TMPDIR/wiki-review-<page-slug>.md`.

**3. Instruction block** (include verbatim at the top of the payload file):
```
You are an adversarial reviewer. Given a wiki page, the source excerpts its claims
cite, and the bodies of its directly-linked neighbor pages, find ONLY these problems
and return them as a JSON array — nothing else. Do not restate claims that are fine.
Finding types:
- "overreach": a claim generalizes beyond what its cited excerpt supports.
- "internal-contradiction": two claims on this page conflict.
- "cross-page-contradiction": a claim conflicts with a directly-linked neighbor page.
Each finding is an object: {"type": "...", "where": "<line / footnote / page ref>",
"detail": "<one sentence>"}. Return [] if you find nothing.
```

**4. Invoke the reviewer** in non-interactive mode:
- codex:  `codex exec "$(cat "$TMPDIR/wiki-review-<page-slug>.md")"`
- gemini: `gemini -p "$(cat "$TMPDIR/wiki-review-<page-slug>.md")"`
- subagent fallback: dispatch one `Agent` whose prompt is the payload file's contents.

If a CLI call errors, check its non-interactive usage (`codex exec --help` / `gemini --help`) and retry once; if it still fails, fall through to the subagent path. Parse the reviewer's reply as the JSON array of findings (tolerate surrounding prose — extract the array).

**5. Filter to disagreements.** Keep only findings that Phase A/B did NOT already flag: a claim Phase B rated `✅`/`⚠️` that the reviewer calls `overreach` is a disagreement; a contradiction neither phase raised is a disagreement. Discard any reviewer finding that merely repeats an existing Phase A/B verdict. The surviving list is the Phase C findings.

**6. Stamp the `review:` frontmatter** on the AUDITED page (not the report). This is audit metadata — write it automatically, like the report; no content of the page changes. Add or replace a `review:` block in the page frontmatter:
```
review:
  model: codex          # gemini | claude-sonnet, per the chain above
  provider: openai      # google | anthropic
  date: <today>
  status: disputed      # `clean` if step 5 left zero disagreements, else `disputed`
  findings: 2           # the disagreement count; OMIT this line when status: clean
```
Carry the Phase C findings into step 4's report.

### 4. Write the audit report

Always write — do not ask permission. Path: `wiki/pages/audit-<page-slug>-<today>.md`. The template below uses obsidian-style slug references for readability; in the actual report, every slug reference must follow the `## Emit` rule from `config/link-style.md`.

```markdown
---
title: Audit Report — <page-slug> — <today>
tags: [audit, maintenance]
sources: []
updated: <today>
---

# Audit Report — [[<page-slug>]] — <today>

## Summary
- Cited claims verified: N
- ✅ Supported: N    ❌ Unsupported: N    ⚠️ Partial: N    🚫 Source missing: N
- 🆘 Uncited factual claims: N
- 🧪 Cross-model disagreements: N   (strong mode only; omit this line in normal mode)

## 🆘 Uncited Claims (Phase A)
- Line 42: "Transformers replaced LSTMs as the default sequence model."
  Suggested source: [[attention-is-all-you-need]] or unknown
  Fix: add footnote, weaken claim, or remove

## ❌ Unsupported (Phase B)
- [^3]: claims "8 attention heads with 128 dims each"
  Source says: "h = 8 parallel attention layers ... d_k = d_v = 64"
  Fix: correct the dimension to 64

## ⚠️ Partial (Phase B)
- [^7]: [synthesis] description says "compares to RNNs across 4 benchmarks"
  Source range covers 2 benchmarks, not 4. Tighten the description.

## 🚫 Source Missing
- [^5]: https://example.com/post — no cached copy in assets/
  Fix: re-fetch source, or remove citation

## ✅ Supported
- [^1], [^2], [^4], [^6], [^8] — all verified

## 🧪 Cross-Model Review (<model> / <provider>)
- overreach — [^3]: claim generalizes to "all transformers" but the cited excerpt
  (L142-143) covers only the encoder.
- internal-contradiction — line 12 says "8 heads", line 40 says "16 heads".
- cross-page-contradiction — [[this-page]] vs [[other-page]] disagree on the release date.
Disposition: surfaced for user review (not auto-applied).
```

Include the `## 🧪 Cross-Model Review` section ONLY in strong mode. Its header names the reviewer (e.g. `(codex / openai)`); when the provider chain fell back to the subagent it reads `(claude-sonnet / anthropic — same-provider, weaker signal)`. List one line per Phase C disagreement; if Phase C found none, write `- none — reviewer agreed with the normal audit.`

**Audit reports are local-only artifacts.** Before writing the report, ensure the wiki `.gitignore` (at the wiki root) contains the line `wiki/pages/audit-*.md`; append it if missing (self-healing for wikis initialized before this convention — create `.gitignore` if there is none). Audit reports never appear in `wiki/index.md`: the index is generated by `bin/generate-index.py`, which skips `audit-*.md` files — so there is nothing to add or remove by hand. For a strong-mode run, the committed record is the `review:` frontmatter token stamped on the page in §3b; the report itself stays local.

### 5. Offer concrete fixes

For each non-empty category, offer one at a time:

- 🆘 **Uncited:** "Search the page's `sources:` list for support and propose footnotes for these claims?"
- ❌ **Unsupported:** "Apply the corrections shown in the report? (I'll show diffs first.)"
- ⚠️ **Partial:** "Tighten the synthesis descriptions, or add the `[synthesis]` tag where missing? (diffs first.)"
- 🚫 **Source missing:** "Re-fetch URLs / locate misplaced PDFs back into `raw/`?"

Apply only after user confirmation. Show the exact diff before each write.

### 6. Record the operation

Per SCHEMA's **Operation Log & Commit Convention**. Note the audit *report* itself is
gitignored (`audit-*.md`), so only page changes are committable.
- **Git wiki:** if the audit changed any committable file — citation fixes to the page, or
  the strong-mode `review:` frontmatter token — suggest a commit (default `fix:` when fixes
  were applied, `chore:` for a review-token-only run, plus the trailer) and commit on
  confirmation. A clean normal-mode audit that changed nothing has nothing to commit.
  ```
  fix: resolve uncited claims on <page-slug>

  Wiki-Op: audit
  ```
- **Non-git wiki:** append to `wiki/log.md`:
  ```
  ## [<today>] audit | <slug reference to <page-slug>> — N supported, N unsupported, N partial, N uncited
  Report: audit-<page-slug>-<today>.md (local-only)
  Cross-model: <model>/<provider> — clean | N disagreements   # strong mode only
  Fixed: <list, or "none">
  ```

### 7. Report to user

- Audit report: `wiki/pages/audit-<page-slug>-<today>.md`
- One-line verdict (e.g. "5/8 cited claims verified, 2 uncited claims found")
- Whether any fixes were applied
