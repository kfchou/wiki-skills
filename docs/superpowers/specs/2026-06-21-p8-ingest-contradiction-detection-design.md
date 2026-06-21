# P8 — Ingest-time contradiction detection

**Status:** Approved (design)
**Date:** 2026-06-21
**Part of:** wiki-skills improvement backlog (plan 8 of 10, dependency order). Independent
root; unblocks P9 (pre-commit gate), which consumes the transient blocker flag defined here.

## Goal

Catch contradictions at the moment a source is ingested — cheaply, while the ingesting
agent already has the new pages and their neighbors in context — and prevent a commit that
would introduce a real factual conflict into the wiki. The check is a **gate**, not an
annotation: every page that lands in git is clean.

## Core principle: committed pages are always clean

Contradiction state is **never persistent metadata**. It exists only as a transient blocker
flag in the working tree, between the moment a blocking contradiction is detected and the
moment it is resolved. Once resolved, the flag is removed and the commit proceeds. A page
committed to git never carries contradiction metadata of any kind — there is no severity
history, no `passed` stamp, nothing. Absence of the flag is the only "clean" state.

## Decisions

- **Inline self-check, no dispatch.** The check is a new sub-step of `wiki-ingest`, run by
  the ingesting agent itself against pages it has already read in-context. No subagent, no
  cross-model call, no provider dependency. The strong cross-model pass already exists on
  demand as `wiki-audit strong` and is not duplicated here.
- **Scope: internal + cross-page against touched neighbors only.** The check compares the
  pages this ingest wrote/edited against (a) themselves (internal contradictions) and
  (b) the pages already read during this ingest — the entity/concept pages from step 6 and
  the neighbor pages from the step 7 backlink audit. It does **not** re-read the whole wiki.
  A conflict with a distant page this ingest never touched is the job of the periodic
  `wiki-lint` sweep.
- **Binary gate, not a severity rubric.** A contradiction is either **blocking** (a real
  factual conflict — incompatible dates, counts, names, or mutually-exclusive claims on the
  same entity under the same scope) or it is not. Blocking conflicts hold the commit.
  Everything else does not.
- **Transient blocker flag.** When a blocking contradiction is found, write a single
  frontmatter line to the affected page and stop before the commit step:
  ```yaml
  contradiction-check: failed — <one-line reason>
  ```
  This is the machine-readable handoff to P9. It is removed once the conflict is resolved;
  it is never committed.
- **Nothing persisted on clean pages.** No `contradiction-check: passed` stamp, no token.
  Absence = clean.
- **Soft tensions are surfaced, not recorded.** A "soft" tension that is not a true conflict
  (differing emphasis, values within plausible version/measurement variance, claims that
  hold under different scope) is mentioned in the ingest's conversational summary so the user
  can act if they wish — but persists nothing and never blocks. The periodic `wiki-lint`
  sweep remains the backstop for anything skipped.

## The blocker flag

A single line in the affected page's frontmatter, written **only** while a blocking
contradiction is unresolved:

```yaml
contradiction-check: failed — model launch year conflicts with [[that-model]] (2024 vs 2023)
```

- The machine-readable token is the literal substring `contradiction-check: failed`. P9's
  gate greps staged page frontmatter for it and refuses the commit.
- The text after `—` is a human-readable one-line reason; it names the counterpart
  `[[slug]]` for a cross-page conflict, or says `internal` for a within-page one. It carries
  enough detail to resolve the conflict without re-deriving it (useful if the session is
  interrupted and resumed).
- Stamped on the page this ingest wrote or edited that carries the newer claim, so it is
  always part of the ingest's working set.
- `bin/generate-index.py` reads only `category`, `summary`, and `created`, so this line is
  ignored by index generation — no script change is required for P8.

## Blocking behavior (P8)

When step 7b finds a **blocking** contradiction:

1. Write the `contradiction-check: failed — <reason>` line to the affected page.
2. **Stop before the commit step (step 10)** — do not suggest a commit.
3. Surface the conflict (both claims, both locations) and offer resolutions:
   - correct the newly-written page,
   - correct the counterpart page,
   - reconcile both with a scope qualifier,
   - or confirm it is not actually a conflict (downgrade — it was a soft tension).
4. On resolution, **remove the `contradiction-check` line** from the page.
5. Only once no `contradiction-check: failed` line remains on any touched page does the
   ingest proceed to the commit step.

Soft tensions never reach this flow — they are mentioned in the summary and the ingest
proceeds normally.

## Relationship to P9 (defense in depth)

P8 gives two layers for the same signal:
- **Skill-level hold** — `wiki-ingest` will not suggest a commit while a flag is present.
- **Script-level gate (P9)** — a deterministic pre-commit hook greps staged files for
  `contradiction-check: failed` and rejects the commit, catching the case where an agent or
  a human stages a flagged page anyway.

P8 defines and writes the flag; P9 builds the deterministic scanner. By design, a committed
page never carries the flag, so on a healthy repo P9 never fires.

## Touch points

1. **`wiki-init` SCHEMA.md template** — add a short **"Contradiction Check"** section (the
   canonical reference, alongside Citations and Cross-Model Review): the gate principle
   (committed pages are clean), the blocking-vs-soft distinction, the neighbor-only scope,
   the transient `contradiction-check: failed` flag and that it must be removed before
   commit. Add a one-line note to the Conventions list.
2. **`wiki-ingest`** — new `### 7b. Contradiction check — do not skip`, placed after the
   step 7 backlink audit and before step 8 (index regeneration). Wire the hold into step 10
   (Record the operation): do not suggest a commit while any `contradiction-check: failed`
   line is present on a touched page. Mention soft tensions in the step 11 report.

`wiki-lint` is **not** touched by P8 — its existing whole-wiki contradiction sweep is
unchanged and remains the backstop for soft/distant conflicts.

## Out of scope

- **P9** — the deterministic pre-commit hook/script that enforces the flag. P8 only defines
  and writes the flag and the skill-level hold.
- **P10** — the lint backstop refactor.
- **`wiki-audit`** — its on-demand cross-model adversarial pass is unchanged.
- Persistent contradiction history, severity grading, or any `passed` stamp — explicitly
  rejected: committed pages stay clean.
- Whole-wiki contradiction scanning at ingest time — P8 is deliberately neighbor-scoped.
