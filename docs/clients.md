# 两个客户端的差异（重要）

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
    { "track": "stable",  "releases": [ /* 当前稳定版 */ ] },
    { "track": "nightly", "releases": [ /* 测试版 */ ] }
  ],
  "versions": [ /* 测试版, 稳定版 */ ],  // ← LiveContainer 走这里，只取第 1 条
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

## 测试版（nightly 轨道）

| 客户端 | 怎么才能拿到测试版 |
|---|---|
| **LiveContainer** | **什么都不用做**。当源里 `versions[0]` 是测试版时，列表里直接显示、点安装就是它，旁边带「测试版」角标 |
| **SideStore / AltStore** | 要手动开开关：`设置 → Beta Testing → 打开 Beta Updates`（轨道选 `nightly`，默认就是它，不用改） |

SideStore 那三层门槛（源码 `AltStore/Core/Model/StoreApp.swift`）：

1. `isBetaUpdatesEnabled` —— 设置里的 `Beta Updates` 开关，**默认 false**
2. `betaUdpatesTrack` —— 轨道名，默认 `nightly`（下拉框只提供 `alpha` 和 `nightly`）
3. `betaSemVer >= stableSemVer` —— 测试版版本号必须不低于稳定版，否则不显示

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

## ⚠️ 为什么 Animeko 写的是 6.2.0，而不是上游的 6.2.0-alpha01

因为**写成 `6.2.0-alpha01` 就一定装不上**。SideStore 安装前会拿声明值和包内真实值逐字核对，
源码 `AltStore/Core/Operations/VerifyAppOperation.swift`：

```swift
// 第 5 步：版本 & build 版本校验
if let buildVersion {
    guard buildVersion == appBundle.buildVersion else {
        throw VerificationError.mismatchedBuildVersion(...)
    }
}
if version != appBundle.version {
    throw VerificationError.mismatchedVersion(...)      // ← 不一致就中止安装
}
```

而 Animeko 的预发布包**里面**写的是：

| 字段 | 包内真实值 | 上游 tag |
|---|---|---|
| `CFBundleShortVersionString` | `6.2.0` | `v6.2.0-alpha01` |
| `CFBundleVersion` | `60201` | ← 预发布序号其实编码在这里（alpha01 → …01） |

所以 `version` **只能**填 `6.2.0`、`buildVersion` 填 `60201`。想一眼看出是哪个预发布，就只能写进**说明文字**——
每条预发布的更新日志开头会自动加一行 `🧪 预发布 <tag>（日期）`。

> 顺带一提：把预发布拆成独立 app 条目、`version` 直接写 tag 串的那种源，在 SideStore 上就是被这一步挡住的。

## 本地就能验证，不用装到手机上

```bash
python tools/simulate_client.py                        # 两个客户端都算
python tools/simulate_client.py --client livecontainer
python tools/simulate_client.py --client sidestore
```

这个脚本把两家客户端的解析逻辑都照抄成了 Python，直接告诉你「谁会看到、会安装哪个版本」。示例输出（2026-09 的 Animeko / EhPanda）：

```
Animeko   (org.animeko.animeko)
   SideStore · 关 Beta → ['6.1.0']
   SideStore · 开 Beta → ['6.2.0']
      ⚠️ ['6.2.0'] 只有开了 Beta 开关才可见
   LiveContainer       → 会安装 6.2.0 (60201)  [BETA 角标]   [来源：扁平 versions[0]]
```

它还会报告「两个客户端结论分歧」的条目 —— 万一以后扁平 `versions` 忘了放测试版，这里会立刻报出来。

## ⚠️ 为什么不用「拆成两个 app 条目」的做法

有些源（例如 `maxchang3/ani-altstore-source`）把测试版拆成**独立的 app 条目**（`Animeko` + `Animeko (Pre-Release)`）。它的 `versions` 是**不带 `releaseChannels` 的扁平列表**，所以预发布在两边都会一直显示、不需要任何开关。

看起来省事，但代价是拆出来的条目**必须编造一个 Bundle ID**（参考源写的是 `org.animeko.animeko.beta`），而 Animeko 测试包内的真实 ID 是 `org.animeko.animeko`：

| 约束 / 校验 | 出处 | 后果 |
|---|---|---|
| `StoreApp` 唯一约束 `(sourceIdentifier, bundleIdentifier)` | CoreData 模型 | 同一源内两个条目**不能共用 Bundle ID**，否则会被合并成一个 |
| 于是测试版条目只能**编造 ID** | 参考源写的是 `org.animeko.animeko.beta` | 与包内真实 ID 不符 |
| `verifyApp` 要求源声明 ID **必须等于** IPA 内真实 ID | `VerifyAppOperation.swift` | 安装时抛 `mismatchedBundleIdentifiers` |
| 该步骤是**安装流水线第 2 步** | `OperationStepDefinition.install` | 默认就在流程里 |
| 校验开关 `isBundleIDVerificationEnabled` 默认 **true** | `UserDefaults+AltStore.swift` | 且**设置界面里没有这个开关** |

**结论**：拆条目的做法在 SideStore 上是「看得见、装不上」。本仓库不这么做——保留规范的 `releaseChannels` 轨道，**同时**用扁平 `versions` 照顾 LiveContainer，两边都看得见、也都装得上。
