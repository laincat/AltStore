#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 GitHub Release 的附件镜像到 cnb.cool 的 Release，供国内直连下载。

为什么需要它
------------
CNB 仓库此前只被 ``git push --force`` 同步分支历史，**从不创建 Release** ——
所以 https://cnb.cool/laincat/*/-/releases 一直是空的。而 CNB 侧原本自带的
``.cnb.yml`` 发布流水线又会被同一次 force-push 覆盖掉，等于发布能力被同步
流程自己抹掉。这里改成由 GitHub 单向驱动：GitHub 是唯一构建源，CNB 只作为
发布出口，两边不会再互相覆盖。

CNB 没有 GitHub 的 ``releases/latest`` 魔法别名（实测会返回
``release for tag latest not found``），所以**固定一个 tag**，每次覆盖同名
附件，地址就永远稳定：

    https://cnb.cool/<slug>/-/releases/download/<tag>/<文件名>

上传是三步，少一步文件就不出现在列表里
-------------------------------------
    ① POST /{repo}/-/releases/{id}/asset-upload-url  → {upload_url, verify_url}
    ② PUT 文件字节到 upload_url（预签名地址，可能 307，要自己跟重定向）
    ③ POST verify_url 确认，服务端才登记这个附件

用法
----
    python tools/publish_cnb_release.py --files a.list b.mrs
    python tools/publish_cnb_release.py --files-dir dist --tag latest
    python tools/publish_cnb_release.py --files-dir dist --dry-run

退出码：0 成功；1 失败（缺 token / 接口报错 / 上传后校验不一致）。
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Windows 下 Python 默认 stdout 是 cp1252，print 中文会 UnicodeEncodeError。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

DEFAULT_ENDPOINT = "https://api.cnb.cool"
DEFAULT_TAG = "latest"
UA = "laincat-cnb-release-publisher/1.0"
PUBLIC_BASE = "https://cnb.cool"


def log(msg: str) -> None:
    print("[cnb-release] %s" % msg, flush=True)


# --------------------------------------------------------------------------- HTTP

def _api(method: str, url: str, token: str, payload: dict | None = None,
         timeout: int = 60) -> tuple[int, dict]:
    """调 CNB OpenAPI。4xx/5xx 不抛异常，交给调用方判断。"""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer %s" % token)
    req.add_header("Accept", "application/vnd.cnb.api+json")
    req.add_header("User-Agent", UA)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, (json.loads(raw) if raw else {})
        except ValueError:
            return e.code, {"errmsg": raw[:200].decode("utf-8", "replace")}


def _put_file(url: str, path: str, timeout: int = 600, max_redirect: int = 5) -> tuple[int, bytes]:
    """把文件 PUT 到预签名地址。

    不用 urllib 是因为它对 PUT 的 30x 处理只允许 GET/HEAD（会把重定向变成
    异常），而预签名地址在多域名 CDN 后面很可能会 307。这里自己跟，保持方法。
    """
    size = os.path.getsize(path)
    cur = url
    for _ in range(max_redirect):
        parts = urllib.parse.urlsplit(cur)
        conn_cls = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
        conn = conn_cls(parts.hostname, parts.port, timeout=timeout)
        target = parts.path + (("?" + parts.query) if parts.query else "")
        try:
            with open(path, "rb") as fh:
                conn.request("PUT", target, body=fh, headers={
                    "Content-Length": str(size),
                    "Content-Type": "application/octet-stream",
                    "User-Agent": UA,
                })
                resp = conn.getresponse()
                body = resp.read()
                status = resp.status
                location = resp.getheader("Location")
        finally:
            conn.close()
        if status in (301, 302, 303, 307, 308):
            if not location:
                raise RuntimeError("上传地址返回 %d 但没有 Location" % status)
            cur = urllib.parse.urljoin(cur, location)
            continue
        return status, body
    raise RuntimeError("上传重定向超过 %d 次" % max_redirect)


# --------------------------------------------------------------------------- Release

def get_release_by_tag(endpoint: str, slug: str, tag: str, token: str) -> dict | None:
    status, body = _api("GET", "%s/%s/-/releases/tags/%s"
                        % (endpoint, slug, urllib.parse.quote(tag)), token)
    if status == 200:
        return body.get("data", body)
    if status == 404:
        return None
    raise RuntimeError("查询版本失败：HTTP %d %s" % (status, json.dumps(body, ensure_ascii=False)[:300]))


