"""Shared test helpers.

The wiki helper scripts (`generate-index.py`, `render-log.py`, `check-contradictions.py`)
are standalone files bundled with the skill at `skills/wiki-init/assets/bin/` — exactly the
files `wiki-init` copies into each wiki. The tests install those files and exercise them, so
the tests validate what ships.
"""
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_BIN = REPO_ROOT / "skills" / "wiki-init" / "assets" / "bin"


def install_script(name, wiki_root):
    """Copy the named helper script into <wiki_root>/bin/ and return its path."""
    bin_dir = Path(wiki_root) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    src = ASSETS_BIN / f"{name}.py"
    dest = bin_dir / f"{name}.py"
    shutil.copy2(src, dest)
    return dest


def write_page(wiki_root, slug, *, title=None, category=None, summary=None,
               created=None, tags=None, sources=None, updated="2026-06-21", body="body"):
    """Write a wiki page with the given frontmatter fields (omitting any left None).

    `tags` and `sources` accept a list and are rendered as an inline `[a, b]` list.
    `updated` defaults to a fixed date; pass an older one to exercise stale-date checks.
    """
    fm = ["---"]
    if title is not None:
        fm.append(f"title: {title}")
    if category is not None:
        fm.append(f"category: {category}")
    if summary is not None:
        fm.append(f"summary: {summary}")
    if tags is not None:
        fm.append(f"tags: [{', '.join(tags)}]")
    if sources is not None:
        fm.append(f"sources: [{', '.join(sources)}]")
    if created is not None:
        fm.append(f"created: {created}")
    if updated is not None:
        fm.append(f"updated: {updated}")
    fm.append("---")
    page = Path(wiki_root) / "wiki" / "pages" / f"{slug}.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("\n".join(fm) + f"\n\n# {title or slug}\n{body}\n", encoding="utf-8")
    return page


def write_schema(wiki_root, domain="ML research",
                 categories=("Sources", "Entities", "Concepts", "Analyses"),
                 link_style=None):
    """Write a minimal SCHEMA.md. `link_style` (obsidian|markdown), if given, adds the
    Cross-References field; omit it to simulate an older wiki with no link_style declared."""
    cats = "\n".join(categories)
    xref = ""
    if link_style is not None:
        xref = f"## Cross-References\n- **link_style:** {link_style}\n- **link_style_rules:** config/link-style.md\n\n"
    (Path(wiki_root) / "SCHEMA.md").write_text(
        f"# Wiki Schema\n\n## Identity\n- **Domain:** {domain}\n\n"
        f"{xref}"
        f"## Index Categories\n{cats}\n\n## Conventions\n- x\n",
        encoding="utf-8",
    )
