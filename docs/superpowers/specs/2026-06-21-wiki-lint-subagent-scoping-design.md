# P10 (reframed) — Scoped wiki-lint: deterministic script + tag-cluster contradiction subagents

**Status:** Approved (design)
**Date:** 2026-06-21
**Part of:** wiki-skills improvement backlog. Supersedes the original P10 ("read pages
carrying a persisted severity token"), whose premise died when P8 shipped as a gate that
persists nothing. Depends on P3 (tags/concept identity), P4 (`generate-index.py` frontmatter
parsing), P8/P9 (the pre-commit hook this extends). Builds on the 2026-06-21 refactor that
moved the `bin/` helper scripts to standalone files at `skills/wiki-init/assets/bin/`.

## Problem

`wiki-lint` runs one whole-wiki LLM pass: it loads `index.md`, `overview.md`, and **every
page body** into a single context, then checks all categories (contradictions, orphans,
broken links, stale claims, slug collisions, coverage gaps). This nukes the context window as
the wiki grows — the original P10 concern — and most of the checks don't need an LLM at all.

The hard part is contradiction detection: it's inherently cross-page (a contradiction is a
*pair* of conflicting claims), so it resists naive partitioning. A subagent that sees only a
subset of pages cannot, by construction, find a contradiction with a page it never saw.

## Decisions

- **Restructure `wiki-lint` into a four-phase pipeline.** The main thread never holds page
  bodies — bodies live only inside a script (Phase 1) or inside a subagent that is discarded
  (Phase 2).
  - **Phase 0** — regenerate the index (existing `bin/generate-index.py`).
  - **Phase 1** — deterministic checks via a new `bin/lint-mechanical.py` (zero LLM).
  - **Phase 2** — contradiction + missing-cross-reference sweep via tag-cluster subagents.
  - **Phase 3** — assemble the existing severity-tiered `lint-<date>.md` report, run the
    tiny coverage-gaps step, offer fixes, log.
- **Approach A now, C later.** Phase 2 groups pages into clusters and checks each in an
  isolated subagent (approach **A**, tag clustering). Recall is capped by clustering quality;
  the design leaves an explicit seam to upgrade to claim-digest map-reduce (approach **C**)
  if recall disappoints at scale. The swappable part is the subagent's return payload (see
  *The C-later seam*).
- **`lint-mechanical.py` has two modes** — a full-wiki sweep and a staged-files pre-commit
  gate — because the deterministic checks are valuable both periodically and at commit time.
- **The staged gate blocks on every structural finding** (exit non-zero), consistent with the
  P9 contradiction gate. Override: `git commit --no-verify`.
- **Stdlib-only, bundled, copied at init** — `lint-mechanical.py` joins the other three
  scripts at `skills/wiki-init/assets/bin/`, copied verbatim into each wiki's `bin/` by
  `wiki-init`, and tested by `tests/` against the real file (no markdown extraction).

## Phase 1 — `bin/lint-mechanical.py` (deterministic checks)

Builds the link graph and frontmatter table once (reusing `generate-index.py`'s manual
frontmatter parser — leading `---` … `---`, split on first `:`, no YAML dep), then runs the
deterministic checks. `overview.md` is exempt from page checks; `audit-*.md` are excluded.

### Two modes

```
python bin/lint-mechanical.py            # full mode  → JSON to stdout, all checks, whole wiki
python bin/lint-mechanical.py --staged   # staged mode → human text + exit code, staged files only
```

Some checks are inherently global, so the modes run different subsets:

| Check | Staged | Full | Severity | Notes |
|---|:---:|:---:|---|---|
| Missing frontmatter | ✅ | ✅ | 🔴 | Per-file: required `title/category/summary/tags/sources/created/updated` |
| Slug collision | ✅ | ✅ | 🟡 | Bare slug sharing its token with a qualified one (`mercury` vs `mercury-element`); flag the pair, never rename |
| Broken links (outgoing) | ✅ | ✅ | 🔴 | A page's `[[refs]]` that resolve to no `wiki/pages/<slug>.md` |
| Orphans | ❌ | ✅ | 🟡 | Zero inbound `[[slug]]` links — global; a new page is legitimately orphaned until linked |
| Missing-concept | ❌ | ✅ | 🔵 | A `[[slug]]` referenced 3+ times that resolves to no page — needs a global ref count |
| Stale-date | ❌ | ✅ | 🟡 | `updated` >90d ago AND body matches `current/latest/recent/state-of-the-art` or a year literal ≥2y old |

### Mode behavior

- **Full mode** — runs all six checks over every page; emits a structured JSON object
  (findings grouped by check, each carrying page slug + detail) to stdout. `wiki-lint`
  Phase 1 consumes it.
- **Staged mode** — operates on `git diff --cached --name-only --diff-filter=ACM` for
  `wiki/pages/*.md` (excluding `audit-*`), reading the **staged blob** (`git show :<path>`),
  not the working tree — same discipline as `check-contradictions.py`. Runs the three
  per-file/resolvable checks (missing frontmatter, slug collision, broken links). Broken-link
  and slug-collision resolution use the global slug set read from disk. Prints human-readable
  findings to stderr and **exits non-zero if any are found** (block everything); otherwise
  exits 0. No-ops (exit 0) outside a git work tree.

## Phase 2 — tag-cluster contradiction subagents

### Clustering (deterministic, emitted by `lint-mechanical.py` full mode)

Full-mode JSON carries a `clusters` field (list of clusters, each a list of page slugs)
alongside the deterministic findings, so `wiki-lint` gets both from a single call. Rules:


- Build `tag → pages` from frontmatter. Each tag with **≥2 pages** is a cluster; singleton
  tags are skipped (one page cannot self-contradict).
