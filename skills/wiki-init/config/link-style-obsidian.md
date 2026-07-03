# Link Style: Obsidian

This file defines how cross-references and citation targets are written and parsed for wikis configured with `link_style: obsidian` in `SCHEMA.md`. Use this style when the wiki will be browsed primarily in Obsidian or another `[[wiki-link]]`-aware viewer.

## Emit

Use `[[slug]]` for every cross-reference and every citation target, where slug is the page's filename without `.md`. The same form is used in body prose, in index/list entries, and inside citation footnotes.

Examples:

- Body cross-reference: `see [[transformer-architecture]] for details`
- Index entry: `- [[transformer-architecture]] — overview`
- Citation footnote: `[^1]: [[attention-is-all-you-need]] §3.2 — "We employ h = 8 parallel attention layers"`

Drive-by citations (paths under `raw/` or `assets/`, and bare URLs) are unchanged by link style — they are not slug references.

## Parse

To find slug references in any wiki page, match:

```
\[\[([a-z0-9-]+)\]\]
```

The captured group is the slug. Resolve to `wiki/pages/<slug>.md`.
