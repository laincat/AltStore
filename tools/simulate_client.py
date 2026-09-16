#!/usr/bin/env python3
"""模拟 SideStore 客户端如何解析 apps.json —— 在本地回答「改完到底看不看得见」。

为什么要这个脚本：源文件「格式正确」和「用户真能看到」是两件事。
测试版会不会出现，完全由客户端的一段门控逻辑决定，那段逻辑在 SideStore
源码 `AltStore/Core/Model/StoreApp.swift` 的 `betaReleases` 里：

    private var betaReleases: [AppVersion]? {
        if UserDefaults.standard.isBetaUpdatesEnabled,             // ① 设置里的开关，默认 false
           let betaTrack = UserDefaults.standard.betaUdpatesTrack  // ② 轨道名，默认 "nightly"
        {
            let betaReleases = releaseTrackFor(track: betaTrack)?.releases?.compactMap { $0 }
            if let latestBeta   = betaReleases?.first(where: { $0.isSupported }),
               let latestStable = stableTrack?.releases?.first(where: { $0.isSupported }),
               let stableSemVer = SemanticVersion(latestStable.version),
               let betaSemVer   = SemanticVersion(latestBeta.version),
               betaSemVer >= stableSemVer                          // ③ 版本号门槛
            { return betaReleases }
        }
        return nil
    }
    // 最终展示的版本列表：
    var versions = getReleases(default: stableTrack) ?? []   // betaReleases ?? stableTrack.releases

另有两条硬约束（都在 CoreData 模型里，改源时必须遵守）：
  StoreApp     唯一约束 (sourceIdentifier, bundleIdentifier)
      → 同一个源里不能出现两个相同 bundleIdentifier 的应用条目，会被合并成一个。
        所以「把测试版拆成独立 app」必须换 bundleIdentifier；而换了就不等于 IPA 内真实 ID，
        安装时会被 VerifyAppOperation 以 mismatchedBundleIdentifiers 拦下
        （安装流水线第 2 步，校验默认开启且**没有界面开关**）。
  ReleaseTrack 唯一约束 (sourceID, appBundleID, track)
      → 同一个 app 的 releaseChannels 里 track 名不能重复。

用法：
  python tools/simulate_client.py                 # 报告两种开关状态下的可见结果
  python tools/simulate_client.py --strict        # 有「必须开开关才可见」的测试版时退出码 1
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(os.path.dirname(HERE), "apps.json")

# UserDefaults+AltStore.swift: static let defaultBetaUpdatesTrack = ReleaseTrackType.nightly.description
DEFAULT_BETA_TRACK = "nightly"
# ReleaseTrack.swift: betaTracks = allCases.filter { $0 == .alpha || $0 == .nightly }
BETA_TRACKS = ("alpha", "nightly")


def semver(s):
    """把 '3.0.0' / '1.2.3-beta01' 拆成可比较的元组（对齐客户端 SemanticVersion 的足够近似）。"""
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(s or "").strip())
    if not m:
        return (0, 0, 0)
    return tuple(int(g or 0) for g in m.groups())


def track_of(app, name):
    for ch in app.get("releaseChannels") or []:
        if ch.get("track") == name:
            return ch.get("releases") or []
    return None


def resolve_visible(app, beta_enabled, beta_track=DEFAULT_BETA_TRACK):
    """返回 (实际展示的版本列表, 说明)。对齐 decodeVersions → getReleases(default:)。"""
    tracks = app.get("releaseChannels")
    stable = track_of(app, "stable") or []

    if tracks is None:
        # 没有 releaseChannels：客户端走扁平的 versions 数组（旧式源）
        flat = app.get("versions") or []
        return flat, "无 releaseChannels，用扁平 versions"

    if beta_enabled:
        beta = track_of(app, beta_track)
        if beta:
            # isSupported：客户端按设备 iOS 版本过滤。本机无法得知用户设备，
            # 因此只要 minOSVersion 存在即视为「可能支持」，并把结果标注出来。
            lb = next((v for v in beta if v.get("minOSVersion")), None)
            ls = next((v for v in stable if v.get("minOSVersion")), None)
            if lb and ls and semver(lb.get("version")) >= semver(ls.get("version")):
                return beta, f"开关 ON + 轨道 {beta_track} → 返回 beta 轨道"

    return stable, "开关 OFF（或门槛不满足）→ 返回 stable 轨道"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=DEFAULT_SRC)
    ap.add_argument("--strict", action="store_true",
                    help="存在「必须开开关才可见」的测试版时退出码 1")
    ap.add_argument("--track", default=DEFAULT_BETA_TRACK)
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as f:
        src = json.load(f)

    print("源名称: %s" % src.get("name"))
    print("identifier: %s" % src.get("identifier"))
    print("可用测试轨道（客户端下拉框只会给这些）: %s" % ", ".join(BETA_TRACKS))
    print()
    print("默认轨道 = %r（客户端 UserDefaults 默认值）" % DEFAULT_BETA_TRACK)
    print()

    hidden_beta = []
    for app in src.get("apps", []):
        name = app.get("name")
        bid = app.get("bundleIdentifier")
        off, why_off = resolve_visible(app, beta_enabled=False, beta_track=args.track)
        on, why_on = resolve_visible(app, beta_enabled=True, beta_track=args.track)

        off_v = [v.get("version") for v in off]
        on_v = [v.get("version") for v in on]
        extra = [v for v in on_v if v not in off_v]

        print("=" * 70)
        print(" %s   (%s)" % (name, bid))
        print("   开关 OFF → 看到 %s" % (off_v or "（空！源会被判定为坏）"))
        print("   开关 ON  → 看到 %s" % (on_v or "（空！）"))
        if extra:
            print("   ⚠️ 多出来的测试版 %s 只有开了开关才可见（%s）" % (extra, why_on))
            hidden_beta.append((name, extra))
        else:
            print("   ✓ 两种状态下一致")

        # 顺带体检：唯一约束不能在源内被违反
        dup = {}
        for v in app.get("versions") or []:
            k = (v.get("version"), v.get("buildVersion"))
            dup[k] = dup.get(k, 0) + 1
        for ch in app.get("releaseChannels") or []:
            for v in ch.get("releases") or []:
                k = (v.get("version"), v.get("buildVersion"))
                dup.setdefault(k, 0)
        bad = [k for k, n in dup.items() if n > 1]
        if bad:
            print("   ✗ versions 数组内重复 (version, buildVersion): %s" % bad)

    print()
    print("=" * 70)
    # 跨条目检查 StoreApp 唯一约束 (sourceIdentifier, bundleIdentifier)
    seen = {}
    for app in src.get("apps", []):
        seen.setdefault(app.get("bundleIdentifier"), []).append(app.get("name"))
    clash = {k: v for k, v in seen.items() if len(v) > 1}
    if clash:
        print("✗ 违反 StoreApp 唯一约束 (sourceIdentifier, bundleIdentifier)：%s" % clash)
        print("  这些条目会被客户端合并成一个。")
    else:
        print("✓ bundleIdentifier 无重复，不触发 StoreApp 唯一约束")

    if hidden_beta:
        print()
        print("提示：以下测试版需要用户在客户端里打开开关才可见：")
        for n, vs in hidden_beta:
            print("  - %s: %s" % (n, vs))
        print("  路径：设置 → Beta Testing（测试版）→ 打开 Beta Updates（轨道默认 %s，无需改）"
              % DEFAULT_BETA_TRACK)
        if args.strict:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
