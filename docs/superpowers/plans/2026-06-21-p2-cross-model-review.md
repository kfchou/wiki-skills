# P2 — Cross-model Adversarial Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in `wiki-audit strong` mode whose new Phase C runs a different-provider model over the page's P1-located claim excerpts to catch overreach and contradiction, surfacing disagreements as findings, recording a committed `review:` frontmatter token, and writing the verbose findings to a now-gitignored local report.

**Architecture:** Prose SKILL.md edits, no application code. `wiki-init` gains a generated `.gitignore` (audit reports are local-only) and documents the `review:` token in the `SCHEMA.md` it writes. `wiki-audit` gains strong-mode arg parsing, a provider-detection chain (`codex` → `gemini` → Claude-subagent fallback), Phase C itself, a frontmatter stamp, a report section, and a step-4 change that gitignores reports and stops adding them to the committed index. The deliverable is instruction text the LLM follows at runtime.

**Tech Stack:** Markdown SKILL.md files. No build, no test runner. "Verification" for each task = a `grep`/`rg` assertion that the intended text landed, plus a manual trace against the design spec (`docs/superpowers/specs/2026-06-21-p2-cross-model-review-design.md`).

**Source of truth:** the approved design spec at `docs/superpowers/specs/2026-06-21-p2-cross-model-review-design.md`. Read it before starting.

---

## Shared definitions (used verbatim across tasks — keep identical)

**Provider chain** (different-provider first, deterministic order):
```
codex   → model: codex,         provider: openai     (command -v codex)
gemini  → model: gemini,        provider: google     (command -v gemini)
else    → model: claude-sonnet, provider: anthropic  (Agent tool, Sonnet)
```
The `claude-sonnet`/`anthropic` fallback is same-provider — every finding it yields is
labeled `same-provider — weaker signal`.

**`review:` frontmatter token** (stamped on the AUDITED page; committed durable record):
```yaml
review:
  model: codex          # gemini | claude-sonnet
  provider: openai      # google | anthropic
  date: <today>
  status: disputed      # or: clean
  findings: 2           # omit this line when status: clean
```

**Gitignore pattern** (identical in wiki-init generation and wiki-audit self-heal):
```
wiki/pages/audit-*.md
```

**Finding types** (Phase C only):
`overreach` · `internal-contradiction` · `cross-page-contradiction`

---

## File Structure

- Modify: `skills/wiki-init/SKILL.md` — (a) directory diagram + a generated `.gitignore`
  (Task 1); (b) the `SCHEMA.md` template it writes: a new `## Cross-Model Review` section
  documenting the `review:` token (Task 1).
- Modify: `skills/wiki-audit/SKILL.md` — strong-mode entry + intro (Task 2), Phase C
  section + frontmatter stamp (Task 3), report section + step-4 gitignore/index change
  (Task 4).

Order matters: Task 1 establishes the gitignore pattern and token shape; Tasks 2-4 build
strong mode on top; Task 5 guards cross-file consistency. Do them in order.

---

### Task 1: `wiki-init` — generate `.gitignore` and document the `review:` token

**Files:**
- Modify: `skills/wiki-init/SKILL.md` (directory diagram lines ~29-41; `SCHEMA.md` template, after the Citations block ~line 132)

- [ ] **Step 1: Verify the current directory diagram and Citations tail**

Run: `sed -n '29,41p' skills/wiki-init/SKILL.md && echo '---' && sed -n '128,137p' skills/wiki-init/SKILL.md`
Expected: the fenced directory tree (`<wiki-root>/ … └── assets/`) and the "Drive-by citation examples" block followed by `## Log Entry Format`. If the text differs, stop and re-read the file before editing.

- [ ] **Step 2: Add `.gitignore` to the directory diagram**

Find (lines ~29-39):
```
<wiki-root>/
├── SCHEMA.md         ← conventions + absolute path (how other skills find the wiki)
├── raw/              ← immutable source documents (you add these, LLM never modifies)
├── wiki/
│   ├── index.md      ← content catalog: every page, one-line summary, by category
│   ├── log.md        ← append-only operation log
│   ├── overview.md   ← evolving synthesis of everything known
│   └── pages/        ← all wiki pages, flat, slug-named (NO subdirectories)
└── assets/           ← downloaded images, PDFs, attachments
```

