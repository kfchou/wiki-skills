#!/usr/bin/env python3
"""Deterministic wiki health checks — the zero-LLM phase of wiki-lint.

Two modes:
  python bin/lint-mechanical.py            full mode  -> JSON, all checks, whole wiki
  python bin/lint-mechanical.py --staged   staged mode -> human text + exit code,
                                           staged files only (pre-commit gate)

Full mode emits a JSON object {"findings": {...}, "clusters": [...]} for wiki-lint to fold
into its report. Staged mode runs the per-file/resolvable checks against the staged blobs and
exits non-zero if any fire, so the pre-commit hook blocks the commit. Stdlib only.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = WIKI_ROOT / "wiki" / "pages"

REQUIRED_FIELDS = ("title", "category", "summary", "tags", "sources", "created", "updated")
# Cross-reference forms (see config/link-style.md). Reading is permissive — match both so the
# linter works on any wiki regardless of its link_style, and on wikis that mix the two forms:
#   obsidian: [[slug]] or [[slug|display]]
#   markdown: [[slug](pages/slug.md)]
LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\](?:\(pages/[^)]*\.md\))?\]")
STALE_MARKERS = ("current", "latest", "recent", "state-of-the-art")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
STALE_AGE_DAYS = 90
DEFAULT_CLUSTER_CAP = 25


def split_doc(text):
    """Return (frontmatter_dict_or_None, body_text) — body excludes the frontmatter block."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, text
    return parse_frontmatter(text), "\n".join(lines[end + 1:])


