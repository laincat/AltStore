# 数据准确性

源里的 **Bundle ID、版本号、最低系统版本都是从 IPA 包内读出来的**，不是猜的，也不是抄 README：

- 对每个 IPA 发 HTTP Range 请求，只读 zip 尾部的中央目录 + `Payload/*.app/Info.plist`（几十 KB，**不下载整包**），解析 `CFBundleIdentifier` / `CFBundleShortVersionString` / `MinimumOSVersion` / 实际字节数
- **声明的 `version` / `buildVersion` 一律取包内真实值，不取 tag**（SideStore 会逐字比对，见 [clients.md](clients.md)）；tag 另存在 `releaseTag` 字段里，预发布的 tag 还会写进更新日志开头
- 同一应用的测试版与稳定版做 Bundle ID 一致性校验，不一致的丢弃
- 跨版本 Bundle ID 不一致的版本会被丢弃
- 图标取自各仓库对应 tag 下的图标资源（**必须是 1024×1024**）。同名文件在不同项目里位置不一样：多数 Flutter 项目在 `ios/Runner/…/AppIcon`，venera-prime 用的却是 `assets/app_icon.png`。**光确认「文件存在」不够，还要量尺寸** —— venera-next 的 `assets/app_icon.png` 只有 512×512，1024×1024 的那张在 iOS appiconset 里；venera-ssr 更麻烦，两张都叫同名、都真是 1024×1024，**但内容不是同一张**，所以按 iOS appiconset 那张走（那才是 App Store 图标）。**用 tag 而不是分支名作 ref**，所以仓库默认分支叫 `main` 还是 `master` 都无所谓；探测失败自动回退为仓库头像
- **源自身的 logo** 用的是 `https://github.com/laincat.png`（GitHub 头像，会 302 到 `avatars.githubusercontent.com`），换头像时源里自动跟着变

README 的应用清单由 `tools/render_docs.py` 从 `apps.json` 生成，所以表格里的版本号永远和源一致；如果有出入，以 `apps.json` 为准。
