"""Shared test helpers.

The wiki helper scripts (`generate-index.py`, `render-log.py`) are not standalone files in
this repo — their canonical source is the fenced ```python block embedded in
`skills/wiki-init/SKILL.md`, because that is what `wiki-init` writes into each wiki. The
tests extract those exact blocks and exercise them, so the tests validate what ships.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "wiki-init" / "SKILL.md"

# A unique substring of each script's module docstring, used to pick its code block.
_SIGNATURES = {
    "generate-index": "Generate wiki/index.md from page frontmatter",
    "render-log": "Render the wiki operation log from git history",
}


def extract_script(name):
    """Return the source of the named helper script from wiki-init/SKILL.md."""
    sig = _SIGNATURES[name]
    text = SKILL.read_text(encoding="utf-8")
    for block in re.findall(r"```python\n(.*?)\n```", text, re.S):
        if sig in block:
            return block + "\n"
    raise AssertionError(f"script {name!r} not found in {SKILL}")


def install_script(name, wiki_root):
    """Write the named helper script into <wiki_root>/bin/ and return its path."""
    bin_dir = Path(wiki_root) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dest = bin_dir / f"{name}.py"
    dest.write_text(extract_script(name), encoding="utf-8")
    return dest


def write_page(wiki_root, slug, *, title=None, category=None, summary=None,
               created=None, body="body"):
    """Write a wiki page with the given frontmatter fields (omitting any left None)."""
    fm = ["---"]
    if title is not None:
        fm.append(f"title: {title}")
    if category is not None:
        fm.append(f"category: {category}")
    if summary is not None:
        fm.append(f"summary: {summary}")
    if created is not None:
        fm.append(f"created: {created}")
    fm.append("updated: 2026-06-21")
    fm.append("---")
    page = Path(wiki_root) / "wiki" / "pages" / f"{slug}.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("\n".join(fm) + f"\n\n# {title or slug}\n{body}\n", encoding="utf-8")
    return page


def write_schema(wiki_root, domain="ML research",
                 categories=("Sources", "Entities", "Concepts", "Analyses")):
    cats = "\n".join(categories)
    (Path(wiki_root) / "SCHEMA.md").write_text(
        f"# Wiki Schema\n\n## Identity\n- **Domain:** {domain}\n\n"
        f"## Index Categories\n{cats}\n\n## Conventions\n- x\n",
        encoding="utf-8",
    )
