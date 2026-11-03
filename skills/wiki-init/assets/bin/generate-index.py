#!/usr/bin/env python3
"""Generate wiki/index.md from page frontmatter.

index.md is a runtime-only, gitignored artifact. Run this before reading the index and
after any operation that adds, removes, renames, or re-categorizes a page. Never
hand-edit index.md — edit the page's frontmatter and rerun this script.
"""
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = WIKI_ROOT / "wiki" / "pages"
SCHEMA = WIKI_ROOT / "SCHEMA.md"
INDEX = WIKI_ROOT / "wiki" / "index.md"


def frontmatter_lines(text):
    """Return the lines between the opening and closing `---`, or None if absent/unterminated."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    return None if end is None else lines[1:end]


def is_field_line(line):
    """True for a `key: value` line; blank lines and `#` comments are not fields."""
    return bool(line.strip()) and not line.lstrip().startswith("#") and ":" in line


def is_quoted(value):
    return len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"


def unquote(value):
    return value[1:-1] if is_quoted(value) else value


def parse_frontmatter(text):
    """Return the page's frontmatter as a dict, or None if absent/unterminated.

    Only scalar `key: value` lines are needed (title, category, summary, created).
    List values like `tags: [...]` are ignored. No third-party deps.
    """
    lines = frontmatter_lines(text)
    if lines is None:
        return None
    fm = {}
    for line in filter(is_field_line, lines):
        key, _, value = line.partition(":")
        fm[key.strip()] = unquote(value.strip())
    return fm


def read_link_style():
    """Return the wiki's cross-reference style: 'markdown' or 'obsidian' (default).

    Reads the `link_style:` field from SCHEMA.md's Cross-References section. A missing
    field (older wiki) or an unfilled `<...>` placeholder defaults to obsidian.
    """
    if not SCHEMA.exists():
        return "obsidian"
    for line in SCHEMA.read_text(encoding="utf-8").splitlines():
        if "link_style:" not in line:
            continue
        value = line.split("link_style:", 1)[1].strip().strip("*").strip()
        if value.startswith("markdown"):
            return "markdown"
        return "obsidian"
    return "obsidian"


def format_ref(slug, link_style):
    """Emit a cross-reference to `slug` in the wiki's link style (see config/link-style.md)."""
    if link_style == "markdown":
        return f"[[{slug}](pages/{slug}.md)]"
    return f"[[{slug}]]"


def schema_category(stripped):
    """Return the category named by a line under `## Index categories`, or None."""
    cat = stripped.lstrip("-").strip()
    return cat if cat and not cat.startswith("<") else None


def read_schema():
    """Return (domain, [categories]) parsed from SCHEMA.md."""
    domain, categories = "", []
    if not SCHEMA.exists():
        return domain, categories
    in_categories = False
    for line in SCHEMA.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "**Domain:**" in line:
            domain = line.split("**Domain:**", 1)[1].strip()
        if stripped.startswith("## "):
            in_categories = stripped[3:].strip().lower() == "index categories"
        elif in_categories and (cat := schema_category(stripped)):
            categories.append(cat)
    return domain, categories


def collect_pages():
    """Return one entry per page with frontmatter, skipping audit reports."""
    pages = []
    for path in sorted(PAGES_DIR.glob("*.md")):
        if path.name.startswith("audit-"):
            continue  # gitignored local-only artifacts
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            print(f"warning: {path.name} has no frontmatter; skipping", file=sys.stderr)
            continue
        pages.append({
            "slug": path.stem,
            "title": fm.get("title", path.stem),
            "category": fm.get("category", "Uncategorized"),
            "summary": fm.get("summary", ""),
            "created": fm.get("created", ""),
        })
    return pages


def order_categories(pages, schema_categories):
    """SCHEMA categories first, then unknown ones alphabetically, then Uncategorized."""
    present = {p["category"] for p in pages}
    extras = sorted(present - set(schema_categories) - {"Uncategorized"})
    ordered = list(schema_categories) + extras
    if "Uncategorized" in present:
        ordered.append("Uncategorized")
    return ordered


def render_category(cat, pages, link_style):
    """Return the index lines for one category, or [] if it has no pages."""
    entries = [p for p in pages if p["category"] == cat]
    if not entries:
        return []
    entries.sort(key=lambda p: p["title"])              # tiebreak: title asc
    entries.sort(key=lambda p: p["created"], reverse=True)  # primary: created desc
    out = [f"### {cat}"]
    for p in entries:
        summary = f" — {p['summary']}" if p["summary"] else ""
        date = f" _({p['created']})_" if p["created"] else ""
        out.append(f"- {format_ref(p['slug'], link_style)}{summary}{date}")
    out.append("")
    return out


def main():
    if not PAGES_DIR.exists():
        sys.exit(f"no pages directory at {PAGES_DIR}")
    domain, schema_categories = read_schema()
    link_style = read_link_style()
    pages = collect_pages()

    out = [f"# Wiki Index — {domain}".rstrip(), "",
           "<!-- Generated by bin/generate-index.py. Do not edit by hand. -->", ""]
    for cat in order_categories(pages, schema_categories):
        out.extend(render_category(cat, pages, link_style))

    INDEX.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {INDEX} ({len(pages)} pages)")

if __name__ == "__main__":
    main()
