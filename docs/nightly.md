# 哪些预发布会被收录

判断标准只有一条：**这个预发布有没有独立的 iOS 安装包、版本是否不低于当前稳定版**。
不是「tag 里带不带 alpha / beta / rc」。

同时满足下面几条才会进 `nightly` 轨道：

1. 上游把它标记为 `prerelease`（或 tag 名明确是预发布）；
2. 该发布里确实有匹配的 iOS IPA；
3. 包内 Bundle ID 与稳定版一致（不一致的会被丢弃，避免装出两个应用）；
4. 版本号不低于稳定版 —— SideStore 的 `betaSemVer >= stableSemVer` 会直接过滤掉更旧的预发布。

## 当前复核结果

<!-- nightly:begin -->
| 应用 | 稳定版 | 最新预发布 | 结论 |
|---|---|---|---|
| Aidoku | 0.9 | 无 | 无预发布 |
| AirCard | 1.3.2 | 无 | 无预发布 |
| AniBaka | 5.2.5 | 无 | 无预发布 |
| AniCh | 1.5.27 | 无 | 无预发布 |
| AnimeFlow | 2.7.0 | 无 | 无预发布 |
| Animeko | 6.4.1 | v6.4.0-beta02 (2026-10-22) | 收录（nightly 轨道） |
| ARMSX2 Nightly | 2.6.0-nightly.20261124.1937 | nightly-20261124 (2026-11-25) | 以预览版作为稳定版 |
| ARMSX3 | 0.0.4 | ios-0.0.3 (2026-11-17) | 以预览版作为稳定版 |
| AvPlay | 2.2.2 | 无 | 无预发布 |
| Breeze | 3.1.0 | custom-issue-246 (2026-11-21) | 不收：该预发布没有 iOS 包 |
| Camlo | 1.3.4 | 无 | 无预发布 |
| EhPanda | 2.8.1 | 无 | 无预发布 |
| GestaltEdit | 2.3.1 | 无 | 无预发布 |
| GestaltX | 1.1.1 | 无 | 无预发布 |
| HentaiPark | 0.15.4 | 无 | 无预发布 |
| HGhubX | 2.2.10 | test-pre (2026-11-21) | 不收：比稳定版旧 |
| INSAV | 1.3.1 | 无 | 无预发布 |
| Kazumi | 2.4.6 | 无 | 无预发布 |
| Nekularity | 0.4.9 | 无 | 无预发布 |
| One | 1.7.1 | 无 | 无预发布 |
| PicaComic | 5.1.3 | 无 | 无预发布 |
| PicaX | 1.2.5 | 无 | 无预发布 |
| Placard | 2.0.3 | 无 | 无预发布 |
| Swipt | 0.1.0 | nightly (2026-11-25) | 以预览版作为稳定版 |
| Venera Prime | 2.8.1 | 无 | 无预发布 |
| Venera-SSR | 2.1.5 | 无 | 无预发布 |
| VeneraNext | 1.18.5 | v1.18.4-rc.3 (2026-11-16) | 不收：比稳定版旧 |
| VeneraX | 3.0.2 | mobile-3.0.2-beta.3 (2026-11-22) | 不收：该预发布没有 iOS 包 |
| 大富翁4重制版 | 1.3.0 | 无 | 无预发布 |
| 真果鉴 | 2.0.3 | windows-native-deps (2026-11-04) | 不收：该预发布没有 iOS 包 |
<!-- nightly:end -->

> 这张表由 `tools/render_docs.py` 按 `apps.json` 与 `cache/releases.json` 生成，每轮自动化后刷新：
> 「稳定版」取源里当前发布的版本，「最新预发布」取上游标记为 prerelease 的最新一条，
> 「结论」说明它为什么被收录或不收。不要手工编辑。

## 判断示例

> **Animeko 早先为什么不收**：`v6.1.0-beta01` 的更新日志与正式版 6.1.0 **逐字相同**，等于没有独立内容；
> `v6.2.0-alpha01` 是新东西，所以收了。判断标准是「有没有独立的新内容」，不是「tag 里带不带 alpha」。
>
> 另外，Animeko 包内真实 Bundle ID 就是 `org.animeko.animeko`，**没有**独立的 beta ID ——
> `org.animeko.animeko.beta` 是别的源编出来的，本仓库不编造 ID。

另外两类容易误判的情况：

- **上游只发预览版**（ARMSX2 Nightly、ARMSX3、Swipt 这类）：没有稳定版可选，源里直接把预览版当稳定版，结论列会写「以预览版作为稳定版」。
- **预发布里没有 iOS 包**（例如某些仓库的 Windows / HarmonyOS 预览）：没有可安装的 IPA，不能收，结论列会写「该预发布没有 iOS 包」。
