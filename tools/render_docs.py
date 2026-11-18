#!/usr/bin/env python3
"""按 apps.json 刷新 README 的应用清单，并把本轮变化写入 docs/Changelog.md。

设计要点：
  * README 里的表格由 apps.json 生成，避免「说 20 个应用其实有 26 个」这种漂移；
  * Changelog 只在确实有变化时追加（与 git HEAD 的 apps.json 对比），
    没有变化就完全不写文件，避免产生空提交。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CHANGELOG = ROOT / "docs" / "Changelog.md"
NIGHTLY = ROOT / "docs" / "nightly.md"
RELEASES = ROOT / "cache" / "releases.json"
APPS = ROOT / "apps.json"

BEGIN = "<!-- apps:begin -->"
END = "<!-- apps:end -->"
LOG_BEGIN = "<!-- changelog:begin -->"
NIGHTLY_BEGIN = "<!-- nightly:begin -->"
NIGHTLY_END = "<!-- nightly:end -->"

REPO_RE = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
NUM_RE = re.compile(r"\d+")


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["apps"]


def head_apps() -> list[dict]:
    """读取 git HEAD 里的 apps.json；不在仓库或没有历史时返回空列表。"""
    try:
        raw = subprocess.run(
            ["git", "-C", str(ROOT), "show", "HEAD:apps.json"],
            capture_output=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    try:
        return json.loads(raw.decode("utf-8"))["apps"]
    except (ValueError, KeyError):
        return []


def stable(app: dict) -> dict | None:
    for channel in app.get("releaseChannels") or []:
        if channel.get("track") == "stable" and channel.get("releases"):
            return channel["releases"][0]
    versions = app.get("versions") or []
    return versions[0] if versions else None


def beta(app: dict) -> dict | None:
    for channel in app.get("releaseChannels") or []:
        if channel.get("track") != "stable" and channel.get("releases"):
            return channel["releases"][0]
    return None


def upstream(app: dict) -> str:
    match = REPO_RE.search(app.get("localizedDescription") or "")
    if not match:
        match = REPO_RE.search((stable(app) or {}).get("downloadURL") or "")
    if not match:
        return "—"
    owner, name = match.group(0).rstrip("/").rsplit("/", 2)[-2:]
    return "[%s/%s](%s)" % (owner, name, match.group(0))


def cell(value: str) -> str:
    return value.replace("|", "\\|")


def render_table(apps: list[dict]) -> str:
    rows = [
        "| 应用 | Bundle ID | 稳定版 | 最低系统 | 测试版 | 上游 |",
        "|---|---|---|---|---|---|",
    ]
    for app in sorted(apps, key=lambda a: a["name"].lower()):
        cur = stable(app) or {}
        nxt = beta(app)
        rows.append(
            "| %s | `%s` | %s | iOS %s+ | %s | %s |"
            % (
                cell(app["name"]),
                app["bundleIdentifier"],
                cur.get("version", "—"),
                cur.get("minOSVersion", "?"),
                nxt.get("version", "无") if nxt else "无",
                upstream(app),
            )
        )
    return "\n".join(rows)


def replace_block(text: str, begin: str, end: str, body: str) -> str:
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise SystemExit("README 缺少标记块：%s / %s" % (begin, end))
    return pattern.sub(begin + "\n" + body + "\n" + end, text, count=1)


def diff_lines(prev: list[dict], cur: list[dict]) -> list[str]:
    """列出应用级别的变化；没有变化返回空列表。"""
    before = {a["bundleIdentifier"]: a for a in prev}
    after = {a["bundleIdentifier"]: a for a in cur}
    lines: list[str] = []

    for bundle, app in after.items():
        old = before.get(bundle)
        new_version = (stable(app) or {}).get("version") or "?"
        if old is None:
            lines.append("- 新增 **%s** %s" % (app["name"], new_version))
            continue
        old_version = (stable(old) or {}).get("version") or "?"
        if old_version != new_version:
            lines.append("- **%s** %s → %s" % (app["name"], old_version, new_version))
        elif old.get("name") != app.get("name"):
            lines.append("- **%s** 更名为 **%s**" % (old["name"], app["name"]))

    for bundle, app in before.items():
        if bundle not in after:
            lines.append("- 移除 **%s**" % app["name"])

    return lines


def append_changelog(lines: list[str], stamp: str) -> bool:
    if not lines:
        return False
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# 更新记录\n\n"
        "由自动化维护：每轮检测到上游版本变化时追加，最新的在最上面；"
        "没有变化时不写。更早的历史见 git 提交记录。\n\n"
    )
    if CHANGELOG.exists():
        text = CHANGELOG.read_text(encoding="utf-8")
    else:
        text = header + LOG_BEGIN + "\n\n<!-- changelog:end -->\n"
    if LOG_BEGIN not in text:
        raise SystemExit("Changelog 缺少标记：%s" % LOG_BEGIN)
    entry = "## %s\n\n%s\n\n" % (stamp, "\n".join(lines))
    text = text.replace(LOG_BEGIN + "\n", LOG_BEGIN + "\n\n" + entry, 1)
    CHANGELOG.write_text(text, encoding="utf-8")
    return True


def semver(text: str) -> tuple:
    nums = NUM_RE.findall(str(text or ""))
    return tuple(int(x) for x in nums[:3]) + (0,) * (3 - min(3, len(nums)))


def app_configs() -> list[dict]:
    """生成器的应用配置（repo / nightly / prereleaseAsStable）。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_source

    return build_source.APPS


