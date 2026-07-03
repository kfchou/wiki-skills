#!/usr/bin/env python3
"""Block commits that stage a wiki page still flagged with a contradiction.

wiki-ingest writes `contradiction-check: failed` into a page's frontmatter when it finds a
blocking contradiction, and removes it once resolved. This pre-commit gate is the
deterministic backstop: it scans the *staged* content of wiki/pages/*.md and, if any still
carries that flag in its frontmatter, blocks the commit. No LLM, stdlib only.

Invoked from bin/hooks/pre-commit. Override an intentional commit with `git commit --no-verify`.
"""
import subprocess
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parent.parent
FLAG_KEY = "contradiction-check"


def git(*args):
    result = subprocess.run(
        ["git", "-C", str(WIKI_ROOT), *args],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def staged_pages():
    """Yield staged (added/copied/modified) wiki/pages/*.md paths, excluding audit reports."""
    out = git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    for path in out.splitlines():
        path = path.strip()
        if (path.startswith("wiki/pages/") and path.endswith(".md")
                and not Path(path).name.startswith("audit-")):
            yield path


def frontmatter_flag(text):
    """Return the flag's reason if the frontmatter carries `contradiction-check: failed`.

    Parses only the leading `---` ... `---` block, so a mention of the token in the page
    body (or any prose) never trips the gate. Returns None when clean or unterminated.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        if key.strip() == FLAG_KEY and value.strip().lower().startswith("failed"):
            return value.strip()
    return None


def main():
    try:
        git("rev-parse", "--is-inside-work-tree")
    except RuntimeError:
        return  # not a git repo — nothing to gate

    flagged = []
    for path in staged_pages():
        try:
            staged = git("show", f":{path}")  # the staged blob, not the working tree
        except RuntimeError:
            continue
        reason = frontmatter_flag(staged)
        if reason is not None:
            flagged.append((path, reason))

    if not flagged:
        return

    print("commit blocked — unresolved contradiction flag in staged page(s):\n",
          file=sys.stderr)
    for path, reason in flagged:
        print(f"  {path}\n    {reason}", file=sys.stderr)
    print("\nResolve the contradiction and remove the `contradiction-check:` line "
          "(see wiki-ingest step 7b), then re-stage.", file=sys.stderr)
    print("To commit anyway: git commit --no-verify", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
