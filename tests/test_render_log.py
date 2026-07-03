"""Tests for bin/render-log.py (bundled at skills/wiki-init/assets/bin/)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _harness  # noqa: E402


class RenderLogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "wiki" / "pages").mkdir(parents=True)
        self.script = _harness.install_script("render-log", self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args, env=None):
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def init_repo(self):
        self.git("init", "-q")
        self.git("config", "user.email", "t@t.t")
        self.git("config", "user.name", "tester")

    def commit(self, message, date=None, touch=None):
        if touch:
            page = self.root / "wiki" / "pages" / touch
            page.write_text("x\n", encoding="utf-8")
        self.git("add", "-A")
        import os
        env = dict(os.environ)
        if date:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{date}T10:00:00"
        args = ["commit", "-q"]
        if not touch:
            args.append("--allow-empty")
        for paragraph in message.split("\n\n"):
            args += ["-m", paragraph]
        self.git(*args, env=env)

    def render(self):
        result = subprocess.run([sys.executable, str(self.script)],
                                capture_output=True, text=True)
        return result

    def test_renders_wiki_op_commits_grouped_by_date(self):
        self.init_repo()
        self.commit("chore: initialize wiki\n\nWiki-Op: init", date="2026-06-20")
        self.commit("docs: summarize Attention\n\nWiki-Op: ingest",
                    date="2026-06-21", touch="attention.md")
        out = self.render()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("## 2026-06-21", out.stdout)
        self.assertIn("## 2026-06-20", out.stdout)
        self.assertIn("**ingest** — docs: summarize Attention (`attention`)", out.stdout)
        self.assertIn("**init** — chore: initialize wiki", out.stdout)
        # newest date first
        self.assertLess(out.stdout.index("## 2026-06-21"), out.stdout.index("## 2026-06-20"))

    def test_ignores_commits_without_trailer(self):
        self.init_repo()
        self.commit("docs: summarize Attention\n\nWiki-Op: ingest",
                    date="2026-06-21", touch="attention.md")
        self.commit("chore: manual tweak, no trailer", date="2026-06-21", touch="other.md")
        out = self.render()
        self.assertIn("ingest", out.stdout)
        self.assertNotIn("manual tweak", out.stdout)

    def test_excludes_audit_report_pages_from_page_list(self):
        self.init_repo()
        self.commit("fix: audit bert\n\nWiki-Op: audit",
                    date="2026-06-21", touch="audit-bert-2026-06-21.md")
        out = self.render()
        self.assertIn("**audit**", out.stdout)
        self.assertNotIn("audit-bert", out.stdout)

    def test_non_git_exits_with_message(self):
        # No init_repo(): the directory is not a git repo.
        out = self.render()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("not a git repo", out.stderr.lower())


if __name__ == "__main__":
    unittest.main()
