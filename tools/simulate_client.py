#!/usr/bin/env python3
"""模拟各家客户端如何解析 apps.json —— 在本地回答「改完用户到底看不看得见」。

为什么要这个脚本：源文件「格式正确」和「用户真能看到」是两件事，而且
**不同的客户端解析逻辑完全不同**，同一个 apps.json 在两边会得到不同结果。

──────────── 客户端 A：SideStore / AltStore ────────────
源码 `AltStore/Core/Model/StoreApp.swift` 的 `decodeVersions`：

    var versions = getReleases(default: stableTrack) ?? []
    if versions.isEmpty {
        if let appVersions = try container.decodeIfPresent([AppVersion].self, forKey: .versions) {
            versions = appVersions
        } else {
            // 再退到 app 级单版本字段（version / downloadURL / versionDate…）
        }
    }

  · 优先读 `releaseChannels` 里的轨道；**只有轨道取不到东西时才回头看扁平 `versions`**。
    也就是说：只要 stable 轨道非空，扁平 `versions` 里的内容会被彻底忽略 ——
    所以往扁平列表塞测试版，对 SideStore 没有任何副作用（本脚本可验证）。
  · 测试版是否显示由 `betaReleases` 决定：

        if isBetaUpdatesEnabled,                        // ① 设置开关，默认 false
           let betaTrack = betaUdpatesTrack             // ② 轨道名，默认 "nightly"
        { ... betaSemVer >= stableSemVer ... }          // ③ 版本号门槛

  · 开关打开时 beta 轨道会**取代** stable，不是合并。

──────────── 客户端 B：LiveContainer ────────────
源码 `LiveContainerSwiftUI/Views/LCAltStoreSourcesView.swift`：

    let versions = buildVersions(from: response, baseURL: baseURL)   // 只读扁平 versions
    let latest   = versions.first ?? buildLegacyVersion(from: response, baseURL: baseURL)
    ...
    isBeta: response.beta ?? false

  · **完全不认识 `releaseChannels`**，只读扁平 `versions` 数组。
  · **没有 beta 开关、没有版本选择器**，界面上只显示 `versions[0]`，安装也只装它。
    → 结论：想让测试版在 LiveContainer 里可见，唯一办法是把它放进扁平 versions
      并排到第一位（本脚本会替你确认排没排对）。
  · 两处专有约定：
      - 版本条目的 buildVersion 它解码的键名是 **`buildNumber`**（不是 buildVersion），
        见 `AltStoreSourceAppVersionResponse.CodingKeys`。两个键都写最稳。
      - app 级 `"beta": true` → 列表里显示橙色 BETA 角标。
        （SideStore 也认 `beta` 键（`case isBeta = "beta"`），但只在上面的兜底分支里读，
          有 releaseChannels 时同样不生效。）

另有两条硬约束（CoreData 模型，改源时必须遵守）：
  StoreApp     唯一约束 (sourceIdentifier, bundleIdentifier)
      → 同源里不能有两个相同 bundleIdentifier 的应用条目，会被合并。
        所以「把测试版拆成独立 app」必须换 bundleIdentifier；换了就不等于 IPA 内真实 ID，
        安装时会被 VerifyAppOperation 以 mismatchedBundleIdentifiers 拦下
        （安装流水线第 2 步，校验默认开启且**没有界面开关**）。
  ReleaseTrack 唯一约束 (sourceID, appBundleID, track)
      → 同一 app 的 releaseChannels 里 track 名不能重复。

用法：
  python tools/simulate_client.py                     # 两个客户端都算
  python tools/simulate_client.py --client sidestore
  python tools/simulate_client.py --client livecontainer
  python tools/simulate_client.py --strict            # 有「必须开开关才可见」的测试版时退出码 1
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


# ---------------------------------------------------------------- SideStore

def resolve_sidestore(app, beta_enabled, beta_track=DEFAULT_BETA_TRACK):
    """返回 (展示的版本列表, 说明)。对齐 decodeVersions → getReleases(default:)。"""
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
            # 因此只要 minOSVersion 存在即视为「可能支持」。
            lb = next((v for v in beta if v.get("minOSVersion")), None)
            ls = next((v for v in stable if v.get("minOSVersion")), None)
            if lb and ls and semver(lb.get("version")) >= semver(ls.get("version")):
                return beta, "开关 ON + 轨道 %s → 返回 beta 轨道" % beta_track

    return stable, "开关 OFF（或门槛不满足）→ 返回 stable 轨道"


# ---------------------------------------------------------- LiveContainer

def resolve_livecontainer(app):
    """返回 (会安装的那个版本 dict 或 None, 说明)。

    LiveContainer 只读扁平 versions、只取第 1 条；没有轨道、没有开关、没有版本选择器。
    """
    flat = app.get("versions") or []
    if flat:
        return flat[0], "扁平 versions[0]"
    # 回退到 app 级旧式单版本字段（buildLegacyVersion）
    if app.get("version") and app.get("downloadURL"):
        return {
            "version": app.get("version"),
            "date": app.get("versionDate"),
            "downloadURL": app.get("downloadURL"),
            "size": app.get("size"),
            "minOSVersion": app.get("minOSVersion"),
        }, "app 级 legacy 单版本字段"
    return None, "扁平 versions 与 legacy 字段都取不到 → 这一条在 LiveContainer 里是死的"


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=DEFAULT_SRC)
    ap.add_argument("--client", choices=("both", "sidestore", "livecontainer"), default="both",
                    help="要模拟哪个客户端（默认两个都算）")
    ap.add_argument("--strict", action="store_true",
                    help="存在「必须开开关才可见」的测试版时退出码 1")
    ap.add_argument("--track", default=DEFAULT_BETA_TRACK)
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as f:
        src = json.load(f)

    want_ss = args.client in ("both", "sidestore")
    want_lc = args.client in ("both", "livecontainer")

    print("源名称: %s" % src.get("name"))
    print("identifier: %s" % src.get("identifier"))
    print("源图标: %s" % (src.get("iconURL") or "（未设置）"))
    if want_ss:
        print("SideStore 可用测试轨道（下拉框只会给这些）: %s" % ", ".join(BETA_TRACKS))
        print("SideStore 默认轨道 = %r（UserDefaults 默认值）" % DEFAULT_BETA_TRACK)
    if want_lc:
        print("LiveContainer: 不认 releaseChannels，只读扁平 versions 且只取第 1 条")
    print()

    hidden_beta = []
    divergence = []

    for app in src.get("apps", []):
        name = app.get("name")
        bid = app.get("bundleIdentifier")
        has_channels = app.get("releaseChannels") is not None
        print("=" * 74)
        print(" %s   (%s)" % (name, bid))

        ss_on_v, lc_v = [], None

        if want_ss:
            off, why_off = resolve_sidestore(app, beta_enabled=False, beta_track=args.track)
            on, why_on = resolve_sidestore(app, beta_enabled=True, beta_track=args.track)
            off_v = [v.get("version") for v in off]
            ss_on_v = [v.get("version") for v in on]
            extra = [v for v in ss_on_v if v not in off_v]

            print("   SideStore · 关 Beta → %s" % (off_v or "（空！源会被判定为坏）"))
            print("   SideStore · 开 Beta → %s" % (ss_on_v or "（空！）"))
            if extra:
                print("      ⚠️ %s 只有开了 Beta 开关才可见（%s）" % (extra, why_on))
                hidden_beta.append((name, extra))
            elif not has_channels:
                # 旧式源：没有 releaseChannels → betaReleases 恒为 nil → 预发布永远可见
                print("      ✓ 两态一致，原因是「没有 releaseChannels」：")
                print("        客户端只读扁平 versions，betaReleases 恒为 nil，"
                      "列在这里的预发布会**一直可见**，开关管不着。")
            else:
                print("      ✓ 两态一致（该应用没有可用的测试轨道）")

        if want_lc:
            pick, why = resolve_livecontainer(app)
            if pick is None:
                print("   LiveContainer → ✗ %s" % why)
                lc_v = None
            else:
                lc_v = pick.get("version")
                badge = "  [BETA 角标]" if app.get("beta") else ""
                build = pick.get("buildNumber") or pick.get("buildVersion")
                btxt = " (%s)" % build if build else ""
                if not pick.get("buildNumber") and pick.get("buildVersion"):
                    btxt += "  ← 注意：LiveContainer 读的是 buildNumber，这版只有 buildVersion，角标处不会显示构建号"
                print("   LiveContainer       → 会安装 %s%s%s   [来源：%s]"
                      % (lc_v, btxt, badge, why))
                if pick.get("minOSVersion"):
                    print("                          最低系统 %s" % pick["minOSVersion"])

        # 两个客户端结论是否一致？不一致不一定是错，但要让人知道
        if want_ss and want_lc and ss_on_v and lc_v and lc_v not in ss_on_v:
            msg = "%s：LiveContainer 会装 %s，但即便开着 Beta，SideStore 的候选里也没有它" % (name, lc_v)
            divergence.append(msg)
            print("      ⚠️ 客户端分歧：%s" % msg)

        # 顺带体检：唯一约束不能在源内被违反
        dup = {}
        for v in app.get("versions") or []:
            k = (v.get("version"), v.get("buildVersion"))
            dup[k] = dup.get(k, 0) + 1
        bad = [k for k, n in dup.items() if n > 1]
        if bad:
            print("   ✗ 扁平 versions 内重复 (version, buildVersion): %s" % bad)

    print()
    print("=" * 74)
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
        print("提示：以下测试版需要用户在 SideStore 里打开开关才可见：")
        for n, vs in hidden_beta:
            print("  - %s: %s" % (n, vs))
        print("  路径：设置 → Beta Testing（测试版）→ 打开 Beta Updates（轨道默认 %s，无需改）"
              % DEFAULT_BETA_TRACK)
        print("  ⚠️ LiveContainer 没有这个开关 —— 那边靠的是扁平 versions[0]，不是轨道。")

    if divergence:
        print()
        print("提示：以下条目两个客户端结论不同（通常意味着扁平 versions 忘了放测试版）：")
        for m in divergence:
            print("  - %s" % m)

    if args.strict and hidden_beta:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