Replace with:
```
<wiki-root>/
├── SCHEMA.md         ← conventions + absolute path (how other skills find the wiki)
├── .gitignore        ← local-only artifacts (audit reports) excluded from version control
├── raw/              ← immutable source documents (you add these, LLM never modifies)
├── wiki/
│   ├── index.md      ← content catalog: every page, one-line summary, by category
│   ├── log.md        ← append-only operation log
│   ├── overview.md   ← evolving synthesis of everything known
│   └── pages/        ← all wiki pages, flat, slug-named (NO subdirectories)
└── assets/           ← downloaded images, PDFs, attachments
```

- [ ] **Step 3: Add a `.gitignore` write step after the "Critical: flat" note**

Find (line ~41):
```
**Critical:** `wiki/pages/` is flat. All pages live here as `<slug>.md`. No subdirectories. Slugs are lowercase, hyphen-separated.
```

Insert immediately AFTER it:
```

Ensure `<wiki-root>/.gitignore` excludes audit reports (if the wiki is or later becomes a
git repo, this keeps disposable artifacts out of version control). **Do not clobber an
existing `.gitignore`** — a reinitialized wiki, or a wiki root nested in an existing git
repo, may already have one:
- If `<wiki-root>/.gitignore` does not exist, create it with the block below.
- If it exists but has no `wiki/pages/audit-*.md` line, append the block below.
- If it already ignores `wiki/pages/audit-*.md`, leave it untouched.

\```
# Audit reports are regenerated local-only artifacts (wiki-audit). The committed record
# of an audit is the `review:` frontmatter token on the audited page, not the report.
wiki/pages/audit-*.md
\```

This is the same create-or-append discipline `wiki-audit` uses to self-heal (Task 4).
```

- [ ] **Step 4: Document the `review:` token in the `SCHEMA.md` template**

Find the end of the Citations block (lines ~128-134):
```
**Drive-by citation examples:**
\```
[^3]: raw/scaling-laws.pdf p.7 — "loss scales as a power law in compute"
[^4]: https://twitter.com/user/status/123 (2026-04-15) — "<tweet text>"
\```

## Log Entry Format
```

Replace with:
```
**Drive-by citation examples:**
\```
[^3]: raw/scaling-laws.pdf p.7 — "loss scales as a power law in compute"
[^4]: https://twitter.com/user/status/123 (2026-04-15) — "<tweet text>"
\```

## Cross-Model Review

`wiki-audit strong` runs a second-opinion pass with a different-provider model and
stamps the audited page with an optional `review:` frontmatter block:
\```
review:
  model: codex          # gemini | claude-sonnet
  provider: openai      # google | anthropic
  date: YYYY-MM-DD
  status: clean         # or: disputed
  findings: 2           # present only when status: disputed
\```
- `status: clean` — the reviewer surfaced no disagreement with the normal audit.
- `status: disputed` — the reviewer flagged overreach or a contradiction the normal
  audit missed; `findings:` carries the count. The detail lives in the (local-only)
  audit report.
- `provider: anthropic` (the `claude-sonnet` fallback) means no different-provider CLI
  was available, so the check is same-provider and weaker.

This block is optional and is added only by `wiki-audit strong`. Pages never need it to
be valid.

## Log Entry Format
```

- [ ] **Step 5: Verify the edits landed**

Run: `rg -n 'wiki/pages/audit-\*\.md|\.gitignore|## Cross-Model Review|review:|same-provider' skills/wiki-init/SKILL.md`
Expected: the gitignore pattern appears in BOTH the diagram comment context and the fenced `.gitignore` block; `## Cross-Model Review` appears once; the `review:` mapping and `status: clean`/`disputed` appear in the new section.

- [ ] **Step 6: Commit**

