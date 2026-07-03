"""Tests for bin/lint-mechanical.py (bundled at skills/wiki-init/assets/bin/)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _harness  # noqa: E402


def complete_page(root, slug, **overrides):
    """Write a page carrying every required frontmatter field, overridable per test."""
    fields = dict(title=slug.title(), category="Concepts", summary="s",
                  tags=["ml"], sources=["src"], created="2026-06-21",
                  updated="2026-06-21", body="body")
    fields.update(overrides)
    return _harness.write_page(root, slug, **fields)


class LintMechanicalFullTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _harness.write_schema(self.root)
        self.script = _harness.install_script("lint-mechanical", self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def run_full(self, today="2026-06-21", cluster_cap=None):
        argv = [sys.executable, str(self.script), f"--today={today}"]
        if cluster_cap is not None:
            argv.append(f"--cluster-cap={cluster_cap}")
        result = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_missing_frontmatter_reports_absent_required_fields(self):
        complete_page(self.root, "good")
        complete_page(self.root, "bad", summary=None, tags=None)
        findings = self.run_full()["findings"]["missing_frontmatter"]
        bad = next(f for f in findings if f["page"] == "bad")
        self.assertIn("summary", bad["missing"])
        self.assertIn("tags", bad["missing"])
        self.assertFalse(any(f["page"] == "good" for f in findings))

    def test_broken_link_flags_unresolved_target(self):
        complete_page(self.root, "alpha", body="see [[beta]] and [[ghost]]")
        complete_page(self.root, "beta", body="see [[alpha]]")
        findings = self.run_full()["findings"]["broken_links"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0], {"page": "alpha", "link": "ghost"})

    def test_orphan_is_page_with_no_inbound_links(self):
        complete_page(self.root, "hub", body="see [[leaf]]")
        complete_page(self.root, "leaf", body="no links out")
        complete_page(self.root, "lonely", body="no links out")
        orphans = {f["page"] for f in self.run_full()["findings"]["orphans"]}
        self.assertIn("hub", orphans)      # nothing links to hub
        self.assertIn("lonely", orphans)   # nothing links to lonely
        self.assertNotIn("leaf", orphans)  # hub links to leaf

    def test_audit_reports_are_excluded(self):
        complete_page(self.root, "real", body="text")
        # an audit report with no frontmatter must not appear as any finding
        audit = self.root / "wiki" / "pages" / "audit-real-2026-06-21.md"
        audit.write_text("# Audit\nno frontmatter\n", encoding="utf-8")
        findings = self.run_full()["findings"]
        flat = [f.get("page") for group in findings.values() for f in group]
        self.assertNotIn("audit-real-2026-06-21", flat)

    def test_slug_collision_flags_bare_against_qualified(self):
        complete_page(self.root, "mercury", body="ambiguous")
        complete_page(self.root, "mercury-element", body="the metal")
        complete_page(self.root, "mercury-planet", body="the planet")
        complete_page(self.root, "transformer", body="unrelated")
        findings = self.run_full()["findings"]["slug_collisions"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["token"], "mercury")
        self.assertEqual(set(findings[0]["pages"]),
                         {"mercury", "mercury-element", "mercury-planet"})

    def test_stale_date_needs_old_update_and_stale_marker(self):
        complete_page(self.root, "rotten", updated="2020-01-01",
                      body="the current state-of-the-art approach")
        complete_page(self.root, "fresh-old", updated="2020-01-01",
                      body="a timeless description with no markers")
        complete_page(self.root, "recent", updated="2026-06-01",
                      body="the current latest thing")
        stale = {f["page"] for f in self.run_full()["findings"]["stale_date"]}
        self.assertEqual(stale, {"rotten"})  # old + marker only

    def test_missing_concept_needs_three_or_more_unresolved_refs(self):
        complete_page(self.root, "a", body="[[ghost]] here")
        complete_page(self.root, "b", body="[[ghost]] and [[rare]]")
        complete_page(self.root, "c", body="[[ghost]] again")
        findings = self.run_full()["findings"]["missing_concept"]
        self.assertEqual(findings, [{"slug": "ghost", "count": 3}])  # rare seen once: excluded

    def test_markdown_form_links_resolve_for_broken_link_check(self):
        # markdown link_style: [[slug](pages/slug.md)] must be recognized, so a link to an
        # existing page is not flagged broken and a link to a missing page is.
        complete_page(self.root, "alpha",
                      body="see [[beta](pages/beta.md)] and [[ghost](pages/ghost.md)]")
        complete_page(self.root, "beta", body="see [[alpha](pages/alpha.md)]")
        findings = self.run_full()["findings"]["broken_links"]
        self.assertEqual(findings, [{"page": "alpha", "link": "ghost"}])

    def test_markdown_form_links_count_as_inbound_for_orphans(self):
        complete_page(self.root, "hub", body="see [[leaf](pages/leaf.md)]")
        complete_page(self.root, "leaf", body="no links out")
        orphans = {f["page"] for f in self.run_full()["findings"]["orphans"]}
        self.assertIn("hub", orphans)       # nothing links to hub
        self.assertNotIn("leaf", orphans)   # hub's markdown-form link counts as inbound

    def test_mixed_link_forms_both_resolve(self):
        # a wiki mid-migration may carry both forms; the linter must read both.
        complete_page(self.root, "a", body="[[b]] and [[c](pages/c.md)]")
        complete_page(self.root, "b", body="text")
        complete_page(self.root, "c", body="text")
        self.assertEqual(self.run_full()["findings"]["broken_links"], [])


COMPLETE_FM = ("---\ntitle: T\ncategory: Concepts\nsummary: s\ntags: [ml]\n"
               "sources: [src]\ncreated: 2026-06-21\nupdated: 2026-06-21\n---\n")


class LintMechanicalStagedTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "wiki" / "pages").mkdir(parents=True)
        self.script = _harness.install_script("lint-mechanical", self.root)

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

    def page(self, slug, *, complete=True, body="Body text.", extra_fm=""):
        fm = COMPLETE_FM if complete else "---\ntitle: T\n---\n"
        if extra_fm:
            fm = fm[:-4] + extra_fm + "---\n"
        path = self.root / "wiki" / "pages" / f"{slug}.md"
        path.write_text(fm + f"\n# {slug}\n{body}\n", encoding="utf-8")
        return path

    def run_staged(self):
        return subprocess.run([sys.executable, str(self.script), "--staged"],
                              capture_output=True, text=True)

    def test_blocks_staged_page_with_missing_frontmatter(self):
        self.init_repo()
        self.page("bad", complete=False)
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("bad", out.stderr)

    def test_blocks_staged_page_with_broken_link(self):
        self.init_repo()
        self.page("alpha", body="links to [[ghost]]")
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("ghost", out.stderr)

    def test_blocks_staged_slug_colliding_with_existing_page(self):
        self.init_repo()
        self.page("mercury-element", body="committed metal")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "seed")
        self.page("mercury", body="ambiguous, newly staged")  # bare vs qualified
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("mercury", out.stderr)

    def test_passes_when_staged_pages_are_clean(self):
        self.init_repo()
        self.page("alpha", body="links to [[beta]]")
        self.page("beta", body="links to [[alpha]]")
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_markdown_form_broken_link_blocks_commit(self):
        self.init_repo()
        self.page("alpha", body="links to [[ghost](pages/ghost.md)]")
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("ghost", out.stderr)

    def test_markdown_form_valid_link_passes(self):
        self.init_repo()
        self.page("alpha", body="links to [[beta](pages/beta.md)]")
        self.page("beta", body="links to [[alpha](pages/alpha.md)]")
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_reads_staged_blob_not_working_tree(self):
        self.init_repo()
        self.page("alpha", body="clean, no links")
        self.git("add", "-A")
        self.page("alpha", complete=False, body="broken in working tree only")  # unstaged
        out = self.run_staged()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_excludes_audit_reports(self):
        self.init_repo()
        self.page("audit-x-2026-06-21", complete=False, body="links to [[ghost]]")
        self.git("add", "-A")
        out = self.run_staged()
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_noop_outside_git_repo(self):
        self.page("bad", complete=False)  # no init_repo
        out = self.run_staged()
        self.assertEqual(out.returncode, 0, out.stderr)


class LintMechanicalClusterTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _harness.write_schema(self.root)
        self.script = _harness.install_script("lint-mechanical", self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def clusters(self, cluster_cap=None):
        argv = [sys.executable, str(self.script), "--today=2026-06-21"]
        if cluster_cap is not None:
            argv.append(f"--cluster-cap={cluster_cap}")
        result = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["clusters"]

    def page_sets(self, clusters):
        return [set(c["pages"]) for c in clusters]

    def test_shared_tag_forms_a_cluster_singletons_skipped(self):
        complete_page(self.root, "a", tags=["nlp"])
        complete_page(self.root, "b", tags=["nlp"])
        complete_page(self.root, "lonely", tags=["solo"])  # only page with this tag
        sets = self.page_sets(self.clusters())
        self.assertIn({"a", "b"}, sets)
        self.assertNotIn({"lonely"}, sets)

    def test_subset_cluster_is_dropped(self):
        complete_page(self.root, "a", tags=["x", "y"])
        complete_page(self.root, "b", tags=["x", "y"])
        complete_page(self.root, "c", tags=["y"])
        # tag x -> {a,b}; tag y -> {a,b,c}. {a,b} is a subset of {a,b,c}, so only {a,b,c}.
        sets = self.page_sets(self.clusters())
        self.assertEqual(sets, [{"a", "b", "c"}])

    def test_oversized_cluster_is_split_and_flagged(self):
        for slug in ("a", "b", "c", "d"):
            complete_page(self.root, slug, tags=["big"])
        clusters = self.clusters(cluster_cap=2)
        self.assertTrue(all(len(c["pages"]) <= 2 for c in clusters))
        self.assertTrue(all(c["split"] for c in clusters))  # every chunk flagged split
        self.assertEqual(sum(len(c["pages"]) for c in clusters), 4)

    def test_small_cluster_is_not_flagged_split(self):
        complete_page(self.root, "a", tags=["t"])
        complete_page(self.root, "b", tags=["t"])
        self.assertFalse(any(c["split"] for c in self.clusters()))


if __name__ == "__main__":
    unittest.main()
