# Laincat 工具箱 — SideStore / AltStore / LiveContainer 源文件

自用的 iOS 侧载源（源名称 **Laincat 工具箱**，图标是 [@laincat](https://github.com/laincat) 的 GitHub 头像）：收录 6 个开源 iOS 应用（番剧 + 漫画），**自动跟随上游 GitHub Release 更新**。

三个客户端都能用：**SideStore / AltStore / LiveContainer**。

> ⚠️ SideStore、AltStore 与 LiveContainer 的解析逻辑**不一样**，同一个源在两边看到的东西可能不同。
> 典型例子就是 EhPanda 的测试版 3.0.0 —— 详见《两个客户端的差异》。

## 添加这个源

两个地址内容完全一致，**任选一个**。

国内访问更快，推荐用这个：

```
https://cnb.cool/laincat/AltStore/-/git/raw/main/apps.json
```

GitHub 直链，作为备用（大陆可能被墙或极慢）：

```
https://raw.githubusercontent.com/laincat/AltStore/main/apps.json
```

怎么加：

- **SideStore / AltStore**：`Sources（源）` → 右上角 `+` → 粘贴上面的地址
- **LiveContainer**：底部标签栏 `源`（英文是 `Sources`）→ 右上角 `+`（`添加源`）→ 粘贴同一地址

> - cnb.cool 的原文直链必须是 `/-/git/raw/`，别用 `/-/raw/`——那个返回的是仓库网页的 HTML 外壳，不是文件内容。
> - 两个地址都返回 `text/plain`，客户端只按内容解析 JSON，不受影响。
> - `raw.githubusercontent.com` 在大陆经常被墙或极慢，用不了就换 cnb.cool 那个。

## 应用清单

| 应用 | Bundle ID | 稳定版 | 体积 | 最低系统 | 测试版 | 上游 |
|---|---|---|---|---|---|---|
| Kazumi | `com.example.kazumi` | 2.3.3 | 28.4 MB | iOS 15.0+ | 无 | [Predidit/Kazumi](https://github.com/Predidit/Kazumi) |
| Animeko | `org.animeko.animeko` | 6.1.0 | 42.4 MB | iOS 14.0+ | 无 | [open-ani/animeko](https://github.com/open-ani/animeko) |
| EhPanda | `app.ehpanda` | 2.8.1 | 7.0 MB | **iOS 26.0+** | **3.0.0**（9.7 MB） | [EhPanda-Team/EhPanda](https://github.com/EhPanda-Team/EhPanda) |
| VeneraX | `io.github.kyosee.venera` | 2.3.2 | 33.8 MB | iOS 16.0+ | 无 | [Kyosee/VeneraX](https://github.com/Kyosee/VeneraX) |
| Breeze | `com.zephyr.breeze` | 3.0.31 | 24.6 MB | iOS 15.0+ | 无 | [deretame/Breeze](https://github.com/deretame/Breeze) |
| PicaX | `moye.PicaX` | 1.2.3 | 10.7 MB | iOS 15.2+ | 无 | [youshen2/PicaX](https://github.com/youshen2/PicaX) |

每个应用提供 **stable（稳定）** 轨道；只有 EhPanda 有可用的测试版，额外提供 **nightly（测试）** 轨道，内含 3.0.0。

## 两个客户端的差异（重要）

同一个 `apps.json`，两家客户端读的字段**完全不同**：

| | SideStore / AltStore | LiveContainer |
|---|---|---|
| 读哪个字段 | `releaseChannels` 里的轨道 | 只读扁平的 `versions` 数组 |
| 认不认 `releaseChannels` | 认 | **完全不认**（代码里没有这个字段） |
| 测试版开关 | 有，`设置 → Beta Testing`，**默认关闭** | **没有开关** |
| 版本选择器 | 有（能挑历史版本） | **没有**，界面上只显示并安装 `versions[0]` |
| 显示哪个版本 | stable 轨道；开关打开后 beta 轨道**取代** stable | 永远是 `versions[0]` |

所以本仓库**两处都写**：

```jsonc
{
  "releaseChannels": [                  // ← SideStore / AltStore 走这里
    { "track": "stable",  "releases": [ /* 2.8.1 */ ] },
    { "track": "nightly", "releases": [ /* 3.0.0 */ ] }
  ],
  "versions": [ /* 3.0.0, 2.8.1 */ ],   // ← LiveContainer 走这里，只取第 1 条
  "beta": true                          // ← LiveContainer 会显示「测试版」角标
}
```

**往扁平 `versions` 里塞测试版，对 SideStore 没有任何副作用。** 它的解码逻辑是：

```swift
var versions = getReleases(default: stableTrack) ?? []
if versions.isEmpty {          // ← 只有轨道取不到东西时，才会回头看扁平 versions
    versions = try container.decodeIfPresent([AppVersion].self, forKey: .versions) ?? ...
}
```

stable 轨道非空，这个 `if` 永远不成立（整个 `StoreApp.swift` 里搜 `forKey: .versions` 只有这一处）。

## EhPanda 的测试版 3.0.0

| 客户端 | 怎么才能拿到 3.0.0 |
|---|---|
| **LiveContainer** | **什么都不用做**。源里 `versions[0]` 就是 3.0.0，列表里直接显示、点安装就是它，旁边带「测试版」角标 |
| **SideStore / AltStore** | 要手动开开关：`设置 → Beta Testing → 打开 Beta Updates`（轨道选 `nightly`，默认就是它，不用改） |

SideStore 那三层门槛（源码 `AltStore/Core/Model/StoreApp.swift`）：

1. `isBetaUpdatesEnabled` —— 设置里的 `Beta Updates` 开关，**默认 false**
2. `betaUdpatesTrack` —— 轨道名，默认 `nightly`（下拉框只提供 `alpha` 和 `nightly`）
3. `betaSemVer >= stableSemVer` —— 3.0.0 > 2.8.1 ✓

```swift
private var betaReleases: [AppVersion]? {
    if UserDefaults.standard.isBetaUpdatesEnabled,               // ← 必须手动打开
       let betaTrack = UserDefaults.standard.betaUdpatesTrack {  // ← 默认 "nightly"
        ...
        betaSemVer >= stableSemVer
    }
    return nil
}
// 展示的版本列表：betaReleases ?? stableTrack.releases
// 注意是「取代」不是「合并」：开关打开后看到的就是 beta 轨道的内容
```

### 本地就能验证，不用装到手机上

```bash
python tools/simulate_client.py                        # 两个客户端都算
python tools/simulate_client.py --client livecontainer
python tools/simulate_client.py --client sidestore
```

这个脚本把两家客户端的解析逻辑都照抄成了 Python，直接告诉你「谁会看到、会安装哪个版本」：

```
EhPanda   (app.ehpanda)
   SideStore · 关 Beta → ['2.8.1']
   SideStore · 开 Beta → ['3.0.0']
      ⚠️ ['3.0.0'] 只有开了 Beta 开关才可见
   LiveContainer       → 会安装 3.0.0 (158)  [BETA 角标]   [来源：扁平 versions[0]]
                          最低系统 26.0
```

它还会报告「两个客户端结论分歧」的条目 —— 万一以后扁平 `versions` 忘了放测试版，这里会立刻报出来。

### ⚠️ 为什么不用「拆成两个 app 条目」的做法

有些源（例如 `maxchang3/ani-altstore-source`）把测试版拆成**独立的 app 条目**（`Animeko` + `Animeko (Pre-Release)`）。它的 `versions` 是**不带 `releaseChannels` 的扁平列表**，所以预发布在两边都会一直显示、不需要任何开关。

看起来省事，但代价是拆出来的条目**必须编造一个 Bundle ID**（参考源写的是 `org.animeko.animeko.beta`），而 Animeko 测试包内的真实 ID 是 `org.animeko.animeko`：

| 约束 / 校验 | 出处 | 后果 |
|---|---|---|
| `StoreApp` 唯一约束 `(sourceIdentifier, bundleIdentifier)` | CoreData 模型 | 同一源内两个条目**不能共用 Bundle ID**，否则会被合并成一个 |
| 于是测试版条目只能**编造 ID** | 参考源写的是 `org.animeko.animeko.beta` | 与包内真实 ID 不符 |
| `verifyApp` 要求源声明 ID **必须等于** IPA 内真实 ID | `VerifyAppOperation.swift` | 安装时抛 `mismatchedBundleIdentifiers` |
| 该步骤是**安装流水线第 2 步** | `OperationStepDefinition.install` | 默认就在流程里 |
| 校验开关 `isBundleIDVerificationEnabled` 默认 **true** | `UserDefaults+AltStore.swift` | 且**设置界面里没有这个开关**（`DeveloperOptionsView` / `ExperimentalFeaturesView` 里都搜不到） |

**结论**：拆条目的做法在 SideStore 上是「看得见、装不上」。本仓库不这么做——保留规范的 `releaseChannels` 轨道，**同时**用扁平 `versions` 照顾 LiveContainer，两边都看得见、也都装得上。

## 自动更新

`.github/workflows/update-source.yml` **每 15 分钟**检查一次上游（在每小时的 7、22、37、52 分跑，刻意错开整点）。也可以随时手动触发：Actions → 更新 SideStore 源 → Run workflow。

> ⚠️ GitHub 的定时任务是 **best-effort**，不是保证：实测会迟到几分钟，负载高时还会直接丢掉这一轮，而且**频率越高丢得越多**（对照实测：每天一次 100% 准点、每小时基本不漏、`NixOS/nixpkgs` 的 10 分钟粒度只跑到约一半）。
> 丢一轮不影响结果——下一轮会补上，所以实际延迟通常 15~40 分钟，偶发更长。
> 另：**新建的工作流，cron 要先被 GitHub「认领」**。本仓库实测：cron 变更后 **4 小时 48 分**才跑出第一次定时，此前一次都没有；推一个默认分支上的提交能有效催熟（这次是删掉调试文件的那次推送，54 分钟后定时就到点了）。这期间配置是对的，**别反复改表达式 —— 每改一次，认领倒计时就重置一次**。
> 认领刚完成的头几个小时也可能比稳态稀疏（本仓库首 5 小时里约 20 个槽位只跑成 1 次）。
> 真要「秒级」，工作流已经留了 `repository_dispatch` 入口（见下）。

每轮做的事：

```
检查上游 Release（--refresh） → 重新生成 apps.json → verify_source.py 结构校验
  → 有变更才提交到本仓库 → 同步产物到 cnb.cool
```

- 单次实测约 **12 秒**，公开仓库的 Actions 分钟数免费不限量，约 96 次/天
- 只在检测到真实变更时才产生提交，没有新版本就不动
- **校验不通过就不提交**：宁可这轮不动，也不把一个结构坏掉的源推上去（某个 app 的 `releases` 变成空数组时，SideStore 会整体解码失败、整个源都加载不了）
- 某个仓库抓取失败时会**沿用上一次生成的数据**，不会把那个应用从源里抹掉
- 同步到 cnb.cool 需要仓库里配好 `CNB_TOKEN` 与 `CNB_USER` 两个 Secrets；没配就自动跳过，只更新本仓库

### 为什么是轮询，不是「上游发版就触发」

想做到「上游一发版立刻同步」，需要在别的仓库发生 release 事件时触发本仓库的工作流。**GitHub 做不到这件事**：release 事件只在事件发生的那一个仓库里触发工作流，跨仓库收不到；官方给外部事件准备的机制是 `repository_dispatch`，但那需要上游主动往我们的 API 发请求——而给别人的仓库配 webhook，得先有那个仓库的管理权限。

所以现实可行的就是短间隔轮询。按官方文档，定时任务最短只能 5 分钟一次，且负载高时会被延迟、甚至丢弃排队中的任务（整点前后最严重，所以这里错开了整点）。对轮询来说偶尔丢一轮无所谓，下一轮会补上。

真想要「秒级」的话，工作流已经留了 `repository_dispatch` 入口（事件类型 `upstream-release`）：用 Cloudflare Workers 的 1 分钟定时之类去轮询上游 release，命中就打一次这个接口即可。

> 为什么不用 cnb.cool 自带的定时构建：CNB 免费额度只有 160 核时/月，且构建前要预冻结 5 分钟（0.08 核时），额度见底时**所有构建**都会在 Prepare 阶段失败（2026-09 就被 `laincat/Rules` 一个仓库烧光了）。GitHub 公开仓库的 Actions 分钟数免费不限量，且 runner 原生直连 GitHub Release，不需要任何镜像代理。

想手动更新：

```bash
# 本地跑（需要 Python 3.8+，只用标准库）
python tools/build_source.py --refresh      # 重新抓上游
python tools/verify_source.py --min-apps 6  # 校验
```

## 目录结构

```
apps.json                                    # 源文件本体，客户端消费的就是它
.github/workflows/update-source.yml          # 定时更新流水线
tools/build_source.py                        # 生成脚本（抓 GitHub Release + 探测 IPA 元数据）
tools/verify_source.py                       # 结构校验，提交前的守门人
tools/simulate_client.py                     # 模拟两个客户端的解析，回答「改完到底看不看得见」
cache/releases.json                          # 各仓库的 Release 列表缓存
cache/probes.json                            # IPA 元数据缓存（按 URL 永久复用，上游发新版才新增）
cache/icons.json                             # 图标可达性缓存
```

### 参数

```bash
python tools/build_source.py                 # 用缓存，联网最少
python tools/build_source.py --refresh       # 重新抓 Release 列表
python tools/build_source.py --reprobe       # 连 IPA 元数据也重探（一般不需要）
python tools/build_source.py --versions 4    # 稳定版轨道保留最近 4 个（便于回退）
```

## 数据准确性

源里的 **Bundle ID、版本号、最低系统版本都是从 IPA 包内读出来的**，不是猜的，也不是抄 README：

- 对每个 IPA 发 HTTP Range 请求，只读 zip 尾部的中央目录 + `Payload/*.app/Info.plist`（几十 KB，**不下载整包**），解析 `CFBundleIdentifier` / `CFBundleShortVersionString` / `MinimumOSVersion` / 实际字节数
- 同一应用的测试版与稳定版做 Bundle ID 一致性校验，不一致的丢弃
- 跨版本 Bundle ID 不一致的版本会被丢弃
- 图标取自各仓库对应 tag 下的 AppIcon 资源（1024×1024），探测失败自动回退为仓库头像
- **源自身的 logo** 用的是 `https://github.com/laincat.png`（GitHub 头像，会 302 到 `avatars.githubusercontent.com`），换头像时源里自动跟着变

## 为什么只有 EhPanda 有测试版

6 个仓库的发布记录全扫过（含 tag 名带 beta/alpha/rc/nightly 但没打预发布标记的）：

| 仓库 | 情况 | 结论 |
|---|---|---|
| Kazumi | 最近 100+ 个发布里没有任何 beta/alpha/rc | 无测试版 |
| Animeko | 有 `v6.1.0-beta01`，但更新日志与正式版 6.1.0 **逐字相同**，且包内真实 Bundle ID 就是 `org.animeko.animeko`（**没有**独立的 beta ID，`org.animeko.animeko.beta` 是别的源编出来的） | 不收 |
| EhPanda | `3.0.0`，比稳定版 2.8.1 新一个月（离线下载、文件夹分类等） | **收录** |
| VeneraX | `v2.1.8-beta.1`，比稳定版 2.3.2 **落后 5 个小版本**；作者发布说明写着「内部测试版，仅用于开发验证，**请勿分发**」 | 不收（版本号更低，SideStore 也不会显示） |
| Breeze | 最近 100 个发布里无 beta/alpha | 无测试版 |
| PicaX | 仓库总共只有 13 个发布，无预发布 | 无测试版 |

## 注意事项

1. **EhPanda 需 iOS 26.0 及以上**，稳定版 2.8.1 与测试版 3.0.0 都是这个要求。
2. **免费 Apple ID 的侧载限制**：同时最多 3 个自签应用，签名 7 天过期（靠 SideStore 自身续签）。源里有 6 个应用，装不下全部。
3. **PicaX 选的是不含 Watch 组件的包**（`PicaX-unsigned.ipa`）。带 Watch 的版本在免费账号签名时容易因附加 Target 失败。
4. **EhPanda 含 Share Extension、PicaX 含 Widget**，签名时会额外占用标识符；报错可换用不带扩展的版本。
5. **本仓库只做索引，IPA 全部由各项目自己在 GitHub Release 发布**，未重新打包、未修改任何二进制。使用请遵守各项目开源协议（GPL-3.0 / AGPL-3.0 / MPL-2.0 / MIT）及当地法律法规。