```bash
git add skills/wiki-init/SKILL.md
git commit -m "feat(wiki-init): gitignore audit reports, document review token

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `wiki-audit` — strong-mode entry and intro

**Files:**
- Modify: `skills/wiki-audit/SKILL.md` (intro line ~8; page-resolution paragraph line ~37)

- [ ] **Step 1: Verify the current intro and page-resolution text**

Run: `sed -n '8,8p' skills/wiki-audit/SKILL.md && echo '---' && sed -n '37,37p' skills/wiki-audit/SKILL.md`
Expected: the "Verify a single wiki page … Two phases: …" intro, and the "If the user did not name a page … Audit one page per run." paragraph.

- [ ] **Step 2: Update the intro to mention strong mode's third phase**

Find (line 8):
```
Verify a single wiki page against its cited sources. Two phases: detect uncited factual claims, then verify cited claims by dispatching one subagent per source in parallel.
```

Replace with:
```
Verify a single wiki page against its cited sources. Two phases: detect uncited factual claims, then verify cited claims by dispatching one subagent per source in parallel. In **strong mode** (`wiki-audit strong`) a third phase adds a cross-model adversarial review: a different-provider model re-examines the same claims for overreach and contradiction, and disagreements with the normal pass become findings.
```

- [ ] **Step 3: Add strong-mode argument parsing to the page-resolution paragraph**

Find (line 37):
```
If the user did not name a page, ask which page to audit. Accept slug, filename, or absolute path. Resolve to `wiki/pages/<slug>.md`. Audit one page per run.
```

Replace with:
```
**Mode:** if the invocation arguments contain the word `strong` (e.g. `wiki-audit strong transformer-architecture`), enable strong mode — run Phase C (§3b) after Phase B. Otherwise run normal mode (Phases A and B only). The remaining argument token, if any, names the page.

If the user did not name a page, ask which page to audit. Accept slug, filename, or absolute path. Resolve to `wiki/pages/<slug>.md`. Audit one page per run.
```

- [ ] **Step 4: Verify the edits landed**

Run: `rg -n 'strong mode|wiki-audit strong|Phase C' skills/wiki-audit/SKILL.md`
Expected: ≥1 hit in the intro and ≥1 in the page-resolution paragraph.

- [ ] **Step 5: Commit**

```bash
git add skills/wiki-audit/SKILL.md
git commit -m "feat(wiki-audit): add strong-mode entry and intro

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `wiki-audit` — Phase C (cross-model adversarial review) + frontmatter stamp

Insert a new section between Phase B (ends with the "Why per-source, not per-footnote" note) and "### 4. Write the audit report". Numbered `3b` so the existing sections 4-7 keep their numbers.

**Files:**
- Modify: `skills/wiki-audit/SKILL.md` (insert before line ~110, `### 4. Write the audit report`)

- [ ] **Step 1: Verify the insertion point**

Run: `sed -n '106,112p' skills/wiki-audit/SKILL.md`
Expected: the "Why per-source, not per-footnote" paragraph (line ~108) immediately followed by `### 4. Write the audit report` (line ~110). If a section already sits between them, stop and re-read.

- [ ] **Step 2: Insert the Phase C section**

