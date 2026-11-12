"""自有上游配置的离线回归：不联网、不改线上文件。"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_source as b  # noqa: E402
import verify_source as vs  # noqa: E402


def all_urls(cfg):
    out = []
    for key in ("iconURL", "installNotesSource"):
        if cfg.get(key):
            out.append(cfg[key])
    out.extend(cfg.get("screenshots", []))
    out.append(cfg.get("description", ""))
    return out


class UpstreamAppsTests(unittest.TestCase):
    def test_apps_are_complete_and_each_has_its_own_repo(self):
        self.assertEqual(len(b.BASE_APPS), 25)
        self.assertEqual(len(b.UPSTREAM_APPS), 52)
        self.assertEqual(len(b.APPS), 77)
        repos = [a["repo"] for a in b.APPS]
        self.assertEqual(len(set(repos)), 77, "两个应用不能指向同一个上游 repo")
        for a in b.APPS:
            for key in ("name", "developerName", "subtitle", "description",
                        "tintColor", "category", "asset"):
                self.assertIn(key, a, "%s 缺 %s" % (a.get("repo"), key))

    def test_no_third_party_aggregator_anywhere_in_config(self):
        for a in b.UPSTREAM_APPS:
            for u in all_urls(a):
                self.assertNotIn("altgallery", u.lower(),
                                 "%s 仍指向第三方聚合源：%s" % (a["repo"], u[:100]))

    def test_generated_source_has_no_aggregator_dependency(self):
        raw = (ROOT / "apps.json").read_text(encoding="utf-8")
        self.assertNotIn("altgallery", raw.lower())
        src = json.loads(raw)
        self.assertEqual(src["identifier"], "com.acgtoolbox.source")
        self.assertEqual(len(src["apps"]), 77)
        ids = [a["bundleIdentifier"] for a in src["apps"]]
        self.assertEqual(len(set(ids)), 77)
        self.assertEqual(len({a["name"] for a in src["apps"]}), 77)
        self.assertEqual(vs.validate(src, min_apps=len(b.APPS)), [])
        self.assertGreaterEqual(len([a for a in src["apps"] if a.get("installNotes")]), 28)
        self.assertGreaterEqual(len([a for a in src["apps"] if a.get("screenshots")]), 28)
        self.assertGreaterEqual(len(src["news"]), 70)
        for a in src["apps"]:
            for u in a.get("screenshots", []):
                self.assertTrue(u.startswith("https://raw.githubusercontent.com/"),
                                "%s 的截图不是上游自有：%s" % (a["name"], u))

    def test_min_os_fallback_is_explicit_and_documented(self):
        # 上游 IPA 实测缺 MinimumOSVersion；只允许按上游 README 明示值兜底，
        # 防止以后有人「顺手」改成给所有应用填 15.0 之类的默认值。
        self.assertEqual(b.MIN_OS_FALLBACKS, {"lpfoj/lsx4": "26.0"})
        lsx4 = next(a for a in b.UPSTREAM_APPS if a["repo"] == "lpfoj/lsx4")
        self.assertIn("README", lsx4["installNotes"])
        self.assertIn("26.0", lsx4["installNotes"])

    def test_make_versions_uses_only_documented_min_os_fallback(self):
        picks = [(dict(tag_name="t1", published_at="2026-11-01T00:00:00Z",
                       body="", prerelease=False),
                  dict(id=1, name="a.ipa", size=1,
                       browser_download_url="https://github.com/x/y/releases/download/t/a.ipa"))]
        missing = dict(bundleIdentifier="com.x", version="1.0", buildVersion="1",
                       displayName="X", minOSVersion="", size=1)
        orig = b.probe_cached
        b.probe_cached = lambda *a, **k: dict(missing)
        try:
            ok, _ = b.make_versions(picks, "lpfoj/lsx4")
            self.assertEqual(len(ok), 1)
            self.assertEqual(ok[0]["minOSVersion"], "26.0")
            none, _ = b.make_versions(picks, "some/unknown-repo")
            self.assertEqual(none, [], "没有上游明示值时必须跳过，不能猜")
        finally:
            b.probe_cached = orig

    def test_prerelease_as_stable_only_for_all_prerelease_repos(self):
        flagged = {a["repo"] for a in b.UPSTREAM_APPS if a.get("prereleaseAsStable")}
        self.assertEqual(flagged, {
            "OatmealDome/dolphin-ios", "kuscholar/iDeck", "xmiguel911x/PSX3IOS"})

    def test_asset_patterns_match_real_upstream_asset_names(self):
        # 实测过的真实资产名；这些以前全都失配过，写成断言防回归
        cases = {
            "LiveContainer/LiveContainer": "LiveContainer+SideStore.ipa",
            "bggRGjQaUbCoE/PiliPlus": "PiliPlus_ios_2.2.0+5598.ipa",
            "kuscholar/iDeck": "iDeck-0.1.3-alpha.6-build145.ipa",
            "xmiguel911x/PSX3IOS": "PSX3IOS-beta.0.2.7-unsigned.ipa",
            "OatmealDome/dolphin-ios": "Non-Jailbroken.ipa",
            "Apollo-Reborn/Apollo-Reborn": "Apollo-Reborn-4.0.1-GLASS.ipa",
            "lpfoj/lsx4": "LSX4-JIT-128.9934.ipa",
            "altstoreio/AltStore": "AltStore_Classic_Notarized_2_3.ipa",
        }
        by_repo = {a["repo"]: a for a in b.UPSTREAM_APPS}
        for repo, name in cases.items():
            self.assertTrue(by_repo[repo]["asset"](name),
                            "%s 的 asset 规则匹配不到 %s" % (repo, name))
        # Apollo 同 release 还有另外 5 个变体，规则不能把它们也吃进来
        apollo = by_repo["Apollo-Reborn/Apollo-Reborn"]["asset"]
        for wrong in ("Apollo-Reborn-4.0.1-GLASS-NOEXTENSIONS.ipa",
                      "Apollo-Reborn-4.0.1-GLASSICONS.ipa",
                      "Apollo-Reborn-4.0.1-NOEXTENSIONS.ipa"):
            self.assertFalse(apollo(wrong), "Apollo 规则误选了变体 %s" % wrong)

    def test_verify_auto_follows_apps_length(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "verify_source.py"), "--min-apps", "auto"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("APPS=%d" % len(b.APPS), proc.stdout)
        self.assertIn("validation passed", proc.stdout)

    def test_four_official_bundle_ids_are_real_and_documented(self):
        ids = {"com.rileytestut.AltStore": "altstoreio/AltStore",
               "com.SideStore.SideStore": "SideStore/SideStore",
               "com.christianselig.Apollo": "Apollo-Reborn/Apollo-Reborn",
               "com.google.ios.youtube": "mrdrvt99/YouProEXTRA"}
        by_repo = {a["repo"]: a for a in b.UPSTREAM_APPS}
        src = json.loads((ROOT / "apps.json").read_text(encoding="utf-8"))
        by_id = {a["bundleIdentifier"]: a for a in src["apps"]}
        for bid, repo in ids.items():
            self.assertIn(bid, by_id, "%s 没进源" % bid)
            self.assertTrue(by_id[bid]["installNotes"],
                            "%s 没有 Bundle ID 出处说明" % bid)
            self.assertTrue(by_repo[repo]["installNotes"],
                            "%s 配置里没有出处说明" % repo)


class _noop:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


if __name__ == "__main__":
    unittest.main()
