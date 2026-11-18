# 使用注意事项

1. **EhPanda 需 iOS 26.0 及以上**（稳定版与测试版都是这个要求），低于这个系统版本装不上。
2. **免费 Apple ID 的侧载限制**：同时最多 3 个自签应用，签名 7 天过期（靠 SideStore 自身续签）。源里应用较多，装不下全部。
3. **PicaX 选的是不含 Watch 组件的包**（`PicaX-unsigned.ipa`）。带 Watch 的版本在免费账号签名时容易因附加 Target 失败。
4. **EhPanda 含 Share Extension、PicaX 含 Widget**，签名时会额外占用标识符；报错可换用不带扩展的版本。
5. **源里有四个 Venera 系阅读器**：VeneraX（`io.github.kyosee.venera`）、Venera Prime（`com.github.wgh136.venera.prime`）、VeneraNext（`com.github.cyrilpeng.veneranext`）、Venera-SSR（`com.github.kiastr.venera-ssr`）。四者是**独立应用**（不同作者维护的 Venera 分支），可以同时安装 —— 但功能高度重叠，实际按需选一个就够。
   - 其中 **Venera-SSR** 主要在「阅读增强」上做文章：黑白漫画 AI 上色、Anime4K 超分、图片内嵌文字的 OCR 翻译。源里取的是**标准版** iOS 包；上游的「翻译版」只出了 Android。
   - 四个 Venera 的 tint 有意分开：三个蓝（`#4A8FE7` / `#0784FC` / `#2090E0`）+ 一个黄（`#C4BA12`），列表里好认。黄会按白底可读性压过明度，别照着图标原色改。
6. **HGhubX 的 Bundle ID 是 `com.hghubx.app`**（2.x 起）。它与旧版 `com.hghub.huangguo` 是两个应用，升级不会覆盖旧的，需要自己卸载旧包。
7. **未签名安装包**：多数上游只提供未签名 IPA，需要用自己的 Apple ID 重签；TrollStore 可直接导入。签名后的应用一星期需续签一次（SideStore 自动处理）。
8. **本仓库只做索引**，IPA 全部由各项目自己在 GitHub Release 发布，未重新打包、未修改任何二进制。开源应用请遵守各项目许可证；AvPlay 上游未提供应用源代码或开源许可证。
