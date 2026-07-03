"""Tests for bin/generate-index.py (bundled at skills/wiki-init/assets/bin/)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _harness  # noqa: E402


class GenerateIndexTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _harness.write_schema(self.root)
        self.script = _harness.install_script("generate-index", self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def run_generator(self):
        result = subprocess.run(
            [sys.executable, str(self.script)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return (self.root / "wiki" / "index.md").read_text(encoding="utf-8")

    def test_groups_by_category_in_schema_order(self):
        _harness.write_page(self.root, "transformer", title="Transformer",
                            category="Concepts", summary="Arch", created="2026-06-21")
        _harness.write_page(self.root, "attention", title="Attention",
                            category="Sources", summary="The paper", created="2026-06-20")
        index = self.run_generator()
        self.assertIn("# Wiki Index — ML research", index)
        # Sources is declared before Concepts in the schema, so it must appear first.
        self.assertLess(index.index("### Sources"), index.index("### Concepts"))
        self.assertIn("- [[attention]] — The paper _(2026-06-20)_", index)

    def test_skips_audit_reports(self):
        _harness.write_page(self.root, "audit-foo-2026-06-21", title="Audit",
                            category="Sources", summary="nope", created="2026-06-21")
        index = self.run_generator()
        self.assertNotIn("audit-foo", index)

    def test_missing_category_goes_to_uncategorized_last(self):
        _harness.write_page(self.root, "known", title="Known",
                            category="Sources", summary="s", created="2026-06-21")
        _harness.write_page(self.root, "orphan", title="Orphan",
                            summary="no category", created="2026-06-21")
        index = self.run_generator()
        self.assertIn("### Uncategorized", index)
        self.assertIn("- [[orphan]]", index)
        self.assertLess(index.index("### Sources"), index.index("### Uncategorized"))

    def test_unknown_category_after_schema_categories(self):
        _harness.write_page(self.root, "lint-2026-06-21", title="Lint",
                            category="Maintenance", summary="0 errors", created="2026-06-21")
        _harness.write_page(self.root, "attention", title="Attention",
                            category="Sources", summary="s", created="2026-06-21")
        index = self.run_generator()
        # Maintenance is not a schema category, so it comes after the declared ones.
        self.assertLess(index.index("### Sources"), index.index("### Maintenance"))

    def test_sorted_newest_first_then_title(self):
        _harness.write_page(self.root, "old", title="Old",
                            category="Sources", summary="o", created="2026-06-01")
        _harness.write_page(self.root, "bravo", title="Bravo",
                            category="Sources", summary="b", created="2026-06-25")
        _harness.write_page(self.root, "alpha", title="Alpha",
                            category="Sources", summary="a", created="2026-06-25")
        index = self.run_generator()
        order = [line for line in index.splitlines() if line.startswith("- [[")]
        self.assertEqual(order[0], "- [[alpha]] — a _(2026-06-25)_")  # newest, title asc
        self.assertEqual(order[1], "- [[bravo]] — b _(2026-06-25)_")
        self.assertEqual(order[2], "- [[old]] — o _(2026-06-01)_")  # oldest last

    def test_page_without_frontmatter_is_skipped_with_warning(self):
        bad = self.root / "wiki" / "pages" / "raw.md"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("no frontmatter here\n", encoding="utf-8")
        _harness.write_page(self.root, "good", title="Good",
                            category="Sources", summary="g", created="2026-06-21")
        result = subprocess.run([sys.executable, str(self.script)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("raw.md", result.stderr)
        index = (self.root / "wiki" / "index.md").read_text()
        self.assertIn("[[good]]", index)
        self.assertNotIn("[[raw]]", index)

    def test_missing_link_style_defaults_to_obsidian(self):
        # setUp's schema declares no link_style — entries must use the obsidian form.
        _harness.write_page(self.root, "attention", title="Attention",
                            category="Sources", summary="The paper", created="2026-06-20")
        index = self.run_generator()
        self.assertIn("- [[attention]] — The paper _(2026-06-20)_", index)

    def test_markdown_link_style_emits_wrapped_markdown_links(self):
        _harness.write_schema(self.root, link_style="markdown")
        _harness.write_page(self.root, "attention", title="Attention",
                            category="Sources", summary="The paper", created="2026-06-20")
        index = self.run_generator()
        self.assertIn(
            "- [[attention](pages/attention.md)] — The paper _(2026-06-20)_", index)
        self.assertNotIn("- [[attention]] ", index)  # not the bare obsidian form

    def test_obsidian_link_style_emits_bare_links(self):
        _harness.write_schema(self.root, link_style="obsidian")
        _harness.write_page(self.root, "attention", title="Attention",
                            category="Sources", summary="The paper", created="2026-06-20")
        index = self.run_generator()
        self.assertIn("- [[attention]] — The paper _(2026-06-20)_", index)
        self.assertNotIn("pages/attention.md", index)


if __name__ == "__main__":
    unittest.main()
