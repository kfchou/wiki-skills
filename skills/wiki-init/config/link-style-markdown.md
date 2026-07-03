# Link Style: Markdown

This file defines how cross-references and citation targets are written and parsed for wikis configured with `link_style: markdown` in `SCHEMA.md`. Use this style when the wiki will be browsed primarily on GitHub, in VS Code's default markdown preview, in a static-site generator, or in any plain markdown-to-HTML pipeline.

## Emit

Use `[[slug](pages/slug.md)]` for every cross-reference and every citation target — a standard markdown link wrapped in outer brackets. The display text is the slug verbatim. The outer brackets preserve the visual `[slug]` cue from Obsidian; the inner link is what GitHub and other plain-markdown renderers will make clickable.

The same form is used in body prose, in index/list entries, and inside citation footnotes.

Examples:

- Body cross-reference: `see [[transformer-architecture](pages/transformer-architecture.md)] for details`
- Index entry: `- [[transformer-architecture](pages/transformer-architecture.md)] — overview`
- Citation footnote: `[^1]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2 — "We employ h = 8 parallel attention layers"`

The link path is always relative to the page emitting the link. Pages live flat in `wiki/pages/`, so a link from one page to another resolves as `pages/<slug>.md` from the perspective of any page in `wiki/pages/` (the directory is the same). For pages outside `wiki/pages/` (e.g. `wiki/index.md`, `wiki/overview.md`), the same `pages/<slug>.md` path resolves correctly because those files are one level above `pages/`.

Drive-by citations (paths under `raw/` or `assets/`, and bare URLs) are unchanged by link style — they are not slug references.

## Parse

To find slug references in any wiki page, match either pattern (a wiki may legitimately contain both forms if a user has hand-edited content or imported pages):

```
\[\[([a-z0-9-]+)\]\]                                  (legacy / hand-edited obsidian form)
\[\[([a-z0-9-]+)\]\(pages/\1\.md\)\]                  (markdown form)
```

The captured group is the slug. Resolve to `wiki/pages/<slug>.md`.

Reading is permissive (both patterns); writing is strict (only the markdown form).
