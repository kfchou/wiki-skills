# Wiki-Skills Improvement Roadmap

**Date:** 2026-06-21
**Source:** blog post `2026-06-20-llm-wiki-google-okf.md` — improvements observed across 200+ faithful llm-wiki implementations and Google's OKF spec, folded back into wiki-skills.

This is a high-level roadmap. Each improvement (P1–P10) is a **separate plan** with its own
brainstorm → design spec → implementation plan cycle. This document captures the backlog,
the dependency order, and the open design questions for each — it is not itself an
implementation plan.

## Status

| Plan | Title | Stage |
|------|-------|-------|
| P1 | Line-range provenance | ✅ spec + implementation plan written |
| P2 | Cross-model adversarial review | ✅ spec + implementation plan written |
| P3 | Concept identity | ✅ implemented (mechanical links + disambiguation + wiki-merge) |
| P4 | Frontmatter-driven auto-generated index | ✅ implemented (runtime-only index + bin/generate-index.py); unblocks P5, P7 |
| P5 | Adaptive / tiered index for scale | ⬜ roadmap only |
| P6 | Auto-generated logs + commit conventions | ✅ implemented (git history as log + bin/render-log.py; non-git log.md fallback; tests/) |
| P7 | Subdirectory / ontology structuring | ⬜ roadmap only |
| P8 | Ingest-time contradiction detection | ✅ implemented (gate, not annotation — transient `contradiction-check: failed` flag in wiki-ingest 7b; committed pages stay clean); unblocks P9 |
| P9 | Pre-commit gate | ✅ implemented (bin/check-contradictions.py + tracked bin/hooks/pre-commit via core.hooksPath; blocks staged pages carrying the flag; tests/) |
| P10 | Periodic lint backstop | ♻️ superseded — reframed as *scoped wiki-lint* (deterministic script + tag-cluster subagents); see `specs/2026-06-21-wiki-lint-subagent-scoping-design.md` |

## Dependency graph

```
P1 ──► P2          (provenance enables cheaper/located cross-model review)
P4 ──► P5          (auto-index must exist before it can be tiered/budgeted)
P4 ──► P7          (index generation shapes how subdirectories are discovered)
P8 ──► P9 ──► P10  (contradiction-check flag → pre-commit block → periodic backstop)
```

Independent roots: **P1**, **P3**, **P4**, **P6**, **P8**. Recommended build order follows
the dependency chains: P1 → P8 → P9 → P10 (the contradiction/commit pipeline), then P4 → P5
→ P7 (the index/scale chain), with P2, P3, P6 slotted against their roots.

---

## P2 — Cross-model adversarial review

**Goal:** The strong form of `wiki-lint` / `wiki-audit` runs the contradiction and
overreach check with a **second model from a different provider**, because self-review
under-catches. Warnings surface in lint output and page frontmatter.

**Approach sketch:** Add an opt-in "strong" mode to `wiki-audit` (and/or `wiki-lint`) that,
after the normal pass, dispatches the same claims to a different-provider model via the
agent/subagent mechanism, looking specifically for unsupported generalizations and
overreach. Disagreements between the two models become flagged findings.

**Depends on:** P1 (line-located claims make the adversarial pass cheaper and let it cite
exact lines when it disputes a claim).

**Touch points:** `skills/wiki-audit/SKILL.md`, possibly `skills/wiki-lint/SKILL.md`,
`SCHEMA.md` template (record review-model metadata).

**Open questions:**
- How is "a different provider" model invoked from within a Claude Code skill? (subagent
  with a model override, an external CLI like `codex`, or MCP?)
- Where do cross-model warnings live — audit report only, or also page frontmatter (e.g.
  `review: {model: ..., status: ...}`)?
- Is this a new mode flag on `wiki-audit`, or a separate `wiki-audit --strong` style entry?

---

## P3 — Concept identity

**Goal:** Stop `[[wikilink]]` hallucination and homonym collisions. Every concept gets a
stable identity separate from its display name; cross-links are validated against the
existing page set at write time, not invented at render time.

**Approach sketch:** Two complementary mechanisms (decide one or both during brainstorm):
(a) give each concept/entity page a stable `entity_id` in frontmatter, distinct from the
display title, with `merge` / `split` operations; (b) make cross-link creation mechanical
(title/slug matching, co-occurrence) rather than LLM-invented, so the link graph is
trustworthy by construction. Reviews/lint audit every `[[wikilink]]` resolves to a real page.

**Depends on:** nothing (independent root).

**Touch points:** `skills/wiki-init/SKILL.md` (frontmatter schema), `skills/wiki-ingest/SKILL.md`
(link creation discipline), `skills/wiki-lint/SKILL.md` (already checks broken links — extend
to identity/homonym), possibly new merge/split guidance.