def create_release(endpoint: str, slug: str, tag: str, target: str, title: str,
                   body_text: str, token: str) -> dict:
    # 「如果指定的标签不存在，将基于 target_commitish 自动创建标签」—— 不必预先打 tag
    status, body = _api("POST", "%s/%s/-/releases" % (endpoint, slug), token, {
        "tag_name": tag,
        "name": title,
        "body": body_text,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
        "target_commitish": target,
    })
    if status not in (200, 201):
        raise RuntimeError("创建版本失败：HTTP %d %s"
                           % (status, json.dumps(body, ensure_ascii=False)[:400]))
    return body.get("data", body)


def release_assets(endpoint: str, slug: str, tag: str, token: str) -> dict[str, dict]:
    """返回 {附件名: 附件对象}，用于按 sha256 决定要不要重传。"""
    release = get_release_by_tag(endpoint, slug, tag, token)
    if not release:
        return {}
    return {a.get("name"): a for a in (release.get("assets") or [])}


def upload_asset(endpoint: str, slug: str, release_id: str, name: str, path: str,
                 token: str, ttl: int) -> None:
    size = os.path.getsize(path)
    status, body = _api("POST", "%s/%s/-/releases/%s/asset-upload-url"
                        % (endpoint, slug, release_id), token, {
        "asset_name": name,
        "overwrite": True,      # 每次都换同一批名字，靠 overwrite 原地更新
        "size": size,
        "ttl": ttl,
    })
    if status not in (200, 201):
        raise RuntimeError("取上传地址失败（%s）：HTTP %d %s"
                           % (name, status, json.dumps(body, ensure_ascii=False)[:400]))
    info = body.get("data", body)
    upload_url = info.get("upload_url")
    verify_url = info.get("verify_url")
    if not upload_url or not verify_url:
        raise RuntimeError("上传地址响应缺字段：%s" % json.dumps(info, ensure_ascii=False)[:300])

    st, raw = _put_file(upload_url, path)
    if st not in (200, 201, 204):
        raise RuntimeError("上传字节失败（%s）：HTTP %d %s" % (name, st, raw[:200]))
    log("  ↑ 已传 %s（%d 字节）" % (name, size))

    # 第 ③ 步不能省：不确认的话文件在对象存储里，但 Release 附件列表里看不到
    st2, body2 = _api("POST", verify_url, token, None)
    if st2 not in (200, 201, 204):
        raise RuntimeError("确认上传失败（%s）：HTTP %d %s"
                           % (name, st2, json.dumps(body2, ensure_ascii=False)[:300]))


# --------------------------------------------------------------------------- 自检

def verify_published(base: str, files: list[tuple[str, str]]) -> list[str]:
    """逐个下载线上文件，与本地 sha256 比对。最便宜的落地证据。"""
    problems = []
    for name, path in files:
        url = "%s/%s" % (base.rstrip("/"), urllib.parse.quote(name))
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                live = hashlib.sha256(r.read()).hexdigest()
        except Exception as exc:                               # noqa: BLE001
            problems.append("线上读不到 %s：%s: %s" % (name, type(exc).__name__, exc))
            continue
        with open(path, "rb") as fh:
            local = hashlib.sha256(fh.read()).hexdigest()
        if live != local:
            problems.append("%s 线上 %s ≠ 本地 %s" % (name, live[:16], local[:16]))
    return problems


# --------------------------------------------------------------------------- 入口

