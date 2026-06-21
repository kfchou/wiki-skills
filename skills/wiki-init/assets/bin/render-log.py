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


def main():
    try:
        git("rev-parse", "--is-inside-work-tree")
    except RuntimeError:
        sys.exit("not a git repo — the operation log lives in wiki/log.md (the non-git fallback)")

    fmt = f"{REC}%H{FLD}%as{FLD}%s{FLD}%b{FLD}"
    raw = git("log", f"--pretty=format:{fmt}", "--name-status")

    by_date = {}
    order = []
    for chunk in raw.split(REC):
        if not chunk.strip():
            continue
        parts = chunk.split(FLD)
        if len(parts) < 5:
            continue
        commit, date, subject, body, namestatus = (
            parts[0].lstrip("\n"), parts[1], parts[2], parts[3], parts[4])

        op = None
        for line in body.splitlines():
            if line.lower().startswith("wiki-op:"):
                op = line.split(":", 1)[1].strip()
                break
        if not op:
            continue  # not a wiki operation

        pages = []
        for line in namestatus.splitlines():
            line = line.strip()
            if not line:
                continue
            path = line.split("\t")[-1]
            if path.startswith("wiki/pages/") and path.endswith(".md"):
                slug = path[len("wiki/pages/"):-len(".md")]
                if not slug.startswith("audit-"):
                    pages.append(slug)

        if date not in by_date:
            by_date[date] = []
            order.append(date)
        page_str = " (" + ", ".join(f"`{p}`" for p in pages) + ")" if pages else ""
        by_date[date].append(f"- **{op}** — {subject}{page_str}  `{commit[:8]}`")

    out = ["# Wiki Operation Log", "",
           "_Rendered from git history by bin/render-log.py. Do not edit by hand._", ""]
    for date in order:  # git log is already newest-first
        out.append(f"## {date}")
        out.extend(by_date[date])
        out.append("")
    sys.stdout.write("\n".join(out).rstrip() + "\n")


if __name__ == "__main__":
    main()