def repo_of(app: dict, configs: list[dict]) -> str | None:
    desc = app.get("localizedDescription") or ""
    for cfg in configs:
        if cfg["repo"] in desc:
            return cfg["repo"]
    return None


def render_nightly_table(apps: list[dict], releases: dict, configs: list[dict]) -> str:
    rows = ["| 应用 | 稳定版 | 最新预发布 | 结论 |", "|---|---|---|---|"]
    for app in sorted(apps, key=lambda a: a["name"].lower()):
        repo = repo_of(app, configs)
        cfg = next((c for c in configs if c["repo"] == repo), {})
        cur = (stable(app) or {}).get("version") or "-"
        pres = [r for r in (releases.get(repo) or []) if r.get("pre") and not r.get("draft")]
        pres.sort(key=lambda r: r.get("published_at") or r.get("date") or "", reverse=True)
        newest = pres[0] if pres else None
        if newest:
            when = newest.get("date") or (newest.get("published_at") or "")[:10]
            col = "%s (%s)" % (newest.get("tag") or "?", when)
        else:
            col = "无"
        if cfg.get("prereleaseAsStable"):
            note = "以预览版作为稳定版"
        elif beta(app):
            note = "收录（nightly 轨道）"
        elif not newest:
            note = "无预发布"
        elif not newest.get("ipas"):
            note = "不收：该预发布没有 iOS 包"
        elif semver(newest.get("tag")) < semver(cur):
            note = "不收：比稳定版旧"
        else:
            note = "不收：未启用 nightly 轨道"
        rows.append("| %s | %s | %s | %s |" % (cell(app["name"]), cur, cell(col), note))
    return chr(10).join(rows)


def refresh_nightly(apps: list[dict]) -> int:
    releases = json.loads(RELEASES.read_text(encoding="utf-8")) if RELEASES.exists() else {}
    text = NIGHTLY.read_text(encoding="utf-8")
    table = render_nightly_table(apps, releases, app_configs())
    NIGHTLY.write_text(replace_block(text, NIGHTLY_BEGIN, NIGHTLY_END, table), encoding="utf-8")
    return len(table.splitlines()) - 2

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None, help="记录用时间（默认取当前 UTC+8）")
    parser.add_argument("--no-changelog", action="store_true", help="只刷新 README 表格")
    args = parser.parse_args(argv)

    apps = load(APPS)
    readme = README.read_text(encoding="utf-8")
    readme = replace_block(readme, BEGIN, END, render_table(apps))
    readme = re.sub(r"收录 \d+ 个 iOS 应用", "收录 %d 个 iOS 应用" % len(apps), readme, count=1)
    README.write_text(readme, encoding="utf-8")
    print("README 应用清单已更新（%d 个应用）" % len(apps))
    print("docs/nightly.md 预发布复核已更新（%d 个应用）" % refresh_nightly(apps))

    if args.no_changelog:
        return 0
    stamp = args.date or datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M (UTC+8)")
    lines = diff_lines(head_apps(), apps)
    if append_changelog(lines, stamp):
        print("Changelog 已追加 %d 条变化" % len(lines))
    else:
        print("无版本变化，Changelog 未改动")
    return 0


if __name__ == "__main__":
    sys.exit(main())
