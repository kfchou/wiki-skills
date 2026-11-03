#!/usr/bin/env python3
"""Render the wiki operation log from git history.

In a git wiki, each operation is recorded as a commit carrying a `Wiki-Op:` trailer
(see the Operation Log & Commit Convention in SCHEMA.md). This renders those commits as
a human-readable, newest-first log on demand — replacing a hand-maintained log.md.
Commits without a `Wiki-Op:` trailer (e.g. manual edits) are ignored.
"""
import subprocess
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parent.parent
REC = "\x1e"  # record separator between commits
FLD = "\x1f"  # field separator within a commit


def git(*args):
    result = subprocess.run(
        ["git", "-C", str(WIKI_ROOT), *args],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def parse_records(raw):
    """Yield (commit, date, subject, body, namestatus) for each well-formed log record."""
    for chunk in raw.split(REC):
        if not chunk.strip():
            continue
        parts = chunk.split(FLD)
        if len(parts) < 5:
            continue
        yield parts[0].lstrip("\n"), parts[1], parts[2], parts[3], parts[4]


def wiki_op(body):
    """Return the `Wiki-Op:` trailer value from a commit body, or None."""
    for line in body.splitlines():
        if line.lower().startswith("wiki-op:"):
            return line.split(":", 1)[1].strip()
    return None


def page_slug(namestatus_line):
    """Return the slug of a non-audit page in a `--name-status` line, or None."""
    path = namestatus_line.strip().split("\t")[-1]
    if not (path.startswith("wiki/pages/") and path.endswith(".md")):
        return None
    slug = path[len("wiki/pages/"):-len(".md")]
    return None if slug.startswith("audit-") else slug


def main():
    try:
        git("rev-parse", "--is-inside-work-tree")
    except RuntimeError:
        sys.exit("not a git repo — the operation log lives in wiki/log.md (the non-git fallback)")

    fmt = f"{REC}%H{FLD}%as{FLD}%s{FLD}%b{FLD}"
    raw = git("log", f"--pretty=format:{fmt}", "--name-status")

    by_date = {}  # insertion order = git log order, newest first
    for commit, date, subject, body, namestatus in parse_records(raw):
        op = wiki_op(body)
        if not op:
            continue  # not a wiki operation
        pages = [s for s in map(page_slug, namestatus.splitlines()) if s is not None]
        page_str = " (" + ", ".join(f"`{p}`" for p in pages) + ")" if pages else ""
        by_date.setdefault(date, []).append(f"- **{op}** — {subject}{page_str}  `{commit[:8]}`")

    out = ["# Wiki Operation Log", "",
           "_Rendered from git history by bin/render-log.py. Do not edit by hand._", ""]
    for date, entries in by_date.items():
        out.append(f"## {date}")
        out.extend(entries)
        out.append("")
    sys.stdout.write("\n".join(out).rstrip() + "\n")

if __name__ == "__main__":
    main()
