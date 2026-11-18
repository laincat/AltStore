"""render_docs 的离线测试：只查文本处理，不联网。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import render_docs  # noqa: E402


def app(name, bundle, version, min_os="15.0", repo="laincat/Rules", beta=None):
    channels = [{
        "track": "stable",
        "releases": [{"version": version, "minOSVersion": min_os}],
    }]
    if beta:
        channels.append({"track": "nightly", "releases": [{"version": beta}]})
    return {
        "name": name,
        "bundleIdentifier": bundle,
        "localizedDescription": "说明。项目主页：https://github.com/%s" % repo,
        "releaseChannels": channels,
        "versions": [{"version": version}],
    }


class RenderTableTests(unittest.TestCase):
    def test_table_has_one_row_per_app_and_columns(self):
        apps = [app("B", "b.b", "1.0"), app("A", "a.a", "2.0", "16.0", beta="2.1")]
        lines = render_docs.render_table(apps).splitlines()
        self.assertEqual(len(lines), 2 + 2)
        self.assertTrue(lines[0].startswith("| 应用 | Bundle ID |"))
        self.assertIn("| A | `a.a` | 2.0 | iOS 16.0+ | 2.1 |".replace("`", chr(96)), lines[2])
        self.assertEqual(lines[2].split("|")[1].strip(), "A")

    def test_upstream_link_from_description(self):
        self.assertEqual(
            render_docs.upstream(app("X", "x.x", "1.0", repo="foo/bar")),
            "[foo/bar](https://github.com/foo/bar)",
        )

    def test_replace_block_is_idempotent(self):
        text = "a\n<!-- apps:begin -->\nold\n<!-- apps:end -->\nb"
        once = render_docs.replace_block(text, render_docs.BEGIN, render_docs.END, "new")
        twice = render_docs.replace_block(once, render_docs.BEGIN, render_docs.END, "new")
        self.assertEqual(once, twice)
        self.assertIn("new", once)
        self.assertNotIn("old", once)

    def test_missing_markers_raise(self):
        with self.assertRaises(SystemExit):
            render_docs.replace_block("no markers", render_docs.BEGIN, render_docs.END, "x")


class DiffTests(unittest.TestCase):
    def test_detects_update_add_remove_rename(self):
        prev = [app("A", "a.a", "1.0"), app("B", "b.b", "1.0"), app("C", "c.c", "1.0")]
        cur = [app("A", "a.a", "1.1"), app("D", "d.d", "0.1"), app("B2", "b.b", "1.0")]
        lines = render_docs.diff_lines(prev, cur)
        self.assertIn("- **A** 1.0 → 1.1", lines)
        self.assertIn("- 新增 **D** 0.1", lines)
        self.assertIn("- 移除 **C**", lines)
        self.assertIn("- **B** 更名为 **B2**", lines)

    def test_no_change_is_empty(self):
        apps = [app("A", "a.a", "1.0")]
        self.assertEqual(render_docs.diff_lines(apps, apps), [])


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.id().replace(".", "_") + ".md")
        self._orig = render_docs.CHANGELOG
        render_docs.CHANGELOG = self.tmp
        if self.tmp.exists():
            self.tmp.unlink()

    def tearDown(self):
        render_docs.CHANGELOG = self._orig
        if self.tmp.exists():
            self.tmp.unlink()

    def test_newest_entry_first(self):
        self.assertTrue(render_docs.append_changelog(["- 第一条"], "2026-11-17 10:00 (UTC+8)"))
        self.assertTrue(render_docs.append_changelog(["- 第二条"], "2026-11-18 09:00 (UTC+8)"))
        text = self.tmp.read_text(encoding="utf-8")
        self.assertLess(text.index("第二条"), text.index("第一条"))
        self.assertIn(render_docs.LOG_BEGIN, text)

    def test_empty_lines_write_nothing(self):
        self.assertFalse(render_docs.append_changelog([], "2026-11-18 09:00 (UTC+8)"))
        self.assertFalse(self.tmp.exists())


class RepoReadmeTests(unittest.TestCase):
    def test_readme_markers_and_rows(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(render_docs.BEGIN, text)
        self.assertIn(render_docs.END, text)
        apps = render_docs.load(ROOT / "apps.json")
        block = text.split(render_docs.BEGIN)[1].split(render_docs.END)[0]
        rows = [line for line in block.splitlines() if line.startswith("| ") and "---" not in line]
        self.assertEqual(len(rows), len(apps) + 1)
        bundles = {a["bundleIdentifier"] for a in apps}
        for bundle in bundles:
            self.assertIn(bundle, block)


if __name__ == "__main__":
    unittest.main()