Insert immediately BEFORE the line `### 4. Write the audit report`:
```
### 3b. Phase C — cross-model adversarial review (strong mode only)

Run this section ONLY when the audit was invoked as `wiki-audit strong`. In normal mode, skip it entirely and go to step 4.

**1. Select a reviewer model (provider chain).** Detect an available different-provider CLI, in order:
- `command -v codex` succeeds → use codex (OpenAI). Label: model `codex`, provider `openai`.
- else `command -v gemini` succeeds → use gemini (Google). Label: model `gemini`, provider `google`.
- else fall back to a Claude subagent via the `Agent` tool (Sonnet). Label: model `claude-sonnet`, provider `anthropic`. Mark every finding `same-provider — weaker signal`, and tell the user that installing codex or gemini would enable a true cross-provider check.

**2. Assemble the bounded payload** — reuse Phase B's work; do NOT re-read raw sources:
- The full target page body.
- For each cited claim: the claim text plus the line-range excerpt Phase B already read.
- The body of each page directly linked from the target via `[[slug]]` (direct links only — not the whole wiki).

Write the payload followed by the instruction block below to a temp file, `$TMPDIR/wiki-review-<page-slug>.md`.

**3. Instruction block** (include verbatim at the top of the payload file):
```
You are an adversarial reviewer. Given a wiki page, the source excerpts its claims
cite, and the bodies of its directly-linked neighbor pages, find ONLY these problems
and return them as a JSON array — nothing else. Do not restate claims that are fine.
Finding types:
- "overreach": a claim generalizes beyond what its cited excerpt supports.
- "internal-contradiction": two claims on this page conflict.
- "cross-page-contradiction": a claim conflicts with a directly-linked neighbor page.
Each finding is an object: {"type": "...", "where": "<line / footnote / page ref>",
"detail": "<one sentence>"}. Return [] if you find nothing.
```

**4. Invoke the reviewer** in non-interactive mode:
- codex:  `codex exec "$(cat "$TMPDIR/wiki-review-<page-slug>.md")"`
- gemini: `gemini -p "$(cat "$TMPDIR/wiki-review-<page-slug>.md")"`
- subagent fallback: dispatch one `Agent` whose prompt is the payload file's contents.

If a CLI call errors, check its non-interactive usage (`codex exec --help` / `gemini --help`) and retry once; if it still fails, fall through to the subagent path. Parse the reviewer's reply as the JSON array of findings (tolerate surrounding prose — extract the array).

**5. Filter to disagreements.** Keep only findings that Phase A/B did NOT already flag: a claim Phase B rated `✅`/`⚠️` that the reviewer calls `overreach` is a disagreement; a contradiction neither phase raised is a disagreement. Discard any reviewer finding that merely repeats an existing Phase A/B verdict. The surviving list is the Phase C findings.

**6. Stamp the `review:` frontmatter** on the AUDITED page (not the report). This is audit metadata — write it automatically, like the report; no content of the page changes. Add or replace a `review:` block in the page frontmatter:
```
review:
  model: codex          # gemini | claude-sonnet, per the chain above
  provider: openai      # google | anthropic
  date: <today>
  status: disputed      # `clean` if step 5 left zero disagreements, else `disputed`
  findings: 2           # the disagreement count; OMIT this line when status: clean
```
Carry the Phase C findings into step 4's report.
```

- [ ] **Step 3: Verify the section landed in the right place**

Run: `rg -n '### 3b. Phase C|provider chain|command -v codex|review:|same-provider — weaker signal' skills/wiki-audit/SKILL.md`
Expected: `### 3b. Phase C` appears once, before `### 4.`; the provider-detection bullets and the `review:` stamp are present.

Run: `rg -n '^### ' skills/wiki-audit/SKILL.md`
Expected ordering: `### 1.` , `### 2. Phase A` , `### 3. Phase B` , `### 3b. Phase C …` , `### 4. Write the audit report` , `### 5.` , `### 6.` , `### 7.` — sections 4-7 unrenumbered.

- [ ] **Step 4: Commit**

```bash
git add skills/wiki-audit/SKILL.md
git commit -m "feat(wiki-audit): Phase C cross-model adversarial review

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: `wiki-audit` — report section, gitignore self-heal, drop report from committed index

**Files:**
- Modify: `skills/wiki-audit/SKILL.md` (report template ~lines 124-126 and 147-149; the "Add the report to index" line ~151; log step ~lines 164-172)

- [ ] **Step 1: Verify the current report template, index line, and log step**

Run: `sed -n '124,151p' skills/wiki-audit/SKILL.md && echo '---' && sed -n '164,172p' skills/wiki-audit/SKILL.md`
Expected: the report's `## Summary` block, the `## ✅ Supported` tail, the `Add the report to wiki/index.md under the Maintenance category …` line, and the `### 6. Append to wiki/log.md` block.

- [ ] **Step 2: Add the cross-model line to the report Summary**

