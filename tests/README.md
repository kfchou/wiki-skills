# Tests

Unit tests for the wiki helper scripts that `wiki-init` writes into every wiki.

These scripts have no standalone source file in this repo — their canonical source is the
fenced ```python block inside `skills/wiki-init/SKILL.md`, since that is exactly what
`wiki-init` writes into a wiki's `bin/`. The tests **extract those blocks** (via
`_harness.extract_script`) and exercise them, so they validate what actually ships. If you
edit a script in the SKILL, rerun these tests.

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