- **Subset dedup:** if cluster A's page set ⊆ cluster B's, drop A. Identical sets collapse.
- **Large-cluster cap:** if a cluster exceeds a page/token budget, deterministically
  sub-split it (secondary tag, else alphabetical chunks) and **mark in the report that the
  cluster was split** — split chunks can't see each other, so recall drops there. This is
  approach A's known scale tail; honesty in the report is the mitigation, and approach C
  removes it.
- A page in K tags joins K clusters and is checked K times — accepted redundancy that lifts
  recall (a conflict surfaces if two pages share *any* tag).

### Subagent contract (one per cluster, parallel fan-out, batched)

- **In:** the cluster's page paths + wiki root + instructions to find, *within these pages
  only*: (1) contradictions (same entity, conflicting dates/counts/names/relationships) and
  (2) missing cross-references (two pages clearly about the same entity with no `[[link]]`
  between them). The subagent reads the bodies, so they live in **its** context.
- **Out:** a compact structured list — per finding: `type` (`contradiction` |
  `missing-xref`), the two slugs, the entity, a one-line description — or `clean`. **No page
  bodies return.**
- **Isolation:** a subagent sees only its cluster, so it finds only within-cluster relations
  — the accepted recall limit of approach A.
- Dispatch parallel (consistent with `wiki-audit`'s subagent-per-source), batched to bound
  concurrency on large wikis. The "clear context between threads" goal holds regardless:
  bodies never enter the main context; only findings do.

### Aggregation

The main thread merges all subagent findings and **dedups** on
`(type, sorted(slugA, slugB), entity)` — necessary because a page in K clusters can surface
the same finding more than once. The deduped list goes to Phase 3.

### The C-later seam

Phase 2's stable shape is *partition → fan-out subagents → aggregate*. The **single swappable
part is the subagent's return payload.** Today it returns "findings within my cluster." To
upgrade to approach C (claim-digest map-reduce), the subagent instead returns a claim digest
(`entity → asserted facts (+ source page)`) for its slice, and one reduce pass diffs all
digests globally to catch cross-cluster conflicts. Clustering, the fan-out harness, and
report assembly are unchanged by that swap.

## Phase 3 — report assembly

Merge Phase 1 JSON findings + Phase 2 deduped findings into the existing severity-tiered
`wiki/pages/lint-<date>.md` format. Run the small coverage-gaps step (reads only
`overview.md`, in the main thread). Add a caveat line whenever any cluster was split. Offer
concrete fixes and log — unchanged from today's skill.

## Pre-commit hook wiring

`bin/hooks/pre-commit` runs **both** deterministic gates, chained:

```sh
#!/bin/sh
ROOT="$(git rev-parse --show-toplevel)"
uv run "$ROOT/bin/check-contradictions.py" || exit 1
uv run "$ROOT/bin/lint-mechanical.py" --staged || exit 1
```

(Not `exec uv run … && …` — `exec` replaces the shell with the first command, so a chained
second command after it would never run. A plain sequence with `|| exit 1` gates on both.)

`check-contradictions.py` (P9 contradiction-flag gate) and `lint-mechanical.py --staged`
(structural validity) are separate single-responsibility scripts; the hook just chains them.
Both deterministic, no LLM. Override either with `git commit --no-verify`.

## Activation / graceful degradation

No page-count threshold to tune. Phase 1 always runs (cheap). Phase 2 falls out of the
clustering: a small wiki where pages share one tag yields a single cluster → one subagent
over all pages (= today's behavior, still isolated from the main context); a large wiki
yields many small clusters. Behavior scales smoothly from "one pass" to "many scoped passes."

## Touch points

1. **New** `skills/wiki-init/assets/bin/lint-mechanical.py` — the two-mode deterministic
   checker + clustering output.
2. **New** `tests/test_lint_mechanical.py` — installs the real file via
   `_harness.install_script` and exercises it.
3. **Rewrite** `skills/wiki-lint/SKILL.md` around the four-phase pipeline.
4. **`skills/wiki-init/SKILL.md`** — §4 copy step gains a `lint-mechanical.py` line; update
   the dir-tree diagram and the bundled-script descriptions; §5 hook now chains both gates.
5. **`wiki-init` SCHEMA template** — note the staged gate (what it blocks, `--no-verify`
   override) alongside the existing Pre-commit Gate section.
6. **Roadmap** — mark the original P10 superseded by this design.

## Testing

- **`lint-mechanical.py` full mode** — unit tests (fixtures → assert JSON findings), one per
  check plus edges (`overview.md` exempt, `audit-*` excluded, no-frontmatter page handling).
  Deterministic.
- **`lint-mechanical.py --staged`** — git-fixture tests like `test_check_contradictions.py`:
  staged page with missing frontmatter / colliding slug / broken link → exit 1; clean staged
  page → 0; not a git repo → 0; finding only in an unstaged page → ignored.
- **Clustering + aggregation dedup** — unit tests for tag grouping, singleton skip, subset
  dedup, large-cluster split, and the `(type, slugs, entity)` dedup, with stub findings.
  Deterministic.
- **Subagent contradiction-finding itself** — LLM behavior, *not* unit-testable. Validated by
  (a) a fixed return schema the harness asserts against and (b) a small fixture wiki with
  planted contradictions for manual/integration verification. Stated plainly rather than
  pretended to be unit-covered.

## Out of scope

- **Approach C** (claim-digest map-reduce) — only the seam is built now.
- **P5 / P7** (tiered index, subdirectories) — the broader index/scale chain.
- Changing how **P8/P9** write or gate the `contradiction-check` flag.
- Hooks for non-git wikis (the staged gate, like the P9 gate, is git-only).
- The coverage-gaps check's heuristics — it stays as-is, just relocated to Phase 3.
