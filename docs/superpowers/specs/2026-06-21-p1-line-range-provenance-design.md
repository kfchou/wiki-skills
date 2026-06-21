# P1 — Line-range provenance

**Status:** Approved (design)
**Date:** 2026-06-21
**Part of:** wiki-skills improvement backlog (plan 1 of 10, dependency order). Unblocks P2 (cross-model review) and P9 (pre-commit gate).

## Goal

Turn `wiki-audit` from a re-read into a lookup by pinning each text-source citation
to exact lines in its immutable raw file. The most common audit case — verifying a
verbatim quote — becomes a deterministic line read plus string compare, with no LLM
re-read of the whole source.

## Decisions

- **Augment, not replace.** The existing semantic locator (`§3.2.2`, `p.7`,
  `[HH:MM:SS]`) stays as the human anchor. A line-range token is added alongside it
  as the machine anchor. Both are present for text sources.
- **Required for text-addressable sources.** If the resolved raw file is markdown /
  plaintext / code / cached HTML, every footnote to it must carry a line-range. The
  ingest self-check fails a text-source footnote that lacks one.
- **Exempt source types** keep semantic-only locators: PDFs (page-based), transcripts
  (timestamps), and live URLs with no local copy.
- **Line-ranges point into the immutable `raw/` source file**, not the wiki page.
  `raw/` is write-once in the llm-wiki spec, so line numbers are stable references.
- **Footnote format preserved.** No new inline `^[...]` syntax. The line-range is just
  an extra token in the existing footnote locator. Consistency with the current system
  is chosen over matching the blog post's literal `paper.md:42-58` notation.
- **Grandfather legacy citations.** Old footnotes with semantic-only locators stay
  valid. `wiki-lint` reports a text-source footnote missing a line-range as a
  low-severity "addable" suggestion, never a hard failure. No big-bang migration.

## Locator format

Optional line-range token appended to the existing locator:

```
L<start>-<end>     line range, e.g. L142-145
L<n>               single line, e.g. L142
L142-145,L201-203  disjoint ranges
```

It always refers to lines in the **raw source file** resolved from the footnote's
target (`[[slug]]` → its `**Source:**` raw path, or a direct `raw/<file>` target).

Both citation kinds carry a line-range when the source is text-addressable:

- **Quote citation** — the `L…` range is the lines the verbatim quote is taken from.
  Audit can string-match deterministically.
- **Synthesis citation** (`[synthesis]`) — the `L…` range is the **block of text
  being summarized**. There is no verbatim quote; audit confirms the summary honestly
  reflects that block via a bounded subagent read. This is the right tool when a claim
  paraphrases or aggregates a passage rather than quoting one sentence — it is a
  first-class citation kind, not a fallback.

```
[^1]: [[attention-is-all-you-need]] §3.2 L142-143 — "We employ h = 8 parallel attention layers..."
[^3]: [[attention-is-all-you-need]] §3.2-5.3 [synthesis] L138-202 — encoder/decoder + attention sections describe the architecture
[^4]: raw/scaling-laws.pdf p.7 — "loss scales as a power law in compute"   # PDF: exempt, no L…
```

The "required for text-addressable sources" rule applies to **both** kinds: a
synthesis citation to a text source must also carry an `L…` block range. What is
never required is a verbatim quote — `[synthesis]` remains a full substitute for one.

## Touch points

1. **`wiki-init` Citations section** — add `L<start>-<end>` to the locator spec;
   define "text-addressable source" and the exempt types; state the raw-file
   immutability assumption that makes line numbers stable.
2. **`wiki-ingest` (steps 5b/5c)** — when citing a text-addressable raw file, capture
   line numbers while reading and require `L…` on the footnote. The self-check (5c)
   fails a text-source footnote that lacks one.
3. **`wiki-audit`** — when a footnote has `L…`, do a deterministic string-match of the
   verbatim quote within those raw lines (cheap, no subagent). Fall back to the current
   subagent re-read for semantic-only / synthesis / exempt sources.
4. **`wiki-lint`** — text-source footnote missing `L…` → low-severity "addable" nudge,
   never a hard failure.

## Verification semantics in audit

| Footnote | Behavior |
|----------|----------|
| `L…` present, quote string-matches in range | `✅ supported` — deterministic, no model call |
| `L…` present, quote not found in range | `❌ unsupported` — cheap, no model call |
| `[synthesis]` with `L…` | subagent reads only those lines (bounded slice, cheaper) |
| No `L…` (legacy / exempt source) | current behavior unchanged (subagent re-read) |

## Worked example

Raw source `raw/attention-is-all-you-need.md` (immutable):

```
142  are all vectors. We employ h = 8 parallel attention layers, or heads.
143  For each of these we use d_k = d_v = d_model/h = 64. Due to the reduced
...
202  We used the Adam optimizer with β1 = 0.9, β2 = 0.98 and ε = 10^−9.
```

Page footnotes:

```
[^1]: [[attention-is-all-you-need]] §3.2 L142-143 — "We employ h = 8 parallel attention layers, or heads..."
[^2]: [[attention-is-all-you-need]] §5.3 L202 — "Adam optimizer with β1 = 0.9, β2 = 0.98"
```

Audit:
- `[^1]` → read raw lines 142-143, string-match → `✅ supported` (no model call)
- `[^2]` → read raw line 202, string-match → `✅` (or `❌` cheaply if the page misquoted)

## Out of scope

- Cross-model adversarial review (P2).
- Changes to the `[[wikilink]]` concept graph / entity identity (P3).
- Index/log generation, scale work (P4–P10).

P1 only enriches the locator and the audit lookup.