def parse_frontmatter(text):
    """Return the page's frontmatter as a dict, or None if absent/unterminated.

    Scalar `key: value` lines become strings; `key: [a, b]` inline lists become lists.
    No third-party YAML dependency.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    fm = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            fm[key] = items
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fm[key] = value
    return fm


def links_in(text):
    """Return the cross-referenced slugs in a page body, in both link styles.

    `LINK_RE` captures the slug from the obsidian form (`[[slug]]`, `[[slug|display]]`) and
    the markdown form (`[[slug](pages/slug.md)]`) alike, so this works regardless of the
    wiki's link_style. See config/link-style.md.
    """
    return [m.strip() for m in LINK_RE.findall(text)]


def is_page(path):
    return path.suffix == ".md" and not path.name.startswith("audit-")


def load_pages():
    """Return {slug: {"fm": dict|None, "body": str, "links": [slug, ...]}} for real pages.

    `body` and `links` exclude the frontmatter block, so frontmatter dates never count as
    stale-content years and frontmatter never contributes phantom links.
    """
    pages = {}
    if not PAGES_DIR.exists():
        return pages
    for path in sorted(PAGES_DIR.glob("*.md")):
        if not is_page(path):
            continue
        fm, body = split_doc(path.read_text(encoding="utf-8"))
        pages[path.stem] = {"fm": fm, "body": body, "links": links_in(body)}
    return pages


def missing_fields(fm):
    """Required frontmatter fields that are absent or empty."""
    fm = fm or {}
    return [f for f in REQUIRED_FIELDS if not fm.get(f)]


def check_missing_frontmatter(pages):
    out = []
    for slug, page in pages.items():
        missing = missing_fields(page["fm"])
        if missing:
            out.append({"page": slug, "missing": missing})
    return out


def check_broken_links(pages):
    known = set(pages)
    out = []
    for slug, page in pages.items():
        for target in page["links"]:
            if target not in known:
                out.append({"page": slug, "link": target})
    return out


def check_orphans(pages):
    inbound = {slug: 0 for slug in pages}
    for slug, page in pages.items():
        for target in page["links"]:
            if target in inbound and target != slug:
                inbound[target] += 1
    return [{"page": slug} for slug, n in inbound.items() if n == 0]


def check_slug_collisions(pages):
    """Flag a bare single-token slug colliding with qualified slugs sharing its lead token."""
    out = []
    for slug in pages:
        if "-" in slug:
            continue  # only bare slugs are ambiguous
        qualified = sorted(s for s in pages if s != slug and s.split("-")[0] == slug)
        if qualified:
            out.append({"token": slug, "pages": [slug] + qualified})
    return out


def check_stale_date(pages, today):
    out = []
    for slug, page in pages.items():
        fm = page["fm"] or {}
        updated = fm.get("updated")
        try:
            age = (today - date.fromisoformat(updated)).days
        except (TypeError, ValueError):
            continue
        if age <= STALE_AGE_DAYS:
            continue
        body = page["body"].lower()
        has_marker = any(m in body for m in STALE_MARKERS)
        has_old_year = any(int(m.group()) <= today.year - 2 for m in YEAR_RE.finditer(body))
        if has_marker or has_old_year:
            out.append({"page": slug})
    return out


def check_missing_concept(pages):
    """A [[slug]] referenced 3+ times across the wiki that resolves to no page."""
    known = set(pages)
    counts = {}
    for page in pages.values():
        for target in page["links"]:
            if target not in known:
                counts[target] = counts.get(target, 0) + 1
    return [{"slug": s, "count": n} for s, n in sorted(counts.items()) if n >= 3]


def build_clusters(pages, cap):
    """Group pages by shared tag into contradiction-sweep clusters.

    A tag with >=2 pages is a candidate cluster; singleton tags are skipped. A cluster that
    is a strict subset of another is dropped (the superset's subagent covers it). A cluster
    larger than `cap` is deterministically split into alphabetical chunks, each flagged
    `split` so the report can note the recall caveat.
    """
    by_tag = {}
    for slug, page in pages.items():
        for tag in (page["fm"] or {}).get("tags") or []:
            by_tag.setdefault(tag, set()).add(slug)

    candidates = {frozenset(s) for s in by_tag.values() if len(s) >= 2}
    kept = [c for c in candidates if not any(c < other for other in candidates)]

    out = []
    for members in sorted((sorted(c) for c in kept)):
        if len(members) > cap:
            for i in range(0, len(members), cap):
                out.append({"pages": members[i:i + cap], "split": True})
        else:
            out.append({"pages": members, "split": False})
    return out


def run_full(today=None, cluster_cap=None):
    today = today or date.today()
    cluster_cap = cluster_cap or DEFAULT_CLUSTER_CAP
    pages = load_pages()
    findings = {
        "missing_frontmatter": check_missing_frontmatter(pages),
        "broken_links": check_broken_links(pages),
        "orphans": check_orphans(pages),
        "slug_collisions": check_slug_collisions(pages),
        "stale_date": check_stale_date(pages, today),
        "missing_concept": check_missing_concept(pages),
    }
    return {"findings": findings, "clusters": build_clusters(pages, cluster_cap)}


def git(*args):
    result = subprocess.run(["git", "-C", str(WIKI_ROOT), *args],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def staged_page_paths():
    """Yield staged (added/copied/modified) wiki/pages/*.md paths, excluding audit reports."""
    out = git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    for path in out.splitlines():
        path = path.strip()
        if (path.startswith("wiki/pages/") and path.endswith(".md")
                and not Path(path).name.startswith("audit-")):
            yield path


def known_slugs():
    """The slug set used to resolve links/collisions — the working-tree pages on disk."""
    if not PAGES_DIR.exists():
        return set()
    return {p.stem for p in PAGES_DIR.glob("*.md") if is_page(p)}


def collision_for(slug, known):
    """Return the colliding slug group if `slug` collides with a known slug, else None."""
    others = known - {slug}
    if "-" not in slug:  # bare slug vs qualified slugs sharing it
        partners = sorted(s for s in others if s.split("-")[0] == slug)
        return [slug] + partners if partners else None
    base = slug.split("-")[0]  # qualified slug vs an existing bare base
    return sorted([base, slug]) if base in others else None


def run_staged():
    try:
        git("rev-parse", "--is-inside-work-tree")
    except RuntimeError:
        return 0  # not a git repo — nothing to gate
    known = known_slugs()
    problems = []
    for path in staged_page_paths():
        slug = Path(path).stem
        try:
            fm, body = split_doc(git("show", f":{path}"))  # the staged blob
        except RuntimeError:
            continue
        missing = missing_fields(fm)
        if missing:
            problems.append((slug, f"missing frontmatter: {', '.join(missing)}"))
        for target in links_in(body):
            if target not in known:
                problems.append((slug, f"broken link: [[{target}]]"))
        collision = collision_for(slug, known)
        if collision:
            problems.append((slug, f"slug collision: {', '.join(collision)}"))

    if not problems:
        return 0
    print("commit blocked — structural problems in staged page(s):\n", file=sys.stderr)
    for slug, msg in problems:
        print(f"  wiki/pages/{slug}.md\n    {msg}", file=sys.stderr)
    print("\nFix the page(s) and re-stage. To commit anyway: git commit --no-verify",
          file=sys.stderr)
    return 1


def parse_opt(argv, name, convert):
    prefix = f"--{name}="
    for arg in argv:
        if arg.startswith(prefix):
            return convert(arg[len(prefix):])
    return None


def main(argv):
    if "--staged" in argv:
        sys.exit(run_staged())
    today = parse_opt(argv, "today", date.fromisoformat)
    cap = parse_opt(argv, "cluster-cap", int)
    json.dump(run_full(today, cap), sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
