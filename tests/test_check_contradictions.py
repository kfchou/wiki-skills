"""Tests for bin/check-contradictions.py (bundled at skills/wiki-init/assets/bin/)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _harness  # noqa: E402


class CheckContradictionsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "wiki" / "pages").mkdir(parents=True)
        self.script = _harness.install_script("check-contradictions", self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def init_repo(self):
        self.git("init", "-q")
        self.git("config", "user.email", "t@t.t")
        self.git("config", "user.name", "tester")

    def write(self, relpath, text):
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def page(self, slug, *, flag=None, body="Body text.", subdir="wiki/pages"):
        fm = ["---", f"title: {slug}", "category: Sources"]
        if flag is not None:
            fm.append(f"contradiction-check: {flag}")
        fm += ["updated: 2026-06-21", "---"]
        return self.write(f"{subdir}/{slug}.md",
                          "\n".join(fm) + f"\n\n# {slug}\n{body}\n")

    def run_check(self):
        return subprocess.run([sys.executable, str(self.script)],
                              capture_output=True, text=True)

    def test_blocks_when_staged_page_carries_failed_flag(self):
        self.init_repo()
        self.page("attention", flag="failed — conflicts with [[bert]] (2024 vs 2023)")
        self.git("add", "-A")
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("attention", out.stderr)
        self.assertIn("--no-verify", out.stderr)

    def test_passes_when_staged_pages_are_clean(self):
        self.init_repo()
        self.page("attention")
        self.git("add", "-A")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_ignores_flag_token_in_body_prose(self):
        # The token appears only in the body, not the frontmatter — must not trip the gate.
        self.init_repo()
        self.page("notes", body="We use the marker `contradiction-check: failed` to gate.")
        self.git("add", "-A")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_ignores_flag_outside_wiki_pages(self):
        # A non-pages file carrying the flag (e.g. a design doc) is not scanned.
        self.init_repo()
        self.write("docs/spec.md",
                   "---\ncontradiction-check: failed — example\n---\n\nbody\n")
        self.git("add", "-A")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_ignores_unstaged_flag(self):
        # Flag present in the working tree but not staged → nothing to gate.
        self.init_repo()
        self.page("attention")
        self.git("add", "-A")
        self.page("attention", flag="failed — only in working tree")  # overwrite, unstaged
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_excludes_audit_reports(self):
        self.init_repo()
        self.page("audit-bert-2026-06-21", flag="failed — should be ignored")
        self.git("add", "-A")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_noop_outside_git_repo(self):
        # No init_repo(): not a git work tree → exit 0, nothing to gate.
        self.page("attention", flag="failed — example")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
