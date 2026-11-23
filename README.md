# Laincat 工具箱 — SideStore / AltStore / LiveContainer 源文件

自用的 iOS 侧载源（源名称 **Laincat 工具箱**，图标是 [@laincat](https://github.com/laincat) 的 GitHub 头像）：收录 30 个 iOS 应用，**自动跟随上游 GitHub Release 更新**。

三个客户端都能用：**SideStore / AltStore / LiveContainer**。

> ⚠️ SideStore、AltStore 与 LiveContainer 的解析逻辑**不一样**，同一个源在两边看到的东西可能不同。
> 典型例子是测试版：LiveContainer 直接装 `versions[0]`，SideStore 得先开 Beta 开关。
> 详见 [docs/clients.md](docs/clients.md)。

## 添加这个源

三个地址内容完全一致，**任选一个**。

国内访问更快，推荐用这个：

```
https://cnb.cool/laincat/AltStore/-/git/raw/main/apps.json
```

GitHub 直链，作为备用（大陆可能被墙或极慢）：

```
https://raw.githubusercontent.com/laincat/AltStore/main/apps.json
```

GitHub Releases 的固定地址（走 release CDN；在浏览器里打开会直接触发下载）：

```
https://github.com/laincat/AltStore/releases/download/latest/apps.json
```

怎么加：

- **SideStore / AltStore**：`Sources（源）` → 右上角 `+` → 粘贴上面的地址
- **LiveContainer**：底部标签栏 `源`（英文是 `Sources`）→ 右上角 `+`（`添加源`）→ 粘贴同一地址

> - cnb.cool 的原文直链必须是 `/-/git/raw/`，别用 `/-/raw/` —— 那个返回的是仓库网页的 HTML 外壳，不是文件内容。
> - 三个地址的 `Content-Type` 并不相同（前两个 `text/plain; charset=utf-8`，Releases 是 `application/octet-stream`），但客户端只看 HTTP 状态码和 JSON 内容，三个都能用。
> - Releases 那个地址背后**只有一个** release，tag 固定为 `latest`，内容在每次变化后被覆盖，地址永远不变。

## 应用清单

<!-- apps:begin -->
| 应用 | Bundle ID | 稳定版 | 最低系统 | 测试版 | 上游 |
|---|---|---|---|---|---|
| Aidoku | `app.aidoku.Aidoku` | 0.9 | iOS 15.0+ | 无 | [Aidoku/Aidoku](https://github.com/Aidoku/Aidoku) |
| AirCard | `com.mak5er.aircard` | 1.3.2 | iOS 18.0+ | 无 | [Mak5er/AirCard-iOS](https://github.com/Mak5er/AirCard-iOS) |
| AniBaka | `ani.baka` | 5.2.5 | iOS 13.0+ | 无 | [AniBakaBaka/AniBaka](https://github.com/AniBakaBaka/AniBaka) |
| AniCh | `app.anich` | 1.5.27 | iOS 12.0+ | 无 | [Sle2p/AniCh](https://github.com/Sle2p/AniCh) |
| AnimeFlow | `com.ligg.animeflow` | 2.7.0 | iOS 15.0+ | 无 | [openAnimeFlow/AnimeFlow](https://github.com/openAnimeFlow/AnimeFlow) |
| Animeko | `org.animeko.animeko` | 6.4.1 | iOS 16.0+ | 6.4.0 | [open-ani/animeko](https://github.com/open-ani/animeko) |
| ARMSX2 Nightly | `com.armsx2.ios.nightly` | 2.6.0-nightly.20261122.2300 | iOS 17.4+ | 无 | [ARMSX2/ARMSX2](https://github.com/ARMSX2/ARMSX2) |
| ARMSX3 | `com.armsx3.ARMSX3` | 0.0.4 | iOS 17.4+ | 无 | [ARMSX2/ARMSX3](https://github.com/ARMSX2/ARMSX3) |
| AvPlay | `com.javdb.avplay2` | 2.2.2 | iOS 15.3+ | 无 | [anonymousjav/AvPlayRelease](https://github.com/anonymousjav/AvPlayRelease) |
| Breeze | `com.zephyr.breeze` | 3.1.0 | iOS 15.0+ | 无 | [breeze-project-org/Breeze](https://github.com/breeze-project-org/Breeze) |
| Camlo | `com.kianuni.Camlo` | 1.3.4 | iOS 26.0+ | 无 | [Kianuni/Camlo](https://github.com/Kianuni/Camlo) |
| EhPanda | `app.ehpanda` | 2.8.1 | iOS 26.0+ | 无 | [EhPanda-Team/EhPanda](https://github.com/EhPanda-Team/EhPanda) |
| GestaltEdit | `me.ssus.gestaltedit` | 2.3.1 | iOS 26.0+ | 无 | [frs0n/GestaltEdit](https://github.com/frs0n/GestaltEdit) |
| GestaltX | `com.huami.gestultx` | 1.1.1 | iOS 26.0+ | 无 | [huamidev/GestaltX](https://github.com/huamidev/GestaltX) |
| HentaiPark | `com.hentaipark.hentaiPark` | 0.15.4 | iOS 15.0+ | 无 | [drdon1234/Hentai-Park](https://github.com/drdon1234/Hentai-Park) |
| HGhubX | `com.hghubx.app` | 2.2.8 | iOS 15.0+ | 无 | [zxsos/HGhubX](https://github.com/zxsos/HGhubX) |
| INSAV | `com.ios151.insav` | 1.3.1 | iOS 16.0+ | 无 | [ios151/Insav-releases](https://github.com/ios151/Insav-releases) |
| Kazumi | `com.example.kazumi` | 2.4.6 | iOS 15.0+ | 无 | [Predidit/Kazumi](https://github.com/Predidit/Kazumi) |
| Nekularity | `com.laincat.nekularity` | 0.4.9 | iOS 26.0+ | 无 | [laincat/Nekularity](https://github.com/laincat/Nekularity) |
| One | `com.ios151.one` | 1.7.1 | iOS 16.0+ | 无 | [ios151/One-releases](https://github.com/ios151/One-releases) |
| PicaComic | `com.github.pacalini.picaComic` | 5.1.3 | iOS 15.1+ | 无 | [ccbkv/PicaComic](https://github.com/ccbkv/PicaComic) |
| PicaX | `moye.PicaX` | 1.2.5 | iOS 15.2+ | 无 | [youshen2/PicaX](https://github.com/youshen2/PicaX) |
| Placard | `me.ssus.placard` | 2.0.3 | iOS 26.0+ | 无 | [frs0n/placard](https://github.com/frs0n/placard) |
| Swipt | `io.nekohasekai.swipt` | 0.1.0 | iOS 16.4+ | 无 | [swipt-automation/swipt](https://github.com/swipt-automation/swipt) |
| Venera Prime | `com.github.wgh136.venera.prime` | 2.8.1 | iOS 14.0+ | 无 | [venera-app/venera-prime](https://github.com/venera-app/venera-prime) |
| Venera-SSR | `com.github.kiastr.venera-ssr` | 2.1.5 | iOS 14.0+ | 无 | [Kiastr/Venera-SSR](https://github.com/Kiastr/Venera-SSR) |
| VeneraNext | `com.github.cyrilpeng.veneranext` | 1.18.4 | iOS 14.0+ | 无 | [CyrilPeng/Venera-Next](https://github.com/CyrilPeng/Venera-Next) |
| VeneraX | `io.github.kyosee.venera` | 3.0.1 | iOS 15.1+ | 无 | [Kyosee/VeneraX](https://github.com/Kyosee/VeneraX) |
| 大富翁4重制版 | `pro.areu.rich4` | 1.2.4 | iOS 15.0+ | 无 | [iam567/rich4-renew-app](https://github.com/iam567/rich4-renew-app) |
| 真果鉴 | `com.yingshib.xg` | 2.0.3 | iOS 15.1+ | 无 | [Xanerix/guoapp](https://github.com/Xanerix/guoapp) |
<!-- apps:end -->

> - 版本、最低系统与测试版标记都取自 IPA 包内元数据，不是抄上游 README。
> - 表格由 `tools/render_docs.py` 按 `apps.json` 生成，请勿手工编辑。
> - 自动化只在上游确实有新版本时更新，每轮变化记在 [docs/Changelog.md](docs/Changelog.md)。

## 文档

| 文档 | 内容 |
|---|---|
| [docs/clients.md](docs/clients.md) | 两个客户端的解析差异、测试版开关、为什么不用「拆条目」 |
| [docs/nightly.md](docs/nightly.md) | 哪些预发布会被收录，判断标准是什么 |
| [docs/automation.md](docs/automation.md) | 自动更新流程、为什么轮询、依赖更新、网络与缓存安全 |
| [docs/accuracy.md](docs/accuracy.md) | 数据准确性：Bundle ID、版本号、最低系统、图标 |
| [docs/development.md](docs/development.md) | 本地运行、目录结构、参数 |
| [docs/notes.md](docs/notes.md) | 使用注意事项 |
| [docs/Changelog.md](docs/Changelog.md) | 更新记录（自动维护） |

## 说明

本仓库**只做索引**：IPA 全部由各项目自己在 GitHub Release 发布，未重新打包、未修改任何二进制。开源应用请遵守各项目许可证；AvPlay 上游未提供应用源代码或开源许可证。
