# P2 — Cross-model adversarial review

**Status:** Approved (design)
**Date:** 2026-06-21
**Part of:** wiki-skills improvement backlog (plan 2 of 10, dependency order). Builds on
P1 (line-range provenance), which makes the adversarial pass cheap and located.

## Goal

Self-review under-catches. `wiki-audit`'s normal pass verifies that each cited claim is
*supported by its source*, but it judges that with a single model. The strong form runs a
second pass with a **different-provider model** that looks for a different failure class —
overreach and contradiction — and surfaces any disagreement with the normal pass as a
finding. The committed durable record is a small frontmatter token; the verbose findings
are a local-only report.

## Decisions

- **Opt-in via an argument.** `wiki-audit strong` runs the normal audit (Phase A + Phase B)
  unchanged, then adds **Phase C — cross-model adversarial review**. Bare `wiki-audit` is
  unchanged. One skill, no duplication of the page-resolution machinery.
- **Portable provider chain.** Phase C selects a *different-provider* CLI in order:
  `codex` (OpenAI) → `gemini` (Google) → fallback to a **Claude subagent (Sonnet)**. The
  fallback always yields a second opinion, but every finding it produces is labeled
  `same-provider — weaker signal`, and the run advises installing codex/gemini for a true
  cross-provider check. Detection is `command -v codex || command -v gemini`.
- **Reuse P1's located excerpts — do not re-resolve sources.** Phase C feeds the second
  model the line-range excerpts Phase B already pulled. This is the P1 payoff: located
  claims make the adversarial pass a bounded single call rather than a whole-source re-read.
- **Findings are surfaced, never auto-applied.** A disagreement is something the second
  model flags that Phase A/B passed. It goes to the user for disposition.
- **Durable record is a committed frontmatter token; the report is local-only.** Phase C
  stamps the audited page with a `review:` token (committed). The verbose findings append
  to the existing audit report, which becomes **gitignored** — for *all* audit runs, not
  only strong mode.
- **Audit reports leave the committed index.** Because reports are now gitignored, listing
  them in the committed `index.md` would create links that only resolve on the machine that
  ran the audit. So `wiki-audit` stops adding reports to `index.md`. The frontmatter token
  is the committed signal instead. This applies to normal and strong mode alike.

## Phase C — what it does

### Inputs (one bounded call)

- The target page body.
- Per cited claim: the claim text plus its resolved `L…` source excerpt (carried over from
  Phase B — Phase C does not read raw sources again).
- The bodies of the page's **directly-linked `[[slug]]` neighbor pages** (bounded to direct
  links, not the whole wiki — cross-wiki contradiction at scale is P8/P10's job).

### Checks

1. **Overreach** — a claim generalizes beyond what its cited excerpt supports.
2. **Internal contradiction** — two claims on the same page conflict.
3. **Cross-page contradiction** — the page conflicts with a directly-linked neighbor.

### Invocation

The second model is asked to return a structured (JSON) list of findings, each with a
type (`overreach` / `internal-contradiction` / `cross-page-contradiction`), the offending
claim/line, and a one-line rationale. Pattern (codex shown; gemini and the subagent
fallback are analogous):

```
codex exec "<prompt: page body + per-claim excerpts + neighbor bodies;
             return JSON findings as specified>"
```

Claude parses the response, keeps only **disagreements** (things Phase A/B did not already
flag), and renders them.

## Frontmatter token (committed)

Stamped on the audited page by Phase C:

```yaml
review:
  model: codex          # gemini | claude-sonnet
  provider: openai      # google | anthropic
  date: 2026-06-21
  status: clean         # or: disputed
  findings: 2           # omitted when status: clean
```

- `status: clean` — the second model surfaced no new disagreement.
- `status: disputed` — at least one finding; `findings:` carries the count.
- `provider: anthropic` (the `claude-sonnet` fallback) additionally signals a
  same-provider, weaker check.

## Report section (local-only)

Phase C appends to the existing audit report (`wiki/pages/audit-<slug>-<today>.md`):

```markdown
## 🧪 Cross-Model Review (codex / openai)
- [^3]: overreach — claim generalizes to "all transformers" but the cited excerpt
  (L142-143) covers only the encoder. (codex)
- internal-contradiction — line 12 says "8 heads", line 40 says "16 heads".
- cross-page-contradiction — [[this-page]] vs [[other-page]] disagree on the release date.
Disposition: surfaced for user review (not auto-applied).
```

When the provider chain fell back to the subagent, the section header reads
`(claude-sonnet / anthropic — same-provider, weaker signal)`.

## Gitignore policy

Audit reports become disposable local artifacts:

- `wiki-init` writes `wiki/pages/audit-*.md` into the wiki `.gitignore`.
- `wiki-audit` ensures that entry exists before writing a report (self-healing for wikis
  initialized before this change).
- `wiki-audit` no longer adds reports to `wiki/index.md`.

Lint reports are unchanged in this plan (only audit reports were called out).

## Touch points

1. **`skills/wiki-audit/SKILL.md`** — parse the `strong` argument; add Phase C (provider
   detection chain, bounded second-model call, disagreement filtering); add the
   `## 🧪 Cross-Model Review` report section; stamp the `review:` frontmatter token; change
   step 4 to ensure the `.gitignore` entry and stop adding reports to the committed index.
2. **`skills/wiki-init/SKILL.md`** — add `pages/audit-*.md` to the generated `.gitignore`;
   document the `review:` frontmatter field in the page schema.
3. **`SCHEMA.md` template** — record the `review:` token, its `status` values, and the
   provider-chain note.

## Verification semantics

| Situation | Phase C behavior |
|-----------|------------------|
| codex or gemini present | true cross-provider call; findings labeled with that model |
| neither present | Claude-subagent fallback; findings labeled `same-provider — weaker signal` |
| second model agrees with Phase A/B | `review.status: clean`, no report findings |
| second model flags overreach/contradiction Phase A/B missed | `review.status: disputed`, findings in report, surfaced to user |

## Out of scope

- P8/P10 contradiction-severity tokens and the pre-commit gate — Phase C **surfaces**
  disagreements, it does not gate commits or grade severity.
- Entity identity / `[[wikilink]]` validation (P3).
- Index/log generation and scale work (P4–P7).
- Making lint reports gitignored (only audit reports were in scope).
