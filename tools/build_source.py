#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SideStore / AltStore 源文件生成器（仅用标准库，可离线复跑）
-----------------------------------------------------------
流程：
  1. 调 GitHub API 拉取每个仓库的 Release（区分稳定版 / 预发布版）
  2. 对每个 IPA 发 HTTP Range 请求，只读取包内 Info.plist（约 100KB/个，不下载整包）
     从而拿到真实 CFBundleIdentifier / 版本号 / MinimumOSVersion / 体积
  3. 输出符合 AltStore 源格式规范的 apps.json

输出结构（v2 源格式）：
  apps[].releaseChannels = [
      {"track": "stable",  "releases": [...]},
      {"track": "nightly", "releases": [...]}   # 仅配置了 nightly 的应用
  ]
  apps[].versions = 「所有轨道合并、按日期倒序」的扁平列表。

  ⚠️ 两个客户端的解析逻辑完全不同，改动这里前务必先看 tools/simulate_client.py：

  【SideStore / AltStore】StoreApp.swift decodeVersions():
        var versions = getReleases(default: stableTrack) ?? []
        if versions.isEmpty { ...才回退去读扁平的 versions... }
      → 有 releaseChannels 且 stable 轨道非空时，**扁平 versions 被彻底忽略**。
        beta 默认隐藏，要用户手动开「Beta Testing」开关 + 版本号 >= stable 才显示。
        （所以往扁平 versions 里塞测试版，对 SideStore 没有任何副作用 —— 这是实测过的。）

  【LiveContainer】LCAltStoreSourcesView.swift:
        let versions = buildVersions(...)          // 只读扁平 versions
        let latest   = versions.first ?? 旧式单版本字段
      → **完全不认识 releaseChannels**，也没有 beta 开关、没有版本选择器，
        没得选，永远只显示并安装 versions[0]。所以「测试版在 LiveContainer 里看不见」
        的唯一解法就是把测试版放进扁平 versions 并排到第一位。

  另外两处 LiveContainer 专有约定（SideStore 会无视，多写不冲突）：
    · 版本条目的 buildVersion 它读的是 `buildNumber` 键 → 本脚本两个键都写
    · app 级 `"beta": true` 会在 LiveContainer 里显示橙色 BETA 角标

用法：
  python build_source.py                 # 生成 ../apps.json（稳定版取最新 1 个）
  python build_source.py --out x.json    # 指定输出
  python build_source.py --versions 4    # 稳定版轨道保留最近 4 个
  python build_source.py --refresh       # 强制联网重新抓取