Find (lines ~124-127):
```
## Summary
- Cited claims verified: N
- ✅ Supported: N    ❌ Unsupported: N    ⚠️ Partial: N    🚫 Source missing: N
- 🆘 Uncited factual claims: N
```

Replace with:
```
## Summary
- Cited claims verified: N
- ✅ Supported: N    ❌ Unsupported: N    ⚠️ Partial: N    🚫 Source missing: N
- 🆘 Uncited factual claims: N
- 🧪 Cross-model disagreements: N   (strong mode only; omit this line in normal mode)
```

- [ ] **Step 3: Add the Cross-Model Review section to the report template**

Find the tail of the report template (lines ~147-149):
```
## ✅ Supported
- [^1], [^2], [^4], [^6], [^8] — all verified
\```
```

Replace with:
```
## ✅ Supported
- [^1], [^2], [^4], [^6], [^8] — all verified

## 🧪 Cross-Model Review (<model> / <provider>)
- overreach — [^3]: claim generalizes to "all transformers" but the cited excerpt
  (L142-143) covers only the encoder.
- internal-contradiction — line 12 says "8 heads", line 40 says "16 heads".
- cross-page-contradiction — [[this-page]] vs [[other-page]] disagree on the release date.
Disposition: surfaced for user review (not auto-applied).
\```

Include the `## 🧪 Cross-Model Review` section ONLY in strong mode. Its header names the reviewer (e.g. `(codex / openai)`); when the provider chain fell back to the subagent it reads `(claude-sonnet / anthropic — same-provider, weaker signal)`. List one line per Phase C disagreement; if Phase C found none, write `- none — reviewer agreed with the normal audit.`
```

- [ ] **Step 4: Replace the "add to index" line with the gitignore + no-index rule**

Find (line ~151):
```
Add the report to `wiki/index.md` under the `Maintenance` category (create the category if it does not yet exist — `wiki-lint` uses the same category).
```

Replace with:
```
**Audit reports are local-only artifacts.** Before writing the report, ensure the wiki `.gitignore` (at the wiki root) contains the line `wiki/pages/audit-*.md`; append it if missing (self-healing for wikis initialized before this convention — create `.gitignore` if there is none). Do **not** add the report to `wiki/index.md`: the report is gitignored, so an index entry would be a dangling link in any other clone. For a strong-mode run, the committed record is the `review:` frontmatter token stamped on the page in §3b; the report itself stays local.
```

- [ ] **Step 5: Note the local-only report in the log step**

Find (lines ~164-172):
```
### 6. Append to `wiki/log.md`

Always append — do not ask permission:

\```
## [<today>] audit | [[<page-slug>]] — N supported, N unsupported, N partial, N uncited
Report: [[audit-<page-slug>-<today>]]
Fixed: <list, or "none">
\```
```

Replace with:
```
### 6. Append to `wiki/log.md`

Always append — do not ask permission. In strong mode, append the cross-model result too. The `Report:` line points at the local-only (gitignored) report; that is expected.

\```
## [<today>] audit | [[<page-slug>]] — N supported, N unsupported, N partial, N uncited
Report: audit-<page-slug>-<today>.md (local-only)
Cross-model: <model>/<provider> — clean | N disagreements   # strong mode only
Fixed: <list, or "none">
\```
```

- [ ] **Step 6: Verify the edits landed**

Run: `rg -n '🧪 Cross-model disagreements|## 🧪 Cross-Model Review|local-only artifacts|wiki/pages/audit-\*\.md|Cross-model: <model>' skills/wiki-audit/SKILL.md`
Expected: the Summary line, the report section header, the "local-only artifacts" rule, the gitignore pattern, and the log `Cross-model:` line each appear.

Run: `rg -n 'Add the report to .wiki/index.md' skills/wiki-audit/SKILL.md`
Expected: NO matches (the old index-add line is gone).

- [ ] **Step 7: Commit**

