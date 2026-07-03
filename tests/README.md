# Tests

Unit tests for the wiki helper scripts that `wiki-init` writes into every wiki.

These scripts are standalone files bundled with the skill at
`skills/wiki-init/assets/bin/` — exactly the files `wiki-init` copies into a wiki's `bin/`.
The tests **install those files** (via `_harness.install_script`) and exercise them, so they
validate what actually ships. If you edit a script under `assets/bin/`, rerun these tests.

## Running

Standard library only — no dependencies, no install:

```sh
python3 -m unittest discover -s tests
```

(`pytest tests` also works — the tests are plain `unittest.TestCase` classes.)

## Coverage

- `test_generate_index.py` — `bin/generate-index.py` (P4): category ordering, audit-report
  skipping, the `Uncategorized` bucket, newest-first-by-`created` sort, and skipping pages
  with no frontmatter.
- `test_render_log.py` — `bin/render-log.py` (P6): rendering `Wiki-Op:` commits grouped by
  date, ignoring commits without the trailer, excluding gitignored audit pages, and the
  non-git exit path.
- `test_check_contradictions.py` — `bin/check-contradictions.py` (P9): blocking staged pages
  carrying the `contradiction-check: failed` flag, ignoring the flag in body prose, ignoring
  unstaged flags and pages outside `wiki/pages/`, excluding audit reports, and the non-git
  no-op path.
- `test_lint_mechanical.py` — `bin/lint-mechanical.py` (scoped wiki-lint): full-mode checks
  (missing frontmatter, broken links, orphans, slug collisions, stale-date, missing-concept),
  tag clustering (singleton skip, subset dedup, oversized-cluster split), and the `--staged`
  pre-commit gate (blocks structural problems in staged blobs; no-ops outside git).