**Open questions:**
- `entity_id` vs. mechanical-link-only — which, or both?
- What does `merge`/`split` look like as a skill operation, given no database?
- Is homonym handling worth it for a personal wiki, or YAGNI until proven needed?

---

## P4 — Frontmatter-driven auto-generated index

**Goal:** Eliminate the hand-maintained `wiki/index.md` as a source of truth. The index is
redundant with page frontmatter and creates merge conflicts in collaborative wikis. Generate
it from each page's frontmatter at runtime instead.

**Approach sketch:** Define a richer, parsable frontmatter (tags, category, one-line summary,
slug). A lightweight script regenerates `index.md` (or an in-memory equivalent) from
frontmatter on demand. Skills stop *editing* `index.md` and instead *generate* it; reads
become "generate then read."

**Depends on:** nothing (independent root). **Enables:** P5, P7.

**Touch points:** all six skills currently write to `index.md`; `SCHEMA.md` frontmatter spec;
a new generation script (Python or shell) plus how skills invoke it.

**Open questions:**
- Is the generated index a committed `index.md` (regenerated, diffable) or never committed
  (pure runtime artifact)? Trade-off: GitHub browsability vs. zero merge conflicts.
- What frontmatter fields are required to make generation lossless vs. today's hand-written
  one-line summaries?
- Does this break the existing "update index.md on every operation" convention everywhere?

---

## P5 — Adaptive / tiered index for scale

**Goal:** index-as-one-flat-file breaks past a few hundred pages (context overflow, slow
grep). Replace it with token-budgeted, progressively disclosed, intent-scoped index views.

**Approach sketch:** Tiered indexes — L0 (~200 tokens, always loaded), L1 (~1-2K, session
start), L2 (~2-5K, on demand) — and/or an adaptive generator that, given the user's
query/intent, emits only the subset of index entries likely relevant (driven by the rich
frontmatter from P4).

**Depends on:** P4 (must generate the index before tiering/budgeting it).

**Touch points:** `skills/wiki-query/SKILL.md` (today reads the whole `index.md` first), the
P4 generation script, `SCHEMA.md`.

**Open questions:**
- Adaptive subset-by-intent vs. fixed L0/L1/L2 tiers — or both?
- How is "potentially relevant" scored without embeddings — frontmatter tags + grep + slug
  match? (aligns with the "grep beat embeddings" thesis)
- At what page count does this activate? Keep flat index below ~100 pages.

---

## P6 — Auto-generated logs + commit conventions

**Goal:** `wiki/log.md` grows unbounded and confuses weaker models. Replace the
agent-maintained log with one derived from git history, and define wiki-specific commit
message conventions so the git log *is* the operation log.

**Approach sketch:** Stop appending to `log.md`. Define a commit-message convention (e.g.
`ingest: <title> | pages: <slugs>`) emitted by each skill when it commits. A script renders
a human log from `git log` on demand. Propose these conventions upstream to OKF.

**Depends on:** nothing (independent root). Pairs naturally with P9 (both are git-process work).

**Touch points:** every skill's "append to log.md" step (init/ingest/query/update/lint/audit);
`SCHEMA.md` "Log Entry Format"; a render script; assumes the wiki is a git repo.

**Open questions:**
- Hard dependency on git — what's the fallback for non-git wikis? (keep `log.md` as opt-in?)
- Exact commit-message grammar, and how strictly skills must follow it.
- Does removing `log.md` lose anything the git log can't reconstruct (e.g. query sessions
  that don't commit)?

---

## P7 — Subdirectory / ontology structuring

**Goal:** The current flat `wiki/pages/` (no subdirectories) is a hard rule today; it hurts
index generation and navigation at scale. Allow/encourage subdirectory structure organized
by high-level non-overlapping concepts, with ontology learning once the wiki grows large.

**Approach sketch:** Relax the flat-directory rule. At init, optionally divide pages among
top-level concepts. Past ~a few hundred pages, an ontology-learning pass proposes a
subdirectory taxonomy. Slugs/links must remain stable across moves.

**Depends on:** P4 (index generation must understand nested structure). Touches the most
load-bearing existing convention ("pages are flat — no subdirectories"), so highest
blast radius — schedule after P4/P5 prove the index can handle it.

**Touch points:** `skills/wiki-init/SKILL.md` (the flat-dir rule appears in multiple places),
all skills that resolve `wiki/pages/<slug>.md`, link resolution, `SCHEMA.md`.

**Open questions:**
- Does relaxing flat-dir break `[[slug]]` resolution (slugs are currently filename-only)?
- Is ontology learning in scope, or just "allow manual subdirectories"? (YAGNI check)
- How do existing flat wikis migrate, if at all?

---