"""
import argparse
import json
import os
import plistlib
import re
import ssl
import struct
import sys
import urllib.request
import zlib

ssl._create_default_https_context = ssl._create_unverified_context
UA = {"User-Agent": "Mozilla/5.0"}
# GitHub 直连在大陆可能很慢/超时，这里按顺序回退到公共加速节点
MIRRORS = ["", "https://gh-proxy.com/", "https://ghfast.top/"]

SOURCE = {
    "name": "Laincat 工具箱",
    # ⚠️ identifier 故意不改：SideStore 用 identifier 认源，改了会被当成一个「新源」，
    #    设备上旧的源还在、要手动删，且所有源内应用的缓存数据会重建。
    "identifier": "com.acgtoolbox.source",
    # 源列表里显示的那个 logo。用 GitHub 头像地址：
    # github.com/<user>.png 会 302 到 avatars.githubusercontent.com，实测
    # 普通 GET 与 Range 请求都能拿到 image/jpeg，客户端都会跟随跳转。
    # 好处是头像换了源里自动跟着变，不用改这里。
    "iconURL": "https://github.com/laincat.png?size=512",
    "subtitle": "番剧 · 漫画 iOS 自签源",
    "description": (
        "收录 7 款开源 iOS 应用：番剧类 Kazumi、Animeko，漫画阅读类 EhPanda、"
        "VeneraX、Venera Prime、Breeze、PicaX。所有 IPA 均直连各项目 GitHub Release "
        "官方资产，由 SideStore / AltStore / LiveContainer 本地签名安装。"
    ),
    "tintColor": "#7C5CFF",
}

APPS = [
    {
        "repo": "Predidit/Kazumi",
        "asset": lambda n: n.startswith("Kazumi_ios_") and n.endswith(".ipa"),
        "name": "Kazumi",
        "developerName": "Predidit",
        "subtitle": "自定义规则的番剧采集与在线观看",
        "category": "entertainment",
        "tintColor": "#E86AA6",
        "icon": "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png",
        "description": (
            "基于自定义规则的番剧采集 App，支持流媒体在线观看、弹幕与实时超分辨率。"
            "支持多平台，此处为未签名 iOS 构建，需自行签名安装。\n\n"
            "开源协议：GPL-3.0　·　项目主页：https://github.com/Predidit/Kazumi"
        ),
    },
    {
        "repo": "open-ani/animeko",
        "asset": lambda n: n.endswith(".ipa"),
        # Animeko 的预发布节奏是 alpha01→alpha02→…→beta01→…→正式版，
        # 每个预发布都带真 ipa（ani-<ver>.ipa），所以 nightly 直接取「最新的预发布」。
        # ⚠️ 注意：开了 nightly 之后，扁平 versions[0] 会变成预发布 ——
        #    LiveContainer 没有开关也没有版本选择器，会直接装它；
        #    SideStore 侧不受影响，stable 轨道仍是正式版。
        "nightly": True,
        "name": "Animeko",
        "developerName": "open-ani",
        "subtitle": "一站式弹幕追番平台",
        "category": "entertainment",
        "tintColor": "#3B82F6",
        "icon": "app/ios/Animeko/Assets.xcassets/AppIcon.appiconset/1024.png",
        "description": (
            "集找番、追番、看番于一体的弹幕追番平台，支持 Bangumi 云收藏同步、"
            "离线缓存、BitTorrent 与弹幕云过滤。100% Kotlin / Compose Multiplatform 实现。\n\n"
            "开源协议：AGPL-3.0　·　项目主页：https://github.com/open-ani/animeko"
        ),
    },
    {
        "repo": "EhPanda-Team/EhPanda",
        "asset": lambda n: n == "EhPanda.ipa",
        # 有真实可用测试版：3.0.0（比稳定版 2.8.1 新，含离线下载）
        "nightly": True,
        "name": "EhPanda",
        "developerName": "EhPanda Team",
        "subtitle": "非官方 E-Hentai 客户端",
        "category": "books",
        "tintColor": "#8E8E93",
        "icon": "EhPanda/App/Assets.xcassets/AppIcon.appiconset/1024.png",
        "description": (
            "使用 SwiftUI 与 TCA 架构开发的非官方 E-Hentai 客户端。"
            "注意：2.8.x 起最低要求 iOS 26.0，旧版 2.7.x 要求 iOS 17.0，"
            "系统低于 17.0 无法安装。\n\n"
            "开源协议：MIT　·　项目主页：https://github.com/EhPanda-Team/EhPanda"
        ),
    },
    {
        "repo": "Kyosee/VeneraX",
        "asset": lambda n: "-ios-" in n and n.endswith(".ipa"),
        "name": "VeneraX",
        "developerName": "Kyosee",
        "subtitle": "多图源漫画阅读器",
        "category": "books",
        "tintColor": "#4A8FE7",
        "icon": "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png",
        "description": (
            "原版 Venera 的个人维护增强分支，支持通过插件接入多种漫画图源，"
            "提供本地收藏、阅读进度同步等能力。\n\n"
            "开源协议：GPL-3.0　·　项目主页：https://github.com/Kyosee/VeneraX"
        ),
    },
    {
        "repo": "venera-app/venera-prime",
        # 资产名形如 venera-prime-ios-2.4.0+240.ipa。
        # ⚠️ 同一个 release 里有 14 个资产（3 个 apk、dmg、AppImage×2、deb×2、
        #    pkg.tar.zst×2、exe、zip、ipa），必须「前缀 + .ipa 后缀」才唯一命中（实测 1/14）。
        "asset": lambda n: n.startswith("venera-prime-ios-") and n.endswith(".ipa"),
        "name": "Venera Prime",
        "developerName": "venera-app",
        "subtitle": "次世代多图源漫画阅读器",
        "category": "books",
        # 用上游自己的品牌色，和 VeneraX 的 #4A8FE7 区分开（两者都是蓝色系）。
        "tintColor": "#0784FC",
        # ⚠️ 这个仓库默认分支是 master（不是 main）。
        #    但取图标用的是 release tag 作 ref（见 build() 里的 icon 拼装），
        #    所以分支叫什么都不影响；路径只要在该 tag 下存在即可（已实测 200 / image/png）。
        "icon": "assets/app_icon.png",
        "description": (
            "原版 Venera 的次世代重写版，Flutter + Rust 构建。支持本地漫画与网络图源阅读、"
            "用 JavaScript 编写自定义漫画源、收藏管理、下载、评论与标签查看；"
            "中文标签翻译来自 EhTagTranslation 项目。\n\n"
            "注意：这与源里的 VeneraX 是两个独立应用（Bundle ID 不同），可以同时安装。\n\n"
            "开源协议：GPL-3.0　·　项目主页：https://github.com/venera-app/venera-prime"
        ),
    },
    {
        "repo": "deretame/Breeze",
        "asset": lambda n: n.lower().endswith(".ipa"),
        "name": "Breeze",
        "developerName": "deretame",
        "subtitle": "插件化漫画阅读器",
        "category": "books",
        "tintColor": "#4FB3F5",
        "icon": "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png",
        "description": (
            "使用 Flutter 构建的漫画阅读器，通过插件机制提供漫画源支持，"
            "已支持哔咔、禁漫、E-Hentai、nhentai、拷贝漫画、包子漫画等多个图源。\n\n"
            "开源协议：MPL-2.0　·　项目主页：https://github.com/deretame/Breeze"
        ),
    },
    {
        "repo": "youshen2/PicaX",
        "asset": lambda n: n == "PicaX-unsigned.ipa",
        "name": "PicaX",
        "developerName": "youshen2",
        "subtitle": "iOS 原生聚合漫画阅读器",
        "category": "books",
        "tintColor": "#FF5C7A",
        "icon": "PicaX/Assets.xcassets/AppIcon.appiconset/app_icon_1024.png",
        "description": (
            "使用 SwiftUI 开发、面向 iOS 的聚合漫画阅读器。"
            "此处选用不含 Watch 组件的未签名包，避免免费账号签名时因附加 Target 失败。\n\n"
            "开源协议：MPL-2.0　·　项目主页：https://github.com/youshen2/PicaX"
        ),
    },
]


# ---------- 网络 ----------
def fetch(url, start=None, end=None, timeout=60):
    headers = dict(UA)
    if start is not None:
        headers["Range"] = "bytes=%d-%d" % (start, end)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers)


def fetch_ranged(url, start, end, attempts=2):
    """带加速镜像回退 + 重试的 Range 请求（大陆直连 GitHub 偶发超时）。"""
    last = None
    for m in MIRRORS:
        for _ in range(attempts):
            try:
                data, _ = fetch((m + url) if m else url, start, end)
                if data:
                    return data
            except Exception as e:  # noqa: BLE001
                last = e
    raise last


def remote_total(url):
    """取远端文件总长度，同样带镜像回退与重试。"""
    last = None
    for m in MIRRORS:
        for _ in range(2):
            try:
                _, h = fetch((m + url) if m else url, 0, 0)
                cr = h.get("Content-Range") or ""
                if "/" in cr:
                    return int(cr.split("/")[-1])
            except Exception as e:  # noqa: BLE001
                last = e
    raise last


def gh_json(url, timeout=60):
    """调 GitHub API，带镜像回退。

    gh-proxy.com 实测可代理 api.github.com（ghfast.top 不行，会 403）。
    未登录的 API 限流是 60 次/小时/IP，CI 上可能撞到；有 GITHUB_TOKEN 就带上。
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    last = None
    for m in MIRRORS:
        try:
            target = (m + url) if m else url
            headers = dict(UA)
            headers["Accept"] = "application/vnd.github+json"
            if token:
                headers["Authorization"] = "Bearer %s" % token
            req = urllib.request.Request(target, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and "rate limit" in str(data.get("message", "")).lower():
                last = RuntimeError(data["message"])
                continue
            return data
        except Exception as e:  # noqa: BLE001
            last = e
    raise last if last else RuntimeError("GitHub API 请求失败：%s" % url)


# ---------- 解析远端 IPA ----------
def probe_ipa(url):
    """只下载 zip 尾部目录 + Info.plist 压缩块，解析出包内元数据。"""
    total = remote_total(url)
    tail_len = min(200000, total)
    tail = fetch_ranged(url, total - tail_len, total - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RuntimeError("未找到 zip 中央目录（EOCD）")
    cd_size, cd_off = struct.unpack_from("<II", tail, i + 12)
    cd = fetch_ranged(url, cd_off, cd_off + cd_size - 1)

    p, n, info = 0, len(cd), None
    while p + 46 <= n and cd[p:p + 4] == b"PK\x01\x02":
        method = struct.unpack_from("<H", cd, p + 10)[0]
        csize = struct.unpack_from("<I", cd, p + 20)[0]
        fnl = struct.unpack_from("<H", cd, p + 28)[0]
        exl = struct.unpack_from("<H", cd, p + 30)[0]
        cml = struct.unpack_from("<H", cd, p + 32)[0]
        lofs = struct.unpack_from("<I", cd, p + 42)[0]
        name = cd[p + 46:p + 46 + fnl].decode("utf-8", "replace")
        is_main = (name.startswith("Payload/") and name.endswith(".app/Info.plist")
                   and name.count("/") == 2 and "Watch" not in name)
        if is_main:
            lh = fetch_ranged(url, lofs, lofs + 29)
            lf, le = struct.unpack_from("<HH", lh, 26)
            d0 = lofs + 30 + lf + le
            comp = fetch_ranged(url, d0, d0 + csize - 1)
            raw = zlib.decompress(comp, -15) if method == 8 else comp
            pl = plistlib.loads(raw)
            info = {
                "bundleIdentifier": pl.get("CFBundleIdentifier"),
                "version": pl.get("CFBundleShortVersionString"),
                "buildVersion": pl.get("CFBundleVersion"),
                "displayName": pl.get("CFBundleDisplayName") or pl.get("CFBundleName"),
                "minOSVersion": pl.get("MinimumOSVersion"),
                "size": total,
            }
            break
        p += 46 + fnl + exl + cml
    if not info:
        raise RuntimeError("IPA 内未找到主 App 的 Info.plist")
    return info


def clean_notes(body, limit=700):
    """把 Release 正文压成适合在源里显示的纯文本。"""
    import re
    if not body:
        return ""
    t = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)           # 图片
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)        # 链接保留文字
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)   # 标题
    t = re.sub(r"\*\*|__|`", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t[:limit].rstrip() + ("…" if len(t) > limit else "")


def icon_url_ok(url, tries=2):
    """图标可达性探测（结果正向缓存，避免复跑重复联网）。"""
    cache = _load("icons.json", {})
    if cache.get(url):
        return True
    for i in range(tries):
        try:
            fetch(url, 0, 0)
            cache[url] = True
            _save("icons.json", cache)
            return True
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                try:
                    fetch(url)
                    cache[url] = True
                    _save("icons.json", cache)
                    return True
                except Exception:  # noqa: BLE001
                    return False
    return False


# ---------- 缓存 ----------
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache")


def _load(name, default):
    p = os.path.join(CACHE_DIR, name)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return default
    return default


def _save(name, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_cached(r):
    return {
        "tag_name": r["tag"],
        "prerelease": r["pre"],
        "draft": r["draft"],
        "published_at": r["date"] + "T00:00:00Z",
        "body": r.get("body", ""),
        "assets": [{"name": i["name"], "size": i["size"],
                    "browser_download_url": i["url"]} for i in r["ipas"]],
    }


def get_releases(repo, refresh=False):
    cache = _load("releases.json", {})
    if not refresh and repo in cache and cache[repo]:
        return [normalize_cached(x) for x in cache[repo]]
    rels = gh_json("https://api.github.com/repos/%s/releases?per_page=20" % repo)
    cache[repo] = [{
        "tag": x["tag_name"], "name": x.get("name"), "pre": x.get("prerelease"),
        "draft": x.get("draft"), "date": (x.get("published_at") or "")[:10],
        "body": (x.get("body") or "")[:2000],
        "ipas": [{"name": a["name"], "size": a["size"],
                  "url": a["browser_download_url"]} for a in x.get("assets", [])
                 if a["name"].lower().endswith(".ipa")],
    } for x in rels]
    _save("releases.json", cache)
    return rels


def probe_cached(url, force=False):
    """探测远端 IPA 元数据。

    探测结果按 URL 永久缓存：同一个 Release 资产的内容不会变，
    重复探测纯属浪费网络。CI 里这一点很关键（大陆直连 GitHub 不稳）。
    需要重探时用 --reprobe。
    """
    cache = _load("probes.json", {})
    if not force and url in cache and cache[url].get("bundleIdentifier"):
        return cache[url]
    info = probe_ipa(url)
    cache[url] = info
    _save("probes.json", cache)
    return info


def repo_of(app):
    """从版本记录里的 GitHub 链接反推仓库（用于失败时找回上一版数据）。"""
    for v in (app.get("versions") or []) + \
             [r for c in (app.get("releaseChannels") or []) for r in c.get("releases", [])]:
        src = v.get("source") or ""
        if src.startswith("https://github.com/"):
            parts = src[len("https://github.com/"):].split("/")
            if len(parts) >= 2:
                return "%s/%s" % (parts[0], parts[1])
    return None


def load_previous(path):
    """读入上一次生成的 apps.json，按仓库名索引，供网络失败时兜底。"""
    try:
        with open(path, encoding="utf-8") as f:
            prev = json.load(f)
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for a in prev.get("apps", []):
        r = repo_of(a)
        if r:
            out[r] = a
    return out


# ---------- 组装 ----------
def notes_for(r):
    """发布说明；预发布会在开头补一行 GitHub 上的预发布标签。

    为什么只能写在说明里：SideStore 安装时会拿 `version` / `buildVersion` 跟
    **下载下来的 IPA 里的真实值逐字比对**（`VerifyAppOperation` 第 5 步
    `verifyDownloadedVersion`：buildVersion 和 version 任一不等就抛
    mismatchedBuildVersion / mismatchedVersion，直接中止安装）。
    而 Animeko 这类项目的预发布 IPA 里 `CFBundleShortVersionString` 只写基础版本
    （`6.2.0`），预发布序号藏在 `CFBundleVersion` 里（`6.2.0-alpha01` → `60201`）。
    所以 `version` 字段**必须**填探测到的 `6.2.0`，不能填 tag 上的 `6.2.0-alpha01`。
    想让人一眼看出是哪个预发布，就只剩「说明文字」这个位置了。
    """
    notes = clean_notes(r.get("body"))
    if not notes:
        # 有些上游发布时正文是空的（实测 venera-prime v2.4.0 的 body 就是 null），
        # 客户端里「版本说明」会渲染成一片空白，看着像我们生成的源有问题。
        # 补一句兜底，明确这是上游没写，而不是源坏了。
        notes = "上游未填写本版更新说明，可到项目发布页查看。"
    if not r.get("prerelease"):
        return notes
    tag = (r.get("tag_name") or "").strip().lstrip("vV")
    if not tag:
        return notes
    head = "🧪 预发布 %s（%s）" % (tag, (r.get("published_at") or "")[:10])
    return head + ("\n\n" + notes if notes else "")


def make_versions(picks, repo, bundle_id=None, reprobe=False):
    """把 (release, asset) 列表探测成版本对象；bundleId 与首个不一致的会被丢弃。"""
    out = []
    for r, a in picks:
        try:
            m = probe_cached(a["browser_download_url"], reprobe)
        except Exception as e:  # noqa: BLE001
            print("   ! %-22s %-10s 探测失败：%r" % (repo, r["tag_name"], e), file=sys.stderr)
            continue
        if bundle_id is None:
            bundle_id = m["bundleIdentifier"]
        elif m["bundleIdentifier"] != bundle_id:
            print("   ! %s 的 %s bundleId 不一致，已丢弃" % (repo, r["tag_name"]), file=sys.stderr)
            continue
        out.append({
            "version": m["version"],
            "date": r["published_at"][:10],
            # buildVersion 是 AltStore 规范里的键名；
            # buildNumber 是 LiveContainer 实际解码的键名（CodingKeys 里写死了 buildNumber）。
            # 两个都写，谁也别说谁错 —— 多出来的键两边都会忽略。
            "buildVersion": m["buildVersion"],
            "buildNumber": m["buildVersion"],
            "localizedDescription": notes_for(r),
            "downloadURL": a["browser_download_url"],
            "size": a["size"],
            "minOSVersion": m["minOSVersion"],
            "releaseTag": r["tag_name"],
            "source": "https://github.com/%s/releases/tag/%s" % (repo, r["tag_name"]),
        })
    out.sort(key=lambda v: v["date"], reverse=True)
    return out, bundle_id


def sort_versions(vs):
    """按日期倒序；同日期时按版本号倒序，保证结果稳定可复现。"""
    return sorted(vs, key=lambda v: (str(v.get("date") or ""), semver_key(v.get("version"))),
                  reverse=True)


def semver_key(text):
    """把 3.0.0 / v2.3.2 / 6.1.0-beta01 转成可比元组（只取前三段数字）。"""
    nums = re.findall(r"\d+", str(text or ""))
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - min(3, len(nums)))


def collect(rels, cfg, per_app):
    """从发布列表里挑出：最近 per_app 个稳定版 + 最新的那个预发布版（若配置了 nightly）。"""
    stable, beta = [], None
    want_beta = bool(cfg.get("nightly"))
    for r in rels:
        if r.get("draft"):
            continue
        a = next((x for x in r.get("assets", []) if cfg["asset"](x["name"])), None)
        if not a:
            continue
        if r.get("prerelease"):
            if want_beta and beta is None:
                beta = (r, a)
        elif len(stable) < per_app:
            stable.append((r, a))
        if len(stable) >= per_app and (beta or not want_beta):
            break
    return stable, beta


def build(per_app=1, refresh=False, reprobe=False, prev_path=None):
    apps, carried = [], []
    prev = load_previous(prev_path) if prev_path else {}
    for cfg in APPS:
        repo = cfg["repo"]
        try:
            rels = get_releases(repo, refresh)
        except Exception as e:  # noqa: BLE001
            # 抓不到 Release（限流/断网）时绝不丢应用：沿用上一次生成的条目
            if repo in prev:
                apps.append(prev[repo])
                carried.append(cfg["name"])
                print("  ↺ %-9s 抓取失败（%s），沿用上一次的数据" % (cfg["name"], type(e).__name__))
            else:
                print("  ✗ %-9s 抓取失败且无历史数据，跳过：%r" % (cfg["name"], e), file=sys.stderr)
            continue

        stable_pick, beta_pick = collect(rels, cfg, per_app)
        if not stable_pick:
            if repo in prev:
                apps.append(prev[repo])
                carried.append(cfg["name"])
                print("  ↺ %-9s 没有可用 IPA，沿用上一次的数据" % cfg["name"])
            else:
                print("!! %s 没有可用的 IPA 资产，已跳过" % repo, file=sys.stderr)
            continue

        stable_versions, bundle_id = make_versions(stable_pick, repo, reprobe=reprobe)
        if not stable_versions:
            if repo in prev:
                apps.append(prev[repo])
                carried.append(cfg["name"])
                print("  ↺ %-9s 探测全部失败，沿用上一次的数据" % cfg["name"])
            continue
        latest = stable_versions[0]

        channels = [{"track": "stable", "releases": stable_versions}]
        beta_versions = []
        if beta_pick:
            beta_versions, nbid = make_versions([beta_pick], repo, bundle_id, reprobe)
            if beta_versions:
                channels.append({"track": "nightly", "releases": beta_versions})
            elif nbid and nbid != bundle_id:
                print("   ! %s 的测试版 bundleId 与稳定版不一致，已丢弃" % repo, file=sys.stderr)

        # 扁平 versions：所有轨道合并、按日期倒序、按 (版本号, build) 去重。
        # 给不认 releaseChannels 的客户端用 —— 尤其是 LiveContainer，
        # 它只读这个数组、只取 [0] 安装，没有开关也没有版本选择器。
        # 对 SideStore 无副作用：它有 releaseChannels 时压根不读这个数组（源码已核实）。
        flat_versions, seen_keys = [], set()
        for v in sort_versions(list(stable_versions) + list(beta_versions)):
            key = (v["version"], v.get("buildVersion"))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            flat_versions.append(v)
        is_beta_head = bool(beta_versions) and flat_versions and \
            flat_versions[0]["version"] == beta_versions[0]["version"]

        icon = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, latest["releaseTag"], cfg["icon"])
        if not icon_url_ok(icon):
            icon = "https://github.com/%s.png?size=460" % repo.split("/")[0]
            print("   ~ %s 图标回退为仓库头像" % repo, file=sys.stderr)

        app = {
            "name": cfg["name"],
            "bundleIdentifier": bundle_id,
            "developerName": cfg["developerName"],
            "subtitle": cfg["subtitle"],
            "localizedDescription": cfg["description"],
            "iconURL": icon,
            "tintColor": cfg["tintColor"],
            "category": cfg["category"],
            "appPermissions": {"entitlements": [], "privacy": {}},
            # v2 源格式：稳定 / 测试双轨道（SideStore 读这里）
            "releaseChannels": channels,
            # LiveContainer 等只读扁平列表的客户端走这里；
            # 含测试版，因为 LiveContainer 没有开关可以打开它们
            "versions": flat_versions,
            "version": latest["version"],
            "versionDate": latest["date"],
            "versionDescription": latest["localizedDescription"],
            "downloadURL": latest["downloadURL"],
            "size": latest["size"],
            "minOSVersion": latest["minOSVersion"],
        }
        if is_beta_head:
            # 纯展示用的角标（LiveContainer 会渲染成橙色 BETA）。
            # SideStore 只在「既无 releaseChannels 又无扁平 versions」的兜底分支读这个键，
            # 我们两条都有，所以对它没有任何影响。
            app["beta"] = True

        apps.append(app)
        btag = ("；nightly %s" % beta_versions[0]["version"]) if beta_versions else "；无测试版"
        print("  ✓ %-10s %-24s stable %-8s minOS %-5s%s"
              % (cfg["name"], bundle_id, latest["version"], latest["minOSVersion"], btag))
        print("      扁平 versions（LiveContainer 只认这个，取第 1 条）：%s%s"
              % ([v["version"] for v in flat_versions],
                 "  ← 首条是测试版，会打 BETA 角标" if is_beta_head else ""))

    src = dict(SOURCE)
    src["apps"] = apps
    if not apps:
        # 一个都没生成（首次运行且全网失败）：交给入口判失败，别写出半成品
        src["featuredApps"] = []
        src["news"] = []
        return src, carried

    src["iconURL"] = SOURCE["iconURL"]
    src["featuredApps"] = [a["bundleIdentifier"] for a in apps[:2]]
    src["news"] = [{
        "title": "源已建立",
        "identifier": "source-created",
        "caption": "收录 %d 款应用，IPA 直连各项目 GitHub Release。" % len(apps),
        "date": max(a["versionDate"] for a in apps),
        "tintColor": SOURCE["tintColor"],
        "notify": False,
    }]
    return src, carried


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--out", default=os.path.join(here, "..", "apps.json"))
    ap.add_argument("--versions", type=int, default=1, help="稳定版轨道保留几个版本（默认 1）")
    ap.add_argument("--refresh", action="store_true",
                    help="忽略 cache/ 里的 Release 列表，重新调 GitHub API 抓取")
    ap.add_argument("--reprobe", action="store_true",
                    help="连 IPA 元数据也重新探测（默认永久复用 cache/probes.json）")
    ap.add_argument("--no-probe-icons", action="store_true", help="跳过图标可达性检查")
    args = ap.parse_args()

    if args.no_probe_icons:
        globals()["icon_url_ok"] = lambda url, tries=2: True

    out = os.path.abspath(args.out)
    source, carried = build(args.versions, args.refresh, args.reprobe, prev_path=out)

    # 原子写入：避免异常中断留下半截 apps.json 被提交
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(source, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, out)

    n_stable = sum(len(c["releases"]) for a in source["apps"] for c in a["releaseChannels"]
                   if c["track"] == "stable")
    n_beta = sum(len(c["releases"]) for a in source["apps"] for c in a["releaseChannels"]
                 if c["track"] == "nightly")
    print("\n已生成 %s（%d 个 app；稳定 %d 条 / 测试 %d 条；%.1f KB）"
          % (out, len(source["apps"]), n_stable, n_beta, os.path.getsize(out) / 1024.0))
    if carried:
        print("沿用上一次数据的应用：%s" % "、".join(carried))
    if not source["apps"]:
        print("!! 一个应用都没生成，判定为失败", file=sys.stderr)
        sys.exit(1)
