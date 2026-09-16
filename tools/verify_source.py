#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apps.json 结构校验：流水线提交前的守门人。

为什么需要它
------------
源文件是端上直接消费的，一旦结构不对（比如某个 app 的 releases 为空数组），
SideStore 解码时会直接抛错，整个源都加载不了。而这类错误在生成阶段往往是
「网络抽风导致某个 app 数据不完整」造成的，肉眼看不出来。所以提交前必须先过一遍。

用法：
    python tools/verify_source.py                 # 校验 ../apps.json
    python tools/verify_source.py --file x.json --min-apps 6
退出码：0 通过，1 有问题。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

TRACKS = {"stable", "alpha", "nightly", "local", "unknown"}
REQ_APP = ["name", "bundleIdentifier", "developerName", "localizedDescription",
           "iconURL", "tintColor", "category", "releaseChannels", "versions"]
REQ_REL = ["version", "date", "downloadURL", "size", "minOSVersion"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def semver(text):
    """把 6.1.0 / v2.3.2 / 2.3.2+245 之类转成可比元组。"""
    nums = re.findall(r"\d+", str(text))
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - min(3, len(nums)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "..", "apps.json"))
    ap.add_argument("--min-apps", type=int, default=1)
    args = ap.parse_args()

    path = os.path.abspath(args.file)
    errs, warns = [], []

    try:
        with open(path, encoding="utf-8") as f:
            src = json.load(f)
    except Exception as e:  # noqa: BLE001
        print("✗ 无法解析 %s：%r" % (path, e), file=sys.stderr)
        return 1

    for k in ("name", "identifier", "apps"):
        if not src.get(k):
            errs.append("源缺少 %s" % k)
    if src.get("identifier") and "." not in src["identifier"]:
        warns.append("identifier 建议用反向域名（当前 %r）" % src["identifier"])

    apps = src.get("apps") or []
    if len(apps) < args.min_apps:
        errs.append("应用数 %d 少于要求的 %d（可能生成不完整）" % (len(apps), args.min_apps))

    seen = set()
    for a in apps:
        nm = a.get("name") or "<未命名>"
        for k in REQ_APP:
            if k not in a:
                errs.append("%s 缺少字段 %s" % (nm, k))
        bid = a.get("bundleIdentifier")
        if bid in seen:
            errs.append("bundleIdentifier 重复：%s" % bid)
        seen.add(bid)
        for u in [a.get("iconURL")] + [v.get("downloadURL") for c in (a.get("releaseChannels") or [])
                                       for v in c.get("releases", [])]:
            if u and not str(u).startswith("https://"):
                errs.append("%s 的 URL 不是 https：%s" % (nm, u))

        chans = a.get("releaseChannels") or []
        tracks = [c.get("track") for c in chans]
        if not chans:
            errs.append("%s 没有 releaseChannels" % nm)
        if tracks.count("stable") != 1:
            errs.append("%s 的 stable 轨道数量应为 1，实际 %d" % (nm, tracks.count("stable")))
        for c in chans:
            t = c.get("track")
            if t not in TRACKS:
                errs.append("%s 出现未知轨道 %r" % (nm, t))
            rels = c.get("releases") or []
            if not rels:
                # SideStore 的 ReleaseTrack 解码时显式拒绝空数组
                errs.append("%s 的 %s 轨道 releases 为空（SideStore 会解码失败）" % (nm, t))
            for v in rels:
                for k in REQ_REL:
                    if k not in v:
                        errs.append("%s/%s 缺少 %s" % (nm, v.get("version"), k))
                if not isinstance(v.get("size"), int) or (v.get("size") or 0) <= 0:
                    errs.append("%s/%s 的 size 非法：%r" % (nm, v.get("version"), v.get("size")))
                if not DATE_RE.match(str(v.get("date") or "")):
                    errs.append("%s/%s 的 date 格式应为 YYYY-MM-DD：%r"
                                % (nm, v.get("version"), v.get("date")))

        # 旧客户端的扁平列表必须与 stable 轨道一致，且不能混入测试版
        stable_vs = [v["version"] for c in chans if c.get("track") == "stable"
                     for v in c.get("releases", [])]
        legacy_vs = [v.get("version") for v in (a.get("versions") or [])]
        if legacy_vs != stable_vs:
            errs.append("%s 的 versions %s 与 stable 轨道 %s 不一致" % (nm, legacy_vs, stable_vs))

        # 测试版版本号必须 >= 稳定版，否则 SideStore 根本不显示
        nightly = [v["version"] for c in chans if c.get("track") == "nightly"
                   for v in c.get("releases", [])]
        if nightly and stable_vs and semver(nightly[0]) < semver(stable_vs[0]):
            warns.append("%s 的测试版 %s 低于稳定版 %s，SideStore 不会显示"
                         % (nm, nightly[0], stable_vs[0]))

    for w in warns:
        print("⚠ %s" % w)
    for e in errs:
        print("✗ %s" % e, file=sys.stderr)
    if errs:
        print("\n校验未通过：%d 个错误" % len(errs), file=sys.stderr)
        return 1

    n_rel = sum(len(c.get("releases", [])) for a in apps for c in a["releaseChannels"])
    print("✓ 校验通过：%d 个应用，%d 条版本记录%s"
          % (len(apps), n_rel, ("，%d 条警告" % len(warns)) if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