## P8 — Ingest-time severity-graded contradiction detection

**Goal:** Move contradiction detection from the expensive whole-wiki lint pass to a cheap
per-source check at ingest, with machine-readable severity so commits can be gated.

**Approach sketch:** Every ingest audits only the pages it touched (not the whole repo) for
contradictions, classifying each as `none` / `soft` / `scope-mismatch` / `hard`. Soft and
scope are non-blocking (flagged, explained, watched). Hard contradictions stop the run, hold
the commit, and require manual resolution. Each flagged contradiction carries a
machine-readable token in frontmatter:
```
Contradiction severity: hard
Status: Unresolved — flagged for user review
```

**Depends on:** nothing (independent root). **Enables:** P9, P10.

**Touch points:** `skills/wiki-ingest/SKILL.md` (new per-source audit step), `SCHEMA.md`
(severity token + status convention), `skills/wiki-lint/SKILL.md` (P10 backstop reads these).

**Open questions:**
- Exact severity rubric — what makes a contradiction `hard` vs. `scope-mismatch`?
- Where does the token live — page frontmatter, a dedicated section, or a sidecar?
- What "watches" soft/scope contradictions so they don't quietly accumulate?

---

## P9 — Pre-commit gate

**Goal:** Deterministically block commits when a staged file carries an unresolved hard
contradiction — fast, no LLM, pure script.

**Approach sketch:** A git pre-commit hook runs a small Python script that scans staged files'
frontmatter for the literal `contradiction-check: failed` flag (written by P8's wiki-ingest
step 7b) and exits non-zero if any are found, naming them. Ships as an installable hook plus
setup guidance. Note: P8 already makes the *skill* refuse to commit while a flag is present,
so the hook is the deterministic backstop for the case where an agent or human stages a
flagged page anyway — on a healthy repo it never fires.

**Depends on:** P8 (the `contradiction-check: failed` flag it scans for) — and the
git-process work in P6 is a natural companion.

**Touch points:** a new `hooks/` or script directory, install instructions (likely in
`wiki-init` and/or README), `SCHEMA.md` reference.

**Open questions:**
- How is the hook installed and kept in sync across clones? (`core.hooksPath`, a setup
  command in `wiki-init`?)
- Python assumed available — acceptable dependency, or make it shell-only?
- Override path for intentional commits (e.g. `--no-verify` guidance)?

---

## P10 — Periodic lint backstop

**Goal:** Keep the whole-wiki lint pass, but make it cheap by loading only the pages already
flagged as contradicting — not the entire repository — so it stops nuking the context window
as the wiki grows.

**Approach sketch:** `wiki-lint`'s contradiction check becomes a backstop for the conflicts
P8 does *not* catch — soft tensions (P8 surfaces but never records) and conflicts with
distant pages outside an ingest's touched neighborhood. **Note:** P8 shipped as a gate that
persists nothing (committed pages are always clean), so the original "read only pages
carrying a `Status:` token" premise no longer holds — there are no persisted tokens to read.
This plan needs a re-brainstorm: the backstop must rescope around what P8 leaves behind
(neighbor-scoped + soft), not around persisted severity tokens.

**Depends on:** P8 (defines what it must back-stop), P9 (gate keeps hard conflicts out of
commits).

**Touch points:** `skills/wiki-lint/SKILL.md` (contradiction check section).

**Resolution (2026-06-21):** superseded. The "read pages carrying a persisted severity
token" premise died with P8 (which persists nothing). The re-brainstorm reframed the whole
problem as **scoped wiki-lint**: the deterministic checks move to a two-mode
`bin/lint-mechanical.py` (full-wiki JSON sweep + `--staged` pre-commit gate), and
contradiction / missing-xref / merge detection becomes **tag-cluster subagents** whose page
bodies never enter the main context — approach A (tag clustering) now, with a seam to
claim-digest map-reduce (approach C) later. The whole-wiki contradiction sweep does *not*
remain as a deep mode; cluster-scoped passes accumulate coverage across periodic runs.
See `specs/2026-06-21-wiki-lint-subagent-scoping-design.md` (implemented). Original open
questions are obsolete: there are no persisted soft/scope flags to age out.

---

## How to use this roadmap

Pick the next plan by dependency order, then run its full cycle:
1. `superpowers:brainstorming` — resolve that plan's open questions into decisions.
2. Write the design spec → `docs/superpowers/specs/YYYY-MM-DD-<plan>-design.md`.
3. `superpowers:writing-plans` — produce the task-by-task implementation plan →
   `docs/superpowers/plans/YYYY-MM-DD-<plan>.md`.
4. Execute. Update the Status table above.

Recommended next: **P8** (independent root that unblocks the P9→P10 chain), or **P2** (builds
directly on the just-specced P1).
