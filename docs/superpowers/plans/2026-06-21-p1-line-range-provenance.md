# P1 — Line-range Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional machine-addressable line-range locator (`L<start>-<end>`) to wiki citations so `wiki-audit` can verify text-source quotes by deterministic line lookup instead of re-reading the whole source.

**Architecture:** Four prose SKILL.md files change in lockstep. `wiki-init` defines the convention (written into every wiki's `SCHEMA.md`); `wiki-audit` carries a duplicate fallback copy of that convention that must stay byte-aligned; `wiki-ingest` enforces the convention when writing footnotes; `wiki-audit` Phase B and `wiki-lint` consume it. There is no application code — the deliverable is instruction text the LLM follows at runtime.

**Tech Stack:** Markdown SKILL.md files. No build, no test runner. "Verification" for each task = a `grep`/`rg` assertion that the intended text landed, plus a manual trace against the worked example in the design spec (`docs/superpowers/specs/2026-06-21-p1-line-range-provenance-design.md`).

**Source of truth:** the approved design spec at `docs/superpowers/specs/2026-06-21-p1-line-range-provenance-design.md`. Read it before starting.

---

## Shared definitions (used verbatim across tasks — keep identical)

**Line-range locator token:**
```
L<start>-<end>     line range, e.g. L142-145
L<n>               single line, e.g. L142
L142-145,L201-203  disjoint ranges
```
Refers to lines in the **raw source file** resolved from the footnote's target.

**Text-addressable source:** the resolved raw file is markdown, plaintext, code, or cached HTML — anything whose lines are stable and readable. These **require** an `L…` token on every footnote (both quote and synthesis kinds).

**Exempt sources** (semantic locator only, no `L…`): PDFs (`p.N`), transcripts (`[HH:MM:SS]`), and live URLs with no local cached copy.

---

## File Structure

- Modify: `skills/wiki-init/SKILL.md` — the `## Citations` block (lines 67-112) that is written into each wiki's `SCHEMA.md`. Authoritative copy of the convention.
- Modify: `skills/wiki-audit/SKILL.md` — (a) the fallback Citations block (lines 16-30) must mirror the authoritative copy; (b) Phase B (lines 55-83) gains the deterministic line-lookup branch.
- Modify: `skills/wiki-ingest/SKILL.md` — step 5b (citation kinds) and step 5c (self-check) enforce `L…` for text sources.
- Modify: `skills/wiki-lint/SKILL.md` — a new 🔵 Info check + report template entry for text-source footnotes missing `L…`.

Order matters: Task 1 defines the convention, Task 2 mirrors it, Tasks 3-5 consume it. Do them in order.

---

### Task 1: Extend the citation convention in `wiki-init` (authoritative copy)

**Files:**
- Modify: `skills/wiki-init/SKILL.md` (the `## Citations` block, lines 67-112)

- [ ] **Step 1: Verify the current text matches what this task edits**

Run: `sed -n '100,112p' skills/wiki-init/SKILL.md`
Expected: shows rule "2. **A locator is present:**" and the "Drive-by citation examples" block. If the text differs, stop and re-read the file before editing.

- [ ] **Step 2: Replace the two example citations to show `L…`**

Find this block (lines ~76-89):
```
**Quote citation** (preferred):
\```
The model uses 8 attention heads.[^1]

[^1]: [[attention-is-all-you-need]] §3.2.2 — "We employ h = 8 parallel attention layers"
\```

**Synthesis citation** (when no single quote captures the claim):
\```
The architecture is fundamentally an encoder-decoder with attention.[^2]

[^2]: [[attention-is-all-you-need]] §3.2-3.4 [synthesis] — encoder, decoder, and
      attention sections together describe the full multi-head architecture
\```
```

Replace with:
```
**Quote citation** (preferred):
\```
The model uses 8 attention heads.[^1]

[^1]: [[attention-is-all-you-need]] §3.2.2 L142-143 — "We employ h = 8 parallel attention layers"
\```

**Synthesis citation** (when no single quote captures the claim):
\```
The architecture is fundamentally an encoder-decoder with attention.[^2]

[^2]: [[attention-is-all-you-need]] §3.2-3.4 [synthesis] L138-202 — encoder, decoder, and
      attention sections together describe the full multi-head architecture
\```

`L142-143` / `L138-202` are line ranges in the raw source file. For a quote they mark
the lines the quote is taken from; for a synthesis they mark the block being summarized.
```

- [ ] **Step 3: Rewrite rule 2 (the locator rule) to define line-ranges, text-addressable, and exempt sources**

Find rule 2 (lines ~102-103):
```
2. **A locator is present:** `§<section>`, `p.<n>`, `[HH:MM:SS]` for transcripts,
   URL anchor for web, or `(YYYY-MM-DD)` for dated posts.
```

Replace with:
```
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
```

- [ ] **Step 4: Verify the edits landed and are self-consistent**

Run: `rg -n 'L142-143|L138-202|text-addressable|line-range token|L<start>-<end>' skills/wiki-init/SKILL.md`
Expected: matches in the two examples AND in rule 2. At least 4 hits.

Run: `rg -n 'Exempt.*PDFs|PDFs, transcripts, and live URLs' skills/wiki-init/SKILL.md`
Expected: one match in rule 2.

- [ ] **Step 5: Trace against the worked example**

Open `docs/superpowers/specs/2026-06-21-p1-line-range-provenance-design.md`, find the "Worked example" footnotes (`[^1]`, `[^2]`). Confirm the format you just wrote into rule 2 would produce exactly those footnotes. If not, fix rule 2 to match the spec (the spec is the source of truth).

- [ ] **Step 6: Commit**

```bash
git add skills/wiki-init/SKILL.md
git commit -m "feat(wiki-init): add line-range locators to citation convention

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Mirror the convention into the `wiki-audit` fallback block

The fallback block in `wiki-audit` is used for wikis whose `SCHEMA.md` predates the Citations section. It must teach the same locator rule as Task 1, in the compressed form the fallback uses.

**Files:**
- Modify: `skills/wiki-audit/SKILL.md` (the fenced fallback block, lines 16-30)

- [ ] **Step 1: Verify current fallback text**

Run: `sed -n '16,30p' skills/wiki-audit/SKILL.md`
Expected: the block containing `Quote:     [^N]: <target> <locator> — "<verbatim quote>"` and the three numbered rules.

- [ ] **Step 2: Replace the fallback block to include the line-range rule**

Find (lines ~16-30):
```
\```
Cite every non-common-knowledge factual claim. Granularity is paragraph or claim,
never per-sentence. Format: Markdown footnotes. Two citation kinds:

Quote:     [^N]: <target> <locator> — "<verbatim quote>"
Synthesis: [^N]: <target> <locator> [synthesis] — <what supports the claim>

Three rules:
1. Target is one of: [[source-slug]] (a source-type wiki page), raw/<file> or
   assets/<file> (a local file path), or a URL. Never an entity / concept /
   analysis page.
2. A locator is present (§section, p.N, [HH:MM:SS], URL anchor, dated post).
3. Either a verbatim quote, or the [synthesis] tag plus a description of what
   the cited range supports.
\```
```

Replace with:
```
\```
Cite every non-common-knowledge factual claim. Granularity is paragraph or claim,
never per-sentence. Format: Markdown footnotes. Two citation kinds:

Quote:     [^N]: <target> <locator> — "<verbatim quote>"
Synthesis: [^N]: <target> <locator> [synthesis] — <what supports the claim>

Three rules:
1. Target is one of: [[source-slug]] (a source-type wiki page), raw/<file> or
   assets/<file> (a local file path), or a URL. Never an entity / concept /
   analysis page.
2. A semantic locator is present (§section, p.N, [HH:MM:SS], URL anchor, dated
   post). PLUS a line-range token (L142-145, L142, or L142-145,L201-203) when the
   resolved raw source is text-addressable (markdown / plaintext / code / cached
   HTML). The line-range points into the raw source file and is required for both
   citation kinds. Exempt (semantic locator only): PDFs, transcripts, live URLs
   with no local copy.
3. Either a verbatim quote, or the [synthesis] tag plus a description of what
   the cited range supports.
\```
```

- [ ] **Step 3: Verify fallback mirrors the authoritative copy**

Run: `rg -n 'line-range token|L142-145|text-addressable' skills/wiki-audit/SKILL.md`
Expected: at least one hit inside the fallback block (lines < 40).

Run: `rg -c 'L142-145' skills/wiki-init/SKILL.md skills/wiki-audit/SKILL.md`
Expected: both files report ≥1. The token spelling `L142-145` must be identical in both.

- [ ] **Step 4: Commit**

```bash
git add skills/wiki-audit/SKILL.md
git commit -m "feat(wiki-audit): mirror line-range rule in fallback citation block

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Enforce line-ranges at ingest

**Files:**
- Modify: `skills/wiki-ingest/SKILL.md` (step 5b, lines ~80-106; step 5c, lines ~107-111)

- [ ] **Step 1: Verify current step 5b/5c text**

Run: `sed -n '80,112p' skills/wiki-ingest/SKILL.md`
Expected: shows "### 5b. Cite as you write" and "### 5c. Self-check before continuing".

- [ ] **Step 2: Add the line-range requirement to step 5b**

Find the block (lines ~98-106):
```
For the source being ingested, use `[[<this-source-slug>]]` — `wiki-ingest`
is creating that page now, so the target exists by the time the page is read.

If you cannot produce either citation kind for a claim, you do not have a
citation. Find one, weaken the claim ("the paper suggests..."), or drop it.

Footnotes go at the bottom of the page, below all sections. Number them
sequentially in order of first reference.
```

Replace with:
```
For the source being ingested, use `[[<this-source-slug>]]` — `wiki-ingest`
is creating that page now, so the target exists by the time the page is read.

**Line-range provenance — required for text-addressable sources.** If the raw file
you are citing is markdown, plaintext, code, or cached HTML, every footnote to it must
carry a line-range token after the semantic locator: `L<start>-<end>` (or `L<n>` for a
single line). As you read the raw file, note the line numbers of the passage you are
citing — for a quote, the lines the quote is taken from; for a `[synthesis]` claim, the
block of lines being summarized. Example:

\```
[^1]: [[<this-source-slug>]] §3.2 L142-143 — "We employ h = 8 parallel attention layers"
[^2]: [[<this-source-slug>]] §3.2-5.3 [synthesis] L138-202 — encoder/decoder + attention describe the architecture
\```

Sources WITHOUT stable line numbers — PDFs, transcripts, and live URLs with no local
cached copy — are exempt: keep the semantic locator (`p.N`, `[HH:MM:SS]`, URL anchor)
and omit `L…`.

If you cannot produce either citation kind for a claim, you do not have a
citation. Find one, weaken the claim ("the paper suggests..."), or drop it.

Footnotes go at the bottom of the page, below all sections. Number them
sequentially in order of first reference.
```

- [ ] **Step 3: Add the line-range check to step 5c (self-check)**

Find (lines ~107-111):
```
### 5c. Self-check before continuing

Re-read the draft once. Scan for unfootnoted factual claims — this is the most
common failure mode in long ingest sessions. For each, add a footnote or revise
the wording. Only then move on to entity pages.
```

Replace with:
```
### 5c. Self-check before continuing

Re-read the draft once. Two passes:

1. **Unfootnoted claims** — scan for factual claims with no footnote (the most common
   failure mode in long ingest sessions). For each, add a footnote or revise the wording.
2. **Missing line-ranges** — for every footnote whose target is a text-addressable raw
   file (markdown / plaintext / code / cached HTML), confirm an `L…` token is present.
   A text-source footnote with no line-range is incomplete: go back to the raw file,
   find the lines, and add the token. Exempt sources (PDF / transcript / live URL) are
   fine without one.

Only when both passes are clean do you move on to entity pages.
```

- [ ] **Step 4: Verify the edits landed**

Run: `rg -n 'Line-range provenance — required|Missing line-ranges|L142-143|L138-202' skills/wiki-ingest/SKILL.md`
Expected: matches in both step 5b and step 5c (≥3 hits).

- [ ] **Step 5: Commit**

```bash
git add skills/wiki-ingest/SKILL.md
git commit -m "feat(wiki-ingest): require line-ranges for text-source citations

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Deterministic line-lookup verification in `wiki-audit` Phase B

This is the payoff: a quote footnote with `L…` is verified by reading those raw lines and string-matching — no subagent. Synthesis with `L…` uses a subagent but on the bounded line slice. Legacy/exempt footnotes keep today's per-source subagent path.

**Files:**
- Modify: `skills/wiki-audit/SKILL.md` (Phase B, lines ~55-83; verdict rubric lines ~75-81)

- [ ] **Step 1: Verify current Phase B text**

Run: `sed -n '55,84p' skills/wiki-audit/SKILL.md`
Expected: "### 3. Phase B — cited claim verification" through the "Why per-source" note.

- [ ] **Step 2: Add `L…` to the footnote parse list**

Find (lines ~57-60):
```
For every footnote definition in the page, parse:
- The **target** — one of `[[source-slug]]`, a path under `raw/`/`assets/`, or a URL.
- The **locator** (§section, p.N, timestamp, URL anchor, dated post).
- Either the verbatim **quote** or the `[synthesis]` description.
```

Replace with:
```
For every footnote definition in the page, parse:
- The **target** — one of `[[source-slug]]`, a path under `raw/`/`assets/`, or a URL.
- The **semantic locator** (§section, p.N, timestamp, URL anchor, dated post).
- The **line-range** `L<start>-<end>` if present (text-addressable sources carry one).
- Either the verbatim **quote** or the `[synthesis]` description.
```

- [ ] **Step 3: Insert the deterministic-lookup branch before the per-source subagent grouping**

Find the paragraph that begins (line ~70):
```
**Group resolvable footnotes by their resolved file** (multiple footnotes against the same PDF read it once). Dispatch one subagent **per file, in parallel** using the `Agent` tool. Each subagent gets:
```

Insert immediately BEFORE that paragraph:
```
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
```

(The existing "Group resolvable footnotes by their resolved file…" paragraph now reads
as the body of the slow path.)

- [ ] **Step 4: Extend the verdict rubric to name the deterministic case**

Find (lines ~77-79):
```
- `✅ supported` — quote string-matches the source at the cited locator, or the `[synthesis]` description honestly summarizes the cited range.
- `❌ unsupported` — quote not found at the cited locator, or the claim is contradicted by the source.
- `⚠️ partial` — quote is paraphrased rather than verbatim (and lacks the `[synthesis]` tag), or the synthesis description overstates the cited range.
```

Replace with:
```
- `✅ supported` — quote string-matches the source at the cited locator (deterministic when an `L…` range is present), or the `[synthesis]` description honestly summarizes the cited range.
- `❌ unsupported` — quote not found at the cited locator/line-range, or the claim is contradicted by the source.
- `⚠️ partial` — quote is paraphrased rather than verbatim (and lacks the `[synthesis]` tag), or the synthesis description overstates the cited range.
```

- [ ] **Step 5: Verify the edits landed**

Run: `rg -n 'Fast path|Slow path|line-range|deterministic' skills/wiki-audit/SKILL.md`
Expected: "Fast path" and "Slow path" each appear once in Phase B; ≥1 "deterministic".

- [ ] **Step 6: Trace against the worked example**

Using the design spec's audit walkthrough, confirm: `[^1]`/`[^2]` (quote + `L…`) route to the fast path string-match; `[^3]` (`[synthesis]` + `L…`) routes to the bounded subagent; `[^4]` (PDF, no `L…`) routes to the slow per-source path. If any example routes wrong, fix the branch wording.

- [ ] **Step 7: Commit**

```bash
git add skills/wiki-audit/SKILL.md
git commit -m "feat(wiki-audit): deterministic line-lookup fast path in Phase B

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Low-severity lint nudge for missing line-ranges

**Files:**
- Modify: `skills/wiki-lint/SKILL.md` (🔵 Info checks, lines ~37-41; report template, lines ~82-92)

- [ ] **Step 1: Verify current Info-check and report text**

Run: `sed -n '37,42p' skills/wiki-lint/SKILL.md && echo '---' && sed -n '82,92p' skills/wiki-lint/SKILL.md`
Expected: the "🔵 Info (consider addressing)" bullet list, and the report's `## 🔵 Missing Concept Pages` / `Coverage Gaps` / `Missing Cross-References` sections.

- [ ] **Step 2: Add the Info check**

Find (lines ~37-41):
```
**🔵 Info (consider addressing)**

- **Missing concept pages** — `[[slug]]` references that appear 3+ times across the wiki but have no dedicated page
- **Coverage gaps** — open questions listed in `overview.md` that could be answered by a web search or new ingest
- **Missing cross-references** — two pages that discuss the same entity but don't link to each other
```

Replace with:
```
**🔵 Info (consider addressing)**

- **Missing concept pages** — `[[slug]]` references that appear 3+ times across the wiki but have no dedicated page
- **Coverage gaps** — open questions listed in `overview.md` that could be answered by a web search or new ingest
- **Missing cross-references** — two pages that discuss the same entity but don't link to each other
- **Addable line-ranges** — footnotes whose target resolves to a text-addressable raw file (markdown / plaintext / code / cached HTML) but carry no `L…` line-range. These are legacy citations: still valid, but a line-range would let `wiki-audit` verify them deterministically. Never an error — only a suggestion. PDFs, transcripts, and live URLs are exempt and must NOT be flagged.
```

- [ ] **Step 3: Add the report-template section**

Find (lines ~90-92):
```
## 🔵 Missing Cross-References
- [[page-a]] and [[page-b]] both discuss <entity> but don't link to each other
\```
```

Replace with:
```
## 🔵 Missing Cross-References
- [[page-a]] and [[page-b]] both discuss <entity> but don't link to each other

## 🔵 Addable Line-Ranges
- [[page]] [^3] cites text source [[markdown-source]] with no line-range
  Fix: add an `L<start>-<end>` token so wiki-audit can verify it deterministically
\```
```

- [ ] **Step 4: Verify the edits landed**

Run: `rg -n 'Addable line-ranges|Addable Line-Ranges|line-range' skills/wiki-lint/SKILL.md`
Expected: one hit in the Info-check list, one in the report template.

- [ ] **Step 5: Commit**

```bash
git add skills/wiki-lint/SKILL.md
git commit -m "feat(wiki-lint): suggest line-ranges for legacy text-source citations

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Cross-file consistency check

No new content — a final guard that the locator token and terminology are identical everywhere.

- [ ] **Step 1: Token spelling is identical across all four files**

Run: `rg -n 'L142-145|L142-143|L138-202|L<start>-<end>' skills/wiki-init/SKILL.md skills/wiki-audit/SKILL.md skills/wiki-ingest/SKILL.md skills/wiki-lint/SKILL.md`
Expected: hits in all four files. Confirm every line-range uses the `L<digits>[-<digits>]` form — no stray `:42-58` colon form, no `lines 42-58` prose form.

Run: `rg -n ':[0-9]+-[0-9]+|lines [0-9]+' skills/wiki-*/SKILL.md`
Expected: NO matches (would indicate an inconsistent locator style slipped in).

- [ ] **Step 2: "text-addressable" and exempt-source wording is consistent**

Run: `rg -n 'text-addressable' skills/wiki-init/SKILL.md skills/wiki-audit/SKILL.md skills/wiki-ingest/SKILL.md skills/wiki-lint/SKILL.md`
Expected: at least one hit in each of the four files.

Run: `rg -n 'PDFs, transcripts' skills/wiki-init/SKILL.md skills/wiki-audit/SKILL.md skills/wiki-ingest/SKILL.md skills/wiki-lint/SKILL.md`
Expected: the exempt-source list phrased the same way in init, audit, ingest, and lint.

- [ ] **Step 3: Final manual trace**

Re-read the design spec's "Worked example" and "What wiki-lint does to a legacy page" sections. Walk each footnote (`[^1]`–`[^4]` and the legacy `[^1]`) through the edited skills and confirm the routing and verdicts match the spec exactly. Fix any drift in the skill text (spec wins).

- [ ] **Step 4: Commit (only if Step 3 required fixes)**

```bash
git add skills/
git commit -m "fix: align line-range locator wording across wiki skills

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (completed by plan author)

**Spec coverage:** Every spec touch point maps to a task — `wiki-init` Citations (Task 1), `wiki-ingest` 5b/5c (Task 3), `wiki-audit` Phase B fast/slow path + rubric (Task 4), `wiki-lint` nudge (Task 5). The spec's "grandfather legacy" decision is realized by the optional `L…` + lint-only nudge (Tasks 4-5). The duplicate fallback convention in `wiki-audit` (not called out in the spec but present in the code) is handled by Task 2. Cross-file token consistency — a risk because the convention is duplicated — is guarded by Task 6.

**Placeholder scan:** No TBD/TODO. Every edit step shows the exact before/after text. Verification steps give exact `rg`/`sed` commands and expected results.

**Type consistency (here: token + term spelling):** The locator token is written `L<start>-<end>` / `L142-145` everywhere; "text-addressable source" and the "PDFs, transcripts, live URLs" exempt list are reused verbatim. Task 6 mechanically enforces this.
