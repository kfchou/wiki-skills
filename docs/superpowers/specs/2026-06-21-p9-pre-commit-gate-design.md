# P9 — Pre-commit gate

**Status:** Approved (design)
**Date:** 2026-06-21
**Part of:** wiki-skills improvement backlog (plan 9 of 10, dependency order). Depends on P8
(scans for the `contradiction-check: failed` flag P8 writes); pairs with P6 (git process).

## Goal

Deterministically block a commit that would land a wiki page still carrying an unresolved
contradiction flag — fast, no LLM, pure script. P8 already makes the *skill* refuse to
commit while a flag is present; P9 is the deterministic backstop for the case where an agent
or human stages a flagged page anyway. On a healthy repo it never fires.

## Decisions

- **Two new files, written by `wiki-init` into each git wiki:**
  - `bin/check-contradictions.py` — stdlib-only Python checker, alongside the existing
    `bin/generate-index.py` and `bin/render-log.py`. Its canonical source is the fenced
    `python` block in `wiki-init/SKILL.md`, so the `tests/` harness extracts and tests it
    exactly like the other two.
  - `bin/hooks/pre-commit` — a tracked, executable shell hook that runs the checker via
    `uv run`.
- **Install via `core.hooksPath`.** `wiki-init` runs `git config core.hooksPath bin/hooks`
  for git wikis. The hook is tracked (committed), but `core.hooksPath` is repo-local config
  and does **not** survive a fresh clone — so the one-liner is documented for re-running.
  There is no fully-automatic cross-clone hook in git; this is the standard trade.
- **Python via `uv`.** The hook shebang delegates to `uv run`, which guarantees an
  interpreter even if system Python is absent. The checker itself stays plain stdlib so the
  `tests/` harness can run it under the system interpreter.
- **Scan staged blobs, frontmatter-only, `wiki/pages/` only.** The checker reads the
  **staged** content (`git show :<path>`), not the working tree — a hook must gate what is
  actually being committed. It parses only the frontmatter block and only considers files
  under `wiki/pages/*.md` (excluding `audit-*`). This is the false-positive guard: prose
  mentions of the literal `contradiction-check: failed` (in SKILLs, specs, this roadmap)
  never trip it.
- **Git-only.** Non-git wikis get no hook, consistent with P6's git-only stance. The checker
  no-ops (exits 0) outside a git work tree.
- **Override:** `git commit --no-verify`, documented in SCHEMA.md.

## The checker — `bin/check-contradictions.py`

Behavior:
1. If not inside a git work tree, return (exit 0) — nothing to gate.
2. List staged (`--diff-filter=ACM`) files under `wiki/pages/*.md`, excluding `audit-*`.
3. For each, read the staged blob (`git show :<path>`), parse the frontmatter block, and
   look for a line whose key is `contradiction-check` and whose value starts with `failed`.
4. If any are found, print each offending page and its reason to stderr, with the fix
   (resolve the conflict and remove the line; see `wiki-ingest` step 7b) and the
   `--no-verify` override, then exit `1`. Otherwise exit `0`.

Frontmatter parsing reuses the same manual line-scan idiom as `generate-index.py` (leading
`---` … `---`, split on the first `:`) — no third-party YAML dependency.

## The hook — `bin/hooks/pre-commit`

```sh
#!/bin/sh
# Wiki pre-commit gate (P9): block commits that stage a page still flagged with an
# unresolved contradiction. See bin/check-contradictions.py. Override: git commit --no-verify.
exec uv run "$(git rev-parse --show-toplevel)/bin/check-contradictions.py"
```

## Touch points

1. **`wiki-init` §4 (bin scripts)** — add the `check-contradictions.py` block (update the
   "two helper scripts" wording to three) and the `bin/hooks/pre-commit` block.
2. **`wiki-init` §5 (operation log / git setup)** — in the git-repo branch, install the
   gate: `chmod +x bin/hooks/pre-commit && git config core.hooksPath bin/hooks`, and note
   the hook is committed while the config line must be re-run after a fresh clone.
3. **`wiki-init` SCHEMA template** — add a short **"Pre-commit Gate"** section: what it
   blocks, the fresh-clone one-liner, and the `--no-verify` escape hatch; plus a Conventions
   line.
4. **`tests/`** — `test_check_contradictions.py` (extract-and-run, like the others) plus a
   `check-contradictions` signature in `_harness._SIGNATURES`. Cases: flag in staged
   frontmatter → exit 1; clean page → 0; token only in body prose → 0 (guard); token in a
   non-`pages/` file → ignored; not a git repo → 0.

## Out of scope

- **P10** — the lint backstop.
- Changing how **P8** writes or removes the flag.
- Hooks for non-git wikis.
