---
name: wiki-merge
description: Use when two wiki pages turn out to be the same concept under different slugs (merge), or one page overloads several distinct senses of a term and should be separated into qualified slugs (split). Often run on a wiki-lint "merge candidate" or "colliding slug" finding.
---

# Wiki Merge

Consolidate two pages into one (**merge**), or separate one overloaded page into
qualified pages (**split**). Both operations rewrite the link graph, so they are
deliberate, confirmed, and verified — never automatic.

The slug is the concept's identity (see the **Concept Identity** section of `SCHEMA.md`).
Merge and split are how identity changes safely: every inbound `[[slug]]` is rewritten so
no link is left resolving to nothing.

## Pre-condition

Find `SCHEMA.md` (search from cwd upward, or `~/wikis/`). If not found, tell the user to
run `wiki-init` first. Read it to get the wiki root path and the Concept Identity
convention.

## Choose the operation

- **Merge** — two slugs name the same concept. Goal: one surviving page, the other gone,
  all links pointing at the survivor.
- **Split** — one slug overloads distinct senses (a homonym, or a page that grew two
  unrelated subjects). Goal: two qualified pages, each inbound link repointed to the
  correct sense.

If unsure which, describe both pages to the user and confirm before proceeding.

---

## Merge

### 1. Identify survivor and loser

Present both pages and recommend which slug survives. Prefer the slug that is: more
specific and correct, more linked-to, or already the better-developed page. Confirm the
choice with the user before writing anything.

> **Survivor:** `[[<survivor-slug>]]` — <why>
> **Loser:** `[[<loser-slug>]]` — folded in, then deleted

### 2. Fold content into the survivor

Read both pages in full. Merge the loser's content into the survivor:
- Combine sections; do not duplicate facts already present.
- **Preserve every citation.** Carry footnotes over, renumbering sequentially. Never drop
  a footnote during the fold — a merged claim keeps its provenance.
- Union the frontmatter `sources` lists; keep the broader/more-correct `title`,
  `category`, `summary`, and `tags`.
- Keep the **earlier** `created` date of the two; bump the survivor's `updated` date.

Show the proposed survivor page as a diff and confirm before writing.

### 3. Rewrite all inbound links

Grep every page in `wiki/pages/` and `overview.md` for `[[<loser-slug>]]` (skip
`index.md` — it is generated and will be rebuilt). Rewrite each to `[[<survivor-slug>]]`.
Watch for:
- A page that linked to *both* — collapse to a single link, fix surrounding prose.
- Link text/aliases that named the loser — update the wording to read naturally.

Show the list of affected pages and the edits; confirm before writing.

### 4. Delete the loser page and regenerate the index

Remove `wiki/pages/<loser-slug>.md`. Do not touch `index.md` by hand — regenerate it so
the loser's entry disappears and the survivor's reflects its merged frontmatter:
`python bin/generate-index.py`.

### 5. Link-resolution sweep

Grep the whole wiki for `[[<loser-slug>]]` — there must be **zero** matches left. Then
confirm every `[[slug]]` on the survivor page resolves to a real page. Fix any stragglers
before finishing. (This is the same inline check `wiki-ingest` runs; a merge that leaves a
dangling link defeats its own purpose.)

### 6. Update overview and record the operation

If the merge changes the synthesis (e.g. a duplicated "Key Concept" becomes one), update
`wiki/overview.md`. Then record the operation per SCHEMA's **Operation Log & Commit
Convention**:
- **Git wiki:** suggest a commit (default `refactor:` for a merge, plus the trailer) and
  commit on confirmation.
  ```
  refactor: merge <loser-slug> into <survivor-slug>

  Wiki-Op: merge
  ```
- **Non-git wiki:** append to `wiki/log.md`:
  ```
  ## [<today>] merge | <loser-slug> → <survivor-slug>
  Inbound links rewritten: <N> across <list of pages>
  ```

---

## Split

### 1. Define the senses and slugs

Identify each distinct sense the overloaded page conflates. Propose a qualified slug per
sense, following the disambiguation convention in `SCHEMA.md` (narrowest discriminator
that disambiguates):

> `[[transformer]]` overloads two senses →
> - `[[transformer-ml]]` — the neural network architecture
> - `[[transformer-electrical]]` — the power-grid device

Decide what happens to the original bare slug:
- **Retire it** (most common): both senses move to qualified slugs; the bare slug is
  deleted and every inbound link repointed.
- **Keep it as the primary sense**: one sense stays on the bare slug, the other moves out.

Confirm the slug plan with the user before writing.

### 2. Create the qualified pages

Write each new page with the content for its sense only, with full frontmatter
(`title`, `category`, a distinct one-line `summary`, `tags`, `created: <today>`,
`updated: <today>`). Split the frontmatter `sources` so each page lists only the sources
that actually support it. Carry the relevant footnotes to each page, renumbering
sequentially. Show each new page and confirm before writing.

### 3. Repoint inbound links per sense

Grep every page in `wiki/pages/` and `overview.md` for `[[<original-slug>]]` (skip the
generated `index.md`). For **each** occurrence, decide which sense it meant from its
context and rewrite it to the correct qualified slug. This is the judgment-heavy step —
do not blanket-replace. When a single page referenced both senses, split it into two links.

Show each repointing decision (link, surrounding context, chosen target) and confirm
before writing.

### 4. Remove or repurpose the original

If retiring the bare slug, delete `wiki/pages/<original-slug>.md`. If keeping it as the
primary sense, trim it to that sense only and bump its `updated` date. Then regenerate the
index so the removed/added pages are reflected — do not hand-edit `index.md`:
`python bin/generate-index.py`.

### 5. Link-resolution sweep

If the bare slug was retired, grep the whole wiki for `[[<original-slug>]]` — zero matches
must remain. Confirm every `[[slug]]` on the new pages resolves. Fix any stragglers.

### 6. Update overview and record the operation

Update `wiki/overview.md` if the split changes the synthesis. Then record the operation
per SCHEMA's **Operation Log & Commit Convention**:
- **Git wiki:** suggest a commit (default `refactor:` for a split, plus the trailer) and
  commit on confirmation.
  ```
  refactor: split <original-slug> into <slug-a>, <slug-b>

  Wiki-Op: split
  ```
- **Non-git wiki:** append to `wiki/log.md`:
  ```
  ## [<today>] split | <original-slug> → <slug-a>, <slug-b>
  Inbound links repointed: <N> across <list of pages>
  ```

---

## Common Mistakes

- **Leaving dangling links** — The whole point is a trustworthy graph. After any merge or
  split, grep for the removed slug; zero matches is the only acceptable result.
- **Dropping citations during a fold** — Every claim keeps its footnote. Renumber, don't
  delete. A merge that loses provenance is a regression.
- **Blanket-replacing on a split** — Each inbound link must be repointed by *meaning*, not
  by find-and-replace. That per-link judgment is the reason split is a deliberate skill.
- **Merging without confirmation** — Merge deletes a page and rewrites links across the
  wiki. Always show the plan and the diffs, and write only after the user confirms.
- **Skipping the log** — Record the operation so the slug change is traceable: a git wiki
  commits it (with the `Wiki-Op:` trailer); a non-git wiki appends to `log.md`.