def collect_files(args) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for p in args.files or []:
        if not os.path.isfile(p):
            raise SystemExit("找不到文件：%s" % p)
        out.append((os.path.basename(p), p))
    if args.files_dir:
        for entry in sorted(os.listdir(args.files_dir)):
            path = os.path.join(args.files_dir, entry)
            if os.path.isfile(path):
                out.append((entry, path))
    names = [n for n, _ in out]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise SystemExit("附件名重复，扁平发布必须唯一：%s" % ", ".join(dupes))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="把文件发布为 cnb.cool Release 附件")
    ap.add_argument("--files", nargs="*", help="要发布的文件（附件名取文件名）")
    ap.add_argument("--files-dir", default=None, help="要发布的目录（取其中所有普通文件）")
    ap.add_argument("--tag", default=DEFAULT_TAG, help="版本标签（固定不变，地址才稳定）")
    ap.add_argument("--title", default=None, help="版本标题，默认取 tag")
    ap.add_argument("--body", default=None, help="版本描述；默认自动生成一份")
    ap.add_argument("--endpoint", default=os.environ.get("CNB_API_ENDPOINT", DEFAULT_ENDPOINT))
    ap.add_argument("--slug", default=os.environ.get("CNB_REPO_SLUG"),
                    help="仓库路径，如 laincat/Rules；默认取 CNB_REPO_SLUG")
    ap.add_argument("--token", default=os.environ.get("CNB_TOKEN"))
    ap.add_argument("--target", default=os.environ.get("CNB_BRANCH", "main"),
                    help="tag 不存在时基于哪个分支创建")
    ap.add_argument("--ttl", type=int, default=0,
                    help="附件保留天数；0 = 永久（最大 180）")
    ap.add_argument("--public-base", default=None,
                    help="公开下载基址，默认按 slug/tag 推导")
    ap.add_argument("--no-verify", action="store_true", help="跳过上传后的线上自检")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不调接口")
    args = ap.parse_args()

    if not args.slug:
        raise SystemExit("缺少 --slug（或环境变量 CNB_REPO_SLUG）")
    files = collect_files(args)
    if not files:
        raise SystemExit("没有可发布的文件")

    base = args.public_base or "%s/%s/-/releases/download/%s" % (PUBLIC_BASE, args.slug, args.tag)
    log("仓库=%s  标签=%s  ttl=%s  文件=%d" % (args.slug, args.tag, args.ttl, len(files)))
    for name, path in files:
        log("  %-34s %8d 字节  sha256=%s"
            % (name, os.path.getsize(path),
               hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]))

    if args.dry_run:
        log("dry-run：endpoint=%s  目标分支=%s" % (args.endpoint, args.target))
        log("  token %s" % ("已提供" if args.token else "缺失（真跑会失败）"))
        for name, _ in files:
            log("  将上传 %s → %s/%s" % (name, base, name))
        return 0

    if not args.token:
        log("缺少 CNB_TOKEN —— CI 里由平台注入；本地请建一个带 repo-release:rw 的令牌")
        return 1

    existing = release_assets(args.endpoint, args.slug, args.tag, args.token)
    release = get_release_by_tag(args.endpoint, args.slug, args.tag, args.token)
    if release:
        rid = str(release.get("id") or "")
        log("版本 %s 已存在（id=%s），按内容覆盖附件" % (args.tag, rid))
    else:
        log("版本 %s 不存在，创建中（基于 %s）…" % (args.tag, args.target))
        body = args.body or (
            "本 Release 的 tag 固定为 `%s`，附件在内容变化后被覆盖，"
            "所以下面的地址永远指向最新一版。\n\n固定下载地址：\n\n" % args.tag
        ) + "".join("- `%s/%s`\n" % (base, n) for n, _ in files)
        release = create_release(args.endpoint, args.slug, args.tag, args.target,
                                 args.title or args.tag, body, args.token)
        rid = str(release.get("id") or "")
        if not rid:
            raise RuntimeError("创建返回里没有 id：%s" % json.dumps(release, ensure_ascii=False)[:400])
        log("已创建，id=%s" % rid)

    changed: list[tuple[str, str]] = []
    for name, path in files:
        with open(path, "rb") as fh:
            want = hashlib.sha256(fh.read()).hexdigest()
        have = (existing.get(name) or {}).get("hash_value") or ""
        if have and have.lower() == want.lower():
            log("  = %s 内容未变，跳过" % name)
            continue
        upload_asset(args.endpoint, args.slug, rid, name, path, args.token, args.ttl)
        changed.append((name, path))

    if not changed:
        log("全部附件内容未变，无需更新")

    if not args.no_verify:
        problems = verify_published(base, files)
        if problems:
            for p in problems:
                log("  ✗ %s" % p)
            log("线上自检未通过")
            return 1
        log("线上自检通过：附件可下载且 sha256 与本地一致")

    log("发布完成。固定地址：")
    for name, _ in files:
        print("%s/%s" % (base, name))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:                                   # noqa: BLE001
        # CI 里让错误以「人话 + 非零退出码」收场，不要甩一坨 traceback
        log("失败：%s: %s" % (type(exc).__name__, exc))
        raise SystemExit(1)