```bash
git add skills/wiki-audit/SKILL.md
git commit -m "feat(wiki-audit): cross-model report section, gitignore reports, drop from index

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Cross-file consistency check + spec trace

No new content — a final guard that the token, gitignore pattern, and provider labels are identical across the two skills, and that the flow matches the spec.

- [ ] **Step 1: Gitignore pattern is byte-identical in both skills**

Run: `rg -n 'wiki/pages/audit-\*\.md' skills/wiki-init/SKILL.md skills/wiki-audit/SKILL.md`
Expected: at least one hit in each file; the pattern spelled exactly `wiki/pages/audit-*.md` in both (no `audit-*` without the path, no trailing slash variant).

- [ ] **Step 2: `review:` token fields and values match between init's doc and audit's stamp**

Run: `rg -n 'model: codex|provider: openai|status: (clean|disputed)|claude-sonnet|anthropic' skills/wiki-init/SKILL.md skills/wiki-audit/SKILL.md`
Expected: the same field names (`model`, `provider`, `date`, `status`, `findings`) and the same enum values (`codex|gemini|claude-sonnet`, `openai|google|anthropic`, `clean|disputed`) appear in both files. Fix any drift so wiki-init's documented token exactly matches what wiki-audit stamps.

- [ ] **Step 3: Provider chain order is identical wherever stated**

Run: `rg -n 'codex|gemini|claude-sonnet' skills/wiki-audit/SKILL.md`
Expected: the detection order is always codex → gemini → claude-sonnet (Phase C step 1, the report header note, the log line). No place lists gemini before codex.

- [ ] **Step 4: Section numbering is intact**

Run: `rg -n '^### ' skills/wiki-audit/SKILL.md`
Expected: `### 1.`, `### 2. Phase A`, `### 3. Phase B`, `### 3b. Phase C …`, `### 4. Write the audit report`, `### 5.`, `### 6.`, `### 7.` — exactly one `3b`, and 4-7 unchanged.

- [ ] **Step 5: Final manual trace against the spec**

Re-read the design spec's "Phase C", "Frontmatter token", "Report section", and "Verification semantics" sections. Walk a strong-mode audit through the edited skills and confirm: (a) provider chain resolves codex→gemini→subagent with the right labels; (b) `status: clean` omits `findings:`, `status: disputed` includes it; (c) the report's 🧪 section appears only in strong mode and names the reviewer; (d) the report is gitignored and never added to `index.md`; (e) the committed durable record is the page's `review:` token. Fix any drift in the skill text (spec wins).

- [ ] **Step 6: Commit (only if Steps 1-5 required fixes)**

```bash
git add skills/
git commit -m "fix: align review token and gitignore wording across wiki skills

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (completed by plan author)

**Spec coverage:** Every spec element maps to a task. Opt-in `strong` arg → Task 2. Provider chain (codex→gemini→subagent) → Task 3 step 1. Reuse of P1 located excerpts (no re-read) → Task 3 step 2. Three check types (overreach / internal / cross-page) → Task 3 step 3. Disagreement filtering → Task 3 step 5. Committed `review:` frontmatter token → Task 3 step 6 (stamp) + Task 1 step 4 (documented in SCHEMA.md). Local-only report + 🧪 section → Task 4 steps 2-3. Gitignore policy (init-generated + audit self-heal) → Task 1 steps 2-3 and Task 4 step 4. Drop reports from committed index → Task 4 step 4. Subagent same-provider labeling → Task 3 step 1 + Task 4 step 3. Out-of-scope items (P8 severity/gating, P3 identity, lint reports) are not touched.

**Placeholder scan:** No TBD/TODO. Every edit step shows exact before/after text; the `<model>`/`<provider>`/`<page-slug>`/`N` placeholders are intentional template fields the runtime fills, not unfinished plan content. Verification steps give exact `rg`/`sed` commands with expected results.

**Type consistency (here: token + label spelling):** The `review:` field set (`model`, `provider`, `date`, `status`, `findings`) and enums (`codex|gemini|claude-sonnet`, `openai|google|anthropic`, `clean|disputed`) are written identically in Task 1 (documentation) and Task 3 (stamp); the gitignore pattern `wiki/pages/audit-*.md` is identical in Task 1 (generation) and Task 4 (self-heal). Task 5 mechanically enforces all three.
