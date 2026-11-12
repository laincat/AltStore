# -*- coding: utf-8 -*-
"""52 个补充应用的上游配置：每个条目只依赖自己的 GitHub repo，不依赖第三方聚合源。

本文件由 investigate/gen_apps_upstream.py 生成（只读扫描 + 链接实测），可人工维护。
字段说明：
  asset        —— 从该 repo 的 Release 资产名归纳，数字段通配以跟随版本更新
  iconURL      —— 上游仓库自有图标；无合格图标时回退到 owner 头像（build_source 默认）
  screenshots  —— 上游仓库自有截图，逐条实测 200 后才写入；拿不到就不填
  installNotes —— 从上游 README 逐条核对的签名/JIT/Bundle ID 约束，附证据链接
"""
import re

# IPA 缺 MinimumOSVersion 时只按上游 README 明示值兜底，绝不猜默认值。
MIN_OS_FALLBACKS = {'lpfoj/lsx4': '26.0'}

UPSTREAM_APPS = [
    {
        "repo": 'altstoreio/AltStore',
        "asset": lambda n: re.match('^AltStore_Classic_Notarized_[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'AltStore',
        "developerName": 'altstoreio',
        "subtitle": '实用工具 · 上游 altstoreio',
        "category": 'utilities',
        "tintColor": '#CFA94A',
        "installNotes": '官方上游（altstoreio/AltStore），Bundle ID com.rileytestut.AltStore 属实，与已安装的官方 AltStore 同 ID。上游说明它是普通沙盒 App，不需特殊 entitlements。若设备上已装官方 AltStore，本条目会覆盖同一 ID。',
        "installNotesSource": 'https://github.com/altstoreio/AltStore#minimum-project-requirements',
        "description": (
            'AltStore is an iOS application that allows you to sideload other apps (.ipa files) onto your iOS device with just your Apple ID.…'
            "\n\n上游项目：https://github.com/altstoreio/AltStore"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Apollo-Reborn/Apollo-Reborn',
        "asset": lambda n: re.match('^Apollo\\-Reborn\\-[0-9A-Za-z._+-]+\\-GLASS\\.ipa$', n) is not None,
        "name": 'Apollo for Reddit - GLASS',
        "developerName": 'Apollo-Reborn',
        "subtitle": '影音娱乐 · 上游 Apollo-Reborn',
        "category": 'entertainment',
        "tintColor": '#B655CE',
        "iconURL": 'https://raw.githubusercontent.com/Apollo-Reborn/Apollo-Reborn/main/Resources/apollo-reborn-options-icon.png',
        "screenshots": ['https://raw.githubusercontent.com/Apollo-Reborn/Apollo-Reborn/main/Resources/ApolloRebornPreviewBanner.jpg', 'https://raw.githubusercontent.com/Apollo-Reborn/Apollo-Reborn/main/Resources/screenshots/banned-profile-ui/compact-card.png', 'https://raw.githubusercontent.com/Apollo-Reborn/Apollo-Reborn/main/Resources/screenshots/banned-profile-ui/long-press-peek.png'],
        "installNotes": '第三方复刻：原 Apollo 已于 2023-06 关停，本条目沿用原官方 Bundle ID com.christianselig.Apollo。上游明确建议侧载时换一个不含 Apollo 的 Bundle ID。GLASS 构建含约 6 个 App Extension，一次侧载约占 7 个 App ID，而免费 Apple ID 每 7 天只有 10 个名额；名额紧张请改用 NOEXTENSIONS 变体（只需 1 个 App ID）。另需自备 Reddit API Key；原生推送（APNs）需要 aps-environment entitlement，仅付费开发者账号可用。',
        "installNotesSource": 'https://github.com/Apollo-Reborn/Apollo-Reborn#which-build-should-i-install',
        "description": (
            'iOS tweak for Apollo for Reddit app that lets you continue using Apollo with your own API keys after its shutdown in June 2023. The tweak also unlocks several Ultra features and includes several enhancements and fixes'
            "\n\n上游项目：https://github.com/Apollo-Reborn/Apollo-Reborn"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Lakr233/Asspp',
        "asset": lambda n: re.match('^Asspp\\.ipa$', n) is not None,
        "name": 'Asspp',
        "developerName": 'Lakr233',
        "subtitle": '实用工具 · 上游 Lakr233',
        "category": 'utilities',
        "tintColor": '#D043B2',
        "iconURL": 'https://raw.githubusercontent.com/Lakr233/Asspp/main/Asspp/App/AppIcon.icon/Assets/pineapple.png',
        "screenshots": ['https://raw.githubusercontent.com/Lakr233/Asspp/main/Resources/Screenshots/Apptisan_Asspp.png'],
        "description": (
            'The Ultimate Multi-Region App Store Manager'
            "\n\n上游项目：https://github.com/Lakr233/Asspp"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'thebcd69/bcd-games',
        "asset": lambda n: re.match('^BCD\\.ipa$', n) is not None,
        "name": 'BCD',
        "developerName": 'thebcd69',
        "subtitle": '影音娱乐 · 上游 thebcd69',
        "category": 'entertainment',
        "tintColor": '#32D2CD',
        "iconURL": 'https://raw.githubusercontent.com/thebcd69/bcd-games/main/assets/readme/icon.png',
        "screenshots": ['https://raw.githubusercontent.com/thebcd69/bcd-games/main/assets/readme/4937d84c7571.jpg', 'https://raw.githubusercontent.com/thebcd69/bcd-games/main/assets/readme/4be504c431c8.jpg', 'https://raw.githubusercontent.com/thebcd69/bcd-games/main/assets/readme/908d936c7497.jpg'],
        "installNotes": '需 JIT。免费 Apple ID 同时只能保持 3 个侧载 App；上游给出的组合是 LiveContainer + StikDebug 提供 JIT + GetMoreRam 提供 Increased Memory Limit entitlement，再把 BCD 放进 LiveContainer 运行。',
        "installNotesSource": 'https://github.com/thebcd69/bcd-games',
        "description": (
            'A fast, controller-friendly launcher with Steam, GOG and Epic Games built in'
            "\n\n上游项目：https://github.com/thebcd69/bcd-games"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'AhmedBafkir/DLiPA',
        "asset": lambda n: re.match('^DLiPA_v[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'DLiPA',
        "developerName": 'AhmedBafkir',
        "subtitle": '实用工具 · 上游 AhmedBafkir',
        "category": 'utilities',
        "tintColor": '#44CFAA',
        "iconURL": 'https://raw.githubusercontent.com/AhmedBafkir/DLiPA/main/images/icon.png',
        "screenshots": ['https://raw.githubusercontent.com/AhmedBafkir/DLiPA/main/images/1.PNG', 'https://raw.githubusercontent.com/AhmedBafkir/DLiPA/main/images/2.PNG', 'https://raw.githubusercontent.com/AhmedBafkir/DLiPA/main/images/3.PNG'],
        "description": (
            'An iOS app inspired by the ipatool project. It allows users to download, install, and share App Store applications using their Apple ID, with support for downloading older versions — no jailbreak required'
            "\n\n上游项目：https://github.com/AhmedBafkir/DLiPA"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'moliango/doer',
        "asset": lambda n: re.match('^doer\\-unsigned\\.ipa$', n) is not None,
        "name": 'Doer',
        "developerName": 'moliango',
        "subtitle": '实用工具 · 上游 moliango',
        "category": 'utilities',
        "tintColor": '#3D4FC2',
        "iconURL": 'https://raw.githubusercontent.com/moliango/doer/main/Doer/AppIcon.icon/Assets/DoerIcon.png',
        "description": (
            'Doer follows a thin ViewController / fat ViewModel pattern with iOS 15-compatible observation. Since the project sets SWIFTDEFAULTACTORISOLATION = MainActor, all UI-adjacent code runs on the main actor by default'
            "\n\n上游项目：https://github.com/moliango/doer"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'OatmealDome/dolphin-ios',
        "asset": lambda n: re.match('^Non\\-Jailbroken\\.ipa$', n) is not None,
        # 该 repo 的 release 全部是 prerelease，只能把预发布当稳定轨道。
        "prereleaseAsStable": True,
        "name": 'DolphiniOS',
        "developerName": 'OatmealDome',
        "subtitle": '影音娱乐 · 上游 OatmealDome',
        "category": 'entertainment',
        "tintColor": '#B33BCE',
        "description": (
            'DolphiniOS is a port of the Dolphin Emulator to iOS and iPadOS. For installation instructions and downloads, check our website'
            "\n\n上游项目：https://github.com/OatmealDome/dolphin-ios"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'MaftyManicEMU/DukeX',
        "asset": lambda n: re.match('^DukeX\\.v[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'DukeX',
        "developerName": 'MaftyManicEMU',
        "subtitle": '影音娱乐 · 上游 MaftyManicEMU',
        "category": 'entertainment',
        "tintColor": '#3A41CF',
        "iconURL": 'https://raw.githubusercontent.com/MaftyManicEMU/DukeX/master/altsource/assets/dukex-icon.png',
        "screenshots": ['https://raw.githubusercontent.com/MaftyManicEMU/DukeX/master/altsource/assets/carousel-screenshots.png', 'https://raw.githubusercontent.com/MaftyManicEMU/DukeX/master/altsource/assets/landscape-screenshots.png'],
        "installNotes": 'xemu 前端，TCG 带 version-aware JIT；iOS 26+ 走 StikDebug 的 Universal.js JIT 交接。上游说明不含 Xbox 系统文件与游戏镜像，兼容性与性能依设备/iOS 版本而异。',
        "installNotesSource": 'https://github.com/MaftyManicEMU/DukeX',
        "description": (
            'DukeX is an experimental iOS and macOS frontend for xemu'
            "\n\n上游项目：https://github.com/MaftyManicEMU/DukeX"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Leviidev/Fathom',
        "asset": lambda n: re.match('^Fathom\\.ipa$', n) is not None,
        "name": 'Fathom',
        "developerName": 'Leviidev',
        "subtitle": '影音娱乐 · 上游 Leviidev',
        "category": 'entertainment',
        "tintColor": '#52DA84',
        "installNotes": 'x86-64 PC 模拟器，上游明确需要 get-task-allow 与 dynamic-codesigning 等 entitlements 才能让 JIT 写可执行内存；签名工具不给这些权限时无法运行。',
        "installNotesSource": 'https://github.com/Leviidev/Fathom',
        "description": (
            'An x86-64 PC emulator for iOS. Fathom runs x86-64 Linux programs on an iPhone or iPad by'
            "\n\n上游项目：https://github.com/Leviidev/Fathom"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'claration/feather',
        "asset": lambda n: re.match('^Feather\\.ipa$', n) is not None,
        "name": 'Feather',
        "developerName": 'claration',
        "subtitle": '实用工具 · 上游 claration',
        "category": 'utilities',
        "tintColor": '#ACCD4C',
        "iconURL": 'https://raw.githubusercontent.com/claration/feather/main/Feather/Resources/AppIcon.icon/Assets/feather%205.png',
        "description": (
            'Sideloading app meant for developer certificates'
            "\n\n上游项目：https://github.com/claration/feather"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'pookjw/HermesEnabler',
        "asset": lambda n: re.match('^HermesEnabler\\.ipa$', n) is not None,
        "name": 'HermesEnabler',
        "developerName": 'pookjw',
        "subtitle": '实用工具 · 上游 pookjw',
        "category": 'utilities',
        "tintColor": '#4A57CF',
        "screenshots": ['https://raw.githubusercontent.com/pookjw/HermesEnabler/main/image.png'],
        "description": (
            'English · 한국어 · 简体中文 · 繁體中文 · 日本語 · Español · Français · Deutsch · Português'
            "\n\n上游项目：https://github.com/pookjw/HermesEnabler"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Leviidev/Husk',
        "asset": lambda n: re.match('^Husk\\.ipa$', n) is not None,
        "name": 'Husk',
        "developerName": 'Leviidev',
        "subtitle": '实用工具 · 上游 Leviidev',
        "category": 'utilities',
        "tintColor": '#2C62CE',
        "screenshots": ['https://raw.githubusercontent.com/Leviidev/Husk/main/Screenshots/beach-buggy-racing-2.jpeg', 'https://raw.githubusercontent.com/Leviidev/Husk/main/Screenshots/game-settings.png', 'https://raw.githubusercontent.com/Leviidev/Husk/main/Screenshots/geometry-dash.jpeg'],
        "installNotes": '游戏需要 JIT；上游给出的无 JIT 替代方案是导入安装证书后走 Play without JIT。',
        "installNotesSource": 'https://github.com/Leviidev/Husk',
        "description": (
            'Add an APK, tap it, and it opens full-screen'
            "\n\n上游项目：https://github.com/Leviidev/Husk"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'kuscholar/iDeck',
        "asset": lambda n: re.match('^iDeck\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        # 该 repo 的 release 全部是 prerelease，只能把预发布当稳定轨道。
        "prereleaseAsStable": True,
        "name": 'iDeck',
        "developerName": 'kuscholar',
        "subtitle": '影音娱乐 · 上游 kuscholar',
        "category": 'entertainment',
        "tintColor": '#945ACE',
        "iconURL": 'https://raw.githubusercontent.com/kuscholar/iDeck/main/docs/assets/ideck/icon.png',
        "installNotes": '把 Steam Big Picture 带到 iOS，需 JIT 且签名要保留 development debugging 权限 （get-task-allow）；上游强调「签名本身不会启用 JIT」，还需 StikDebug 之类的调试器附加。',
        "installNotesSource": 'https://github.com/kuscholar/iDeck',
        "description": (
            "iDeck brings Valve's real Steam client in Big Picture to your iPhone and iPad,"
            "\n\n上游项目：https://github.com/kuscholar/iDeck"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'mengangs/ipadn',
        "asset": lambda n: re.match('^iPadn\\-[0-9A-Za-z._+-]+\\-unsigned\\.ipa$', n) is not None,
        "name": 'iPadn',
        "developerName": 'mengangs',
        "subtitle": '实用工具 · 上游 mengangs',
        "category": 'utilities',
        "tintColor": '#D4532B',
        "iconURL": 'https://raw.githubusercontent.com/mengangs/ipadn/main/docs/images/icon.png',
        "description": (
            '在 iPhone 和 iPad 上搜索、下载、安装你拥有的 App。'
            "\n\n上游项目：https://github.com/mengangs/ipadn"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'intraducine/iridium',
        "asset": lambda n: re.match('^Iridium\\-unsigned\\.ipa$', n) is not None,
        "name": 'Iridium',
        "developerName": 'intraducine',
        "subtitle": '影音娱乐 · 上游 intraducine',
        "category": 'entertainment',
        "tintColor": '#6F44D5',
        "iconURL": 'https://raw.githubusercontent.com/intraducine/iridium/main/iridium-fex-ios/Source/Tools/FEXConfig/icon.png',
        "installNotes": 'Windows/主机游戏运行前端，部分游戏需按上游文档配置 JIT（仓库内有 builtin-stikjit 文档）。',
        "installNotesSource": 'https://github.com/intraducine/iridium',
        "description": (
            'Play Windows and console games on iPhone and iPad. Import games you own into one'
            "\n\n上游项目：https://github.com/intraducine/iridium"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'XITRIX/iTorrent',
        "asset": lambda n: re.match('^iTorrent\\.ipa$', n) is not None,
        "name": 'iTorrent',
        "developerName": 'XITRIX',
        "subtitle": '影音娱乐 · 上游 XITRIX',
        "category": 'entertainment',
        "tintColor": '#5437D7',
        "description": (
            '[AltStore Classic Button]: https://img.shields.io/badge/Download-AltStoreClassic-green?style=flat'
            "\n\n上游项目：https://github.com/XITRIX/iTorrent"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'LinkPass888/Kazumi-Swift',
        "asset": lambda n: re.match('^Kazumi_ios_[0-9A-Za-z._+-]+_no_sign\\.ipa$', n) is not None,
        "name": 'Kazumi-Swift',
        "developerName": 'LinkPass888',
        "subtitle": '实用工具 · 上游 LinkPass888',
        "category": 'utilities',
        "tintColor": '#DB4DAE',
        "iconURL": 'https://raw.githubusercontent.com/LinkPass888/Kazumi-Swift/main/assets/images/logo/app-icon.png',
        "screenshots": ['https://raw.githubusercontent.com/LinkPass888/Kazumi-Swift/main/static/screenshot/01-recommend.png', 'https://raw.githubusercontent.com/LinkPass888/Kazumi-Swift/main/static/screenshot/02-detail.png', 'https://raw.githubusercontent.com/LinkPass888/Kazumi-Swift/main/static/screenshot/03-player.png'],
        "description": (
            '基于自定义规则的番剧采集与在线观看客户端，带弹幕。'
            "\n\n上游项目：https://github.com/LinkPass888/Kazumi-Swift"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Mac-XK/KMusic',
        "asset": lambda n: re.match('^_[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'KMusic',
        "developerName": 'Mac-XK',
        "subtitle": '影音娱乐 · 上游 Mac-XK',
        "category": 'entertainment',
        "tintColor": '#A2D142',
        "description": (
            '一款基于 SwiftUI 开发的多源音乐聚合播放器，支持 iOS/macOS 平台。'
            "\n\n上游项目：https://github.com/Mac-XK/KMusic"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'missuo/kumone',
        "asset": lambda n: re.match('^Kumone\\-iOS\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'Kumone',
        "developerName": 'missuo',
        "subtitle": '影音娱乐 · 上游 missuo',
        "category": 'entertainment',
        "tintColor": '#C253D5',
        "iconURL": 'https://raw.githubusercontent.com/missuo/kumone/main/AppIcon.icon/Assets/Background.png',
        "screenshots": ['https://raw.githubusercontent.com/missuo/kumone/main/docs/screenshot-daily.png', 'https://raw.githubusercontent.com/missuo/kumone/main/docs/screenshot-home.png', 'https://raw.githubusercontent.com/missuo/kumone/main/docs/screenshot-lyrics.png'],
        "installNotes": 'CarPlay 为可选功能，需 Apple 特批的 CarPlay audio entitlement，绝大多数账号拿不到；默认构建里该功能是关闭的。',
        "installNotesSource": 'https://github.com/missuo/kumone',
        "description": (
            '雲の音 — A native music player for macOS and iOS'
            "\n\n上游项目：https://github.com/missuo/kumone"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'LightNovelShelf/Flutter',
        "asset": lambda n: re.match('^app\\-ios\\-unsigned\\.ipa$', n) is not None,
        "name": 'LightNovelShelf',
        "developerName": 'LightNovelShelf',
        "subtitle": '阅读 · 上游 LightNovelShelf',
        "category": 'books',
        "tintColor": '#3CC350',
        "description": (
            '轻书架官方 Flutter 客户端。目前面向 Android 与 iOS 平台进行测试，macOS / Windows / Linux 需要自行编译测试。'
            "\n\n上游项目：https://github.com/LightNovelShelf/Flutter"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'mxhm11cr/LinuxRunner',
        "asset": lambda n: re.match('^LinuxRunner\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'LinuxRunner',
        "developerName": 'mxhm11cr',
        "subtitle": '影音娱乐 · 上游 mxhm11cr',
        "category": 'entertainment',
        "tintColor": '#3BC431',
        "iconURL": 'https://raw.githubusercontent.com/mxhm11cr/LinuxRunner/main/app/Icons/icon1337.png',
        "screenshots": ['https://raw.githubusercontent.com/mxhm11cr/LinuxRunner/main/assets/screenshots/applications/firefox-github.jpg', 'https://raw.githubusercontent.com/mxhm11cr/LinuxRunner/main/assets/screenshots/applications/freecad-metal-iphone.jpg', 'https://raw.githubusercontent.com/mxhm11cr/LinuxRunner/main/assets/screenshots/applications/vesktop-redacted.png'],
        "installNotes": 'ARM64 Linux 用户态，JIT 是可选加速，上游明确说明「安装和使用都不需要 JIT」；解释器路径始终可用。安装时需与所用工具匹配的签名/描述文件。',
        "installNotesSource": 'https://github.com/mxhm11cr/LinuxRunner',
        "description": (
            'LinuxRunner brings ARM64 Linux userspace to iPhone and iPad through a custom instruction interpreter, an optional JIT engine and a Linux compatibility layer. Run Linux applications, explore desktop environments and take your workspace to an external display'
            "\n\n上游项目：https://github.com/mxhm11cr/LinuxRunner"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'LiveContainer/LiveContainer',
        "asset": lambda n: re.match('^LiveContainer\\+SideStore\\.ipa$', n) is not None,
        "name": 'LiveContainer+SideStore',
        "developerName": 'LiveContainer',
        "subtitle": '影音娱乐 · 上游 LiveContainer',
        "category": 'entertainment',
        "tintColor": '#C65A3F',
        "iconURL": 'https://raw.githubusercontent.com/LiveContainer/LiveContainer/main/Resources/AppIconGrey60x60%402x.png',
        "screenshots": ['https://raw.githubusercontent.com/LiveContainer/LiveContainer/main/screenshots/livecontainer_icon.png', 'https://raw.githubusercontent.com/LiveContainer/LiveContainer/main/screenshots/release.png'],
        "installNotes": 'App 容器/启动器。iOS 26 以下且有 JIT 时可完全绕过 codesign；无 JIT 时用与 LiveContainer 相同的证书签名被装载的 App。上游重要提醒：所有 App 都装在容器内，第三方闭源构建能读取你的全部数据，请只用官方构建。',
        "installNotesSource": 'https://github.com/LiveContainer/LiveContainer#important-notice-regarding-third-party-builds-of-livecontainer',
        "description": (
            'Crowdin Project: ![Crowdin](https://crowdin.com/project/livecontainer) &nbsp;| &nbsp; Documentation:livecontainer.github.io'
            "\n\n上游项目：https://github.com/LiveContainer/LiveContainer"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'lpfoj/lsx4',
        "asset": lambda n: re.match('^LSX4\\-JIT\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'LSX4',
        "developerName": 'lpfoj',
        "subtitle": '影音娱乐 · 上游 lpfoj',
        "category": 'entertainment',
        "tintColor": '#C7523D',
        "screenshots": ['https://raw.githubusercontent.com/lpfoj/lsx4/main/assets/screenshots/a-monsters-expedition-poco.png', 'https://raw.githubusercontent.com/lpfoj/lsx4/main/assets/screenshots/a-short-hike.jpg', 'https://raw.githubusercontent.com/lpfoj/lsx4/main/assets/screenshots/absolute-drift-poco.png'],
        "installNotes": 'PS4/PS5 模拟器，iOS 26+ 使用公开 JIT release；兼容性依平台与设备而异。本条目的 IPA 内 Info.plist 缺 MinimumOSVersion 键（实测），源里的 26.0 取自上游 README 明示的「iOS (PS4 & PS5, iOS 26+)」，不是猜的默认值。',
        "installNotesSource": 'https://github.com/lpfoj/lsx4',
        "description": (
            'LSX4 is an open-source PlayStation 4/5 emulator for Android and iOS. Both platforms support PS4 and PS5 gameplay'
            "\n\n上游项目：https://github.com/lpfoj/lsx4"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'willfaust/Madeira',
        "asset": lambda n: re.match('^Madeira\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'Madeira',
        "developerName": 'willfaust',
        "subtitle": '影音娱乐 · 上游 willfaust',
        "category": 'entertainment',
        "tintColor": '#BF3B84',
        "installNotes": 'JIT 需要调试器附加（iOS 只在调试时允许），上游建议用 StikDebug 自动模式；因 JIT 限制无法上架 App Store。免费 Apple ID 可签名，但需按周期续签。',
        "installNotesSource": 'https://github.com/willfaust/Madeira/blob/main/docs/JIT.md',
        "description": (
            'Madeira runs Windows PC games on an iPhone, with no jailbreak. Games run as they'
            "\n\n上游项目：https://github.com/willfaust/Madeira"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'kodjodevf/mangayomi',
        "asset": lambda n: re.match('^Mangayomi\\-v[0-9A-Za-z._+-]+\\-ios\\.ipa$', n) is not None,
        "name": 'Mangayomi',
        "developerName": 'kodjodevf',
        "subtitle": '阅读 · 上游 kodjodevf',
        "category": 'books',
        "tintColor": '#7DC639',
        "iconURL": 'https://raw.githubusercontent.com/kodjodevf/mangayomi/main/assets/app_icons/icon.png',
        "screenshots": ['https://raw.githubusercontent.com/kodjodevf/mangayomi/main/repo/images/screenshots/image_0_black.webp', 'https://raw.githubusercontent.com/kodjodevf/mangayomi/main/repo/images/screenshots/image_0_default.webp', 'https://raw.githubusercontent.com/kodjodevf/mangayomi/main/repo/images/screenshots/image_1_black.webp'],
        "installNotes": '上游说明只有 > 0.5.2 的版本才带签名、才兼容 AltStore/SideStore；本条目版本已满足。',
        "installNotesSource": 'https://github.com/kodjodevf/mangayomi',
        "description": (
            'Mangayomi is an open-source Flutter app for reading manga, novels, and watching animes across multiple platforms'
            "\n\n上游项目：https://github.com/kodjodevf/mangayomi"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Manic-EMU/ManicEMU',
        "asset": lambda n: re.match('^ManicEMU\\.v[0-9A-Za-z._+-]+\\.SideloadJIT\\.ipa$', n) is not None,
        "name": 'ManicEMU',
        "developerName": 'Manic-EMU',
        "subtitle": '影音娱乐 · 上游 Manic-EMU',
        "category": 'entertainment',
        "tintColor": '#A346DD',
        "iconURL": 'https://raw.githubusercontent.com/Manic-EMU/ManicEMU/main/System.core/RomPatcher/webapp/app_icon_192.png',
        "screenshots": ['https://raw.githubusercontent.com/Manic-EMU/ManicEMU/main/images_manicemu_ver5_a01.jpg', 'https://raw.githubusercontent.com/Manic-EMU/ManicEMU/main/images_manicemu_ver5_a02.jpg', 'https://raw.githubusercontent.com/Manic-EMU/ManicEMU/main/images_manicemu_ver5_a03.jpg'],
        "installNotes": '多主机模拟器，上游说明 App Store 版与侧载版在 JIT 可用性上可能不同，功能随 JIT 变化。',
        "installNotesSource": 'https://github.com/Manic-EMU/ManicEMU',
        "description": (
            'Manic EMU is an all-in-one retro game emulator for iOS. It brings console,'
            "\n\n上游项目：https://github.com/Manic-EMU/ManicEMU"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'youshen2/MeloX',
        "asset": lambda n: re.match('^MeloX\\-iOS\\-unsigned\\.ipa$', n) is not None,
        "name": 'MeloX',
        "developerName": 'youshen2',
        "subtitle": '影音娱乐 · 上游 youshen2',
        "category": 'entertainment',
        "tintColor": '#DA7752',
        "screenshots": ['https://raw.githubusercontent.com/youshen2/MeloX/main/docs/screenshots/0.png', 'https://raw.githubusercontent.com/youshen2/MeloX/main/docs/screenshots/1.png', 'https://raw.githubusercontent.com/youshen2/MeloX/main/docs/screenshots/10.png'],
        "description": (
            '面向 iPhone、iPad、Mac 与 Apple Watch，使用原生 SwiftUI 构建的第三方网易云音乐播放器'
            "\n\n上游项目：https://github.com/youshen2/MeloX"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'ResistanceTo/MiniWatts',
        "asset": lambda n: re.match('^MiniWatts\\-unsigned\\.ipa$', n) is not None,
        "name": 'MiniWatts',
        "developerName": 'ResistanceTo',
        "subtitle": '阅读 · 上游 ResistanceTo',
        "category": 'books',
        "tintColor": '#9C3CC8',
        "iconURL": 'https://raw.githubusercontent.com/ResistanceTo/MiniWatts/master/docs/icon.png',
        "screenshots": ['https://raw.githubusercontent.com/ResistanceTo/MiniWatts/master/docs/screenshots/history.jpg', 'https://raw.githubusercontent.com/ResistanceTo/MiniWatts/master/docs/screenshots/power.jpg', 'https://raw.githubusercontent.com/ResistanceTo/MiniWatts/master/docs/screenshots/thermal.jpg'],
        "installNotes": '使用私有 API，只能侧载、无法上架；免费 Apple ID 可用。放进 LiveContainer 时无法运行 App Extension，widget 会消失。',
        "installNotesSource": 'https://github.com/ResistanceTo/MiniWatts',
        "description": (
            "An iPhone and iPad battery and charging monitor built on Apple's private APIs. It reads the"
            "\n\n上游项目：https://github.com/ResistanceTo/MiniWatts"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'mornyeapp/Mornye',
        "asset": lambda n: re.match('^Mornye\\-v[0-9A-Za-z._+-]+\\-ios\\-unsigned\\.ipa$', n) is not None,
        "name": 'Mornye',
        "developerName": 'mornyeapp',
        "subtitle": '实用工具 · 上游 mornyeapp',
        "category": 'utilities',
        "tintColor": '#CC385D',
        "iconURL": 'https://raw.githubusercontent.com/mornyeapp/Mornye/main/icon.png',
        "screenshots": ['https://raw.githubusercontent.com/mornyeapp/Mornye/main/assets/readme/showcase-dark.png', 'https://raw.githubusercontent.com/mornyeapp/Mornye/main/assets/readme/showcase-light.png'],
        "description": (
            'Full-screen cover art, a detailed audio quality label, queue'
            "\n\n上游项目：https://github.com/mornyeapp/Mornye"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'jxxghp/MoviePilot-App',
        "asset": lambda n: re.match('^MoviePilot\\-[0-9A-Za-z._+-]+\\-unsigned\\.ipa$', n) is not None,
        "name": 'MoviePilot',
        "developerName": 'jxxghp',
        "subtitle": '影音娱乐 · 上游 jxxghp',
        "category": 'entertainment',
        "tintColor": '#46DDCE',
        "screenshots": ['https://raw.githubusercontent.com/jxxghp/MoviePilot-App/main/screenshots/all-pages.png', 'https://raw.githubusercontent.com/jxxghp/MoviePilot-App/main/screenshots/menus-and-dialogs.png', 'https://raw.githubusercontent.com/jxxghp/MoviePilot-App/main/screenshots/screens/01.png'],
        "description": (
            'MoviePilot 的 iOS 客户端。使用系统原生导航、搜索和快捷面板，业务页面、弹窗内容和插件界面继续复用 MoviePilot-Frontend。'
            "\n\n上游项目：https://github.com/jxxghp/MoviePilot-App"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'singleton-altman/MoviePilotLite',
        "asset": lambda n: re.match('^ios\\-v[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'MoviePilotLite',
        "developerName": 'singleton-altman',
        "subtitle": '影音娱乐 · 上游 singleton-altman',
        "category": 'entertainment',
        "tintColor": '#6030D9',
        "iconURL": 'https://raw.githubusercontent.com/singleton-altman/MoviePilotLite/master/assets/icon.png',
        "description": (
            '基于 MoviePilot 的 Flutter 跨端客户端，对接 MoviePilot v2 API，在手机上完成订阅、搜索、下载、整理与系统运维等常用操作。'
            "\n\n上游项目：https://github.com/singleton-altman/MoviePilotLite"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'dddevid/Musly',
        "asset": lambda n: re.match('^musly\\-ios\\.ipa$', n) is not None,
        "name": 'Musly',
        "developerName": 'dddevid',
        "subtitle": '影音娱乐 · 上游 dddevid',
        "category": 'entertainment',
        "tintColor": '#AD40CE',
        "iconURL": 'https://raw.githubusercontent.com/dddevid/Musly/master/android/fastlane/metadata/android/en-US/images/icon.png',
        "description": (
            'A free, cross-platform music player and streaming client for self-hosted libraries, web streams, and local audio files'
            "\n\n上游项目：https://github.com/dddevid/Musly"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'verback2308/Opaline',
        "asset": lambda n: re.match('^Opaline_[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'Opaline',
        "developerName": 'verback2308',
        "subtitle": '影音娱乐 · 上游 verback2308',
        "category": 'entertainment',
        "tintColor": '#694ECA',
        "iconURL": 'https://raw.githubusercontent.com/verback2308/Opaline/main/Opaline/AltIcons/AppIconClearDark%402x.png',
        "screenshots": ['https://raw.githubusercontent.com/verback2308/Opaline/main/screenshots/app/ipad/dark/channel.jpeg', 'https://raw.githubusercontent.com/verback2308/Opaline/main/screenshots/app/ipad/dark/player.jpeg', 'https://raw.githubusercontent.com/verback2308/Opaline/main/screenshots/app/ipad/dark/recommendations.jpeg'],
        "description": (
            'A lightweight, native YouTube client for iOS 12+. No ads, no tracking, no dependencies'
            "\n\n上游项目：https://github.com/verback2308/Opaline"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'hugeBlack/OpenParsec',
        "asset": lambda n: re.match('^OpenParsec\\.ipa$', n) is not None,
        "name": 'OpenParsec',
        "developerName": 'hugeBlack',
        "subtitle": '实用工具 · 上游 hugeBlack',
        "category": 'utilities',
        "tintColor": '#CC6C38',
        "description": (
            'OpenParsec is a simple, open-source Parsec client for iOS/iPadOS written in Swift using the SwiftUI framework and the Parsec SDK'
            "\n\n上游项目：https://github.com/hugeBlack/OpenParsec"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'MakrSas/orchard-ios',
        "asset": lambda n: re.match('^Orchard\\.ipa$', n) is not None,
        "name": 'Orchard',
        "developerName": 'MakrSas',
        "subtitle": '实用工具 · 上游 MakrSas',
        "category": 'utilities',
        "tintColor": '#CD379B',
        "installNotes": '需 JIT（StikDebug 附加调试器）且签名工具必须加上 Increased Memory Limit capability；上游实测无该能力时 iOS 在约 3 GB 就会杀掉进程。',
        "installNotesSource": 'https://github.com/MakrSas/orchard-ios',
        "description": (
            'Apple Silicon macOS, running inside an iPhone app'
            "\n\n上游项目：https://github.com/MakrSas/orchard-ios"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'bggRGjQaUbCoE/PiliPlus',
        "asset": lambda n: re.match('^PiliPlus_ios_[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'PiliPlus',
        "developerName": 'bggRGjQaUbCoE',
        "subtitle": '影音娱乐 · 上游 bggRGjQaUbCoE',
        "category": 'entertainment',
        "tintColor": '#2833CC',
        "screenshots": ['https://raw.githubusercontent.com/bggRGjQaUbCoE/PiliPlus/main/assets/screenshots/174shots_so.png', 'https://raw.githubusercontent.com/bggRGjQaUbCoE/PiliPlus/main/assets/screenshots/510shots_so.png', 'https://raw.githubusercontent.com/bggRGjQaUbCoE/PiliPlus/main/assets/screenshots/850shots_so.png'],
        "description": (
            '可以从 Releases 下载，或克隆仓库拉取代码后在本地编译。'
            "\n\n上游项目：https://github.com/bggRGjQaUbCoE/PiliPlus"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Eslzzyl/Pixiv-SwiftUI',
        "asset": lambda n: re.match('^Pixiv\\-SwiftUI\\.ipa$', n) is not None,
        "name": 'Pixiv-SwiftUI',
        "developerName": 'Eslzzyl',
        "subtitle": '阅读 · 上游 Eslzzyl',
        "category": 'books',
        "tintColor": '#C43695',
        "iconURL": 'https://raw.githubusercontent.com/Eslzzyl/Pixiv-SwiftUI/master/Pixiv-SwiftUI/AppIcon.icon/Assets/AppIcon_1024%202.png',
        "description": (
            '项目同时支持 iOS、iPadOS 和 macOS。'
            "\n\n上游项目：https://github.com/Eslzzyl/Pixiv-SwiftUI"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'playportdev/playport',
        "asset": lambda n: re.match('^Playport\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'Playport',
        "developerName": 'playportdev',
        "subtitle": '影音娱乐 · 上游 playportdev',
        "category": 'entertainment',
        "tintColor": '#4D66D5',
        "iconURL": 'https://raw.githubusercontent.com/playportdev/playport/main/app/Icon/AppIcon-dev.png',
        "screenshots": ['https://raw.githubusercontent.com/playportdev/playport/main/site/screenshots/downloads.webp', 'https://raw.githubusercontent.com/playportdev/playport/main/site/screenshots/game-page.webp', 'https://raw.githubusercontent.com/playportdev/playport/main/site/screenshots/hollow-knight.webp'],
        "installNotes": '一次性配对后可用内置 JIT helper，也可由 StikDebug / LiveContainer 提供 JIT；IPA 为 ad hoc 签名（无证书）并请求 Increased Memory Limit。安装时若签名工具询问是否保留 App Extension，请选择保留（JIT helper 依赖它）。',
        "installNotesSource": 'https://github.com/playportdev/playport',
        "description": (
            'PC games on your iPhone. Natively, no streaming'
            "\n\n上游项目：https://github.com/playportdev/playport"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'xmiguel911x/PSX3IOS',
        "asset": lambda n: re.match('^PSX3IOS\\-beta\\.[0-9A-Za-z._+-]+\\-unsigned\\.ipa$', n) is not None,
        # 该 repo 的 release 全部是 prerelease，只能把预发布当稳定轨道。
        "prereleaseAsStable": True,
        "name": 'PSX3IOS',
        "developerName": 'xmiguel911x',
        "subtitle": '影音娱乐 · 上游 xmiguel911x',
        "category": 'entertainment',
        "tintColor": '#BCC62F',
        "installNotes": 'PS3 模拟器，有/无 JIT 都能跑，但上游推荐开 JIT 以获得可用性能。侧载版需 StikDebug + LocalDevVPN 启用 JIT；另有 TrollStore .tipa 变体（iOS 15–17.0）。',
        "installNotesSource": 'https://github.com/xmiguel911x/PSX3IOS',
        "description": (
            'Status: beta 0.5. Real games boot and play. This is not a'
            "\n\n上游项目：https://github.com/xmiguel911x/PSX3IOS"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'liuchuancong/pure_live',
        "asset": lambda n: re.match('^PureLive\\-[0-9A-Za-z._+-]+\\-ios\\-arm64\\-trollstore\\.ipa$', n) is not None,
        "name": 'PureLive',
        "developerName": 'liuchuancong',
        "subtitle": '影音娱乐 · 上游 liuchuancong',
        "category": 'entertainment',
        "tintColor": '#A8D02F',
        "iconURL": 'https://raw.githubusercontent.com/liuchuancong/pure_live/master/assets/icons/icon.png',
        "description": (
            'A third-party live stream aggregator built with Flutter'
            "\n\n上游项目：https://github.com/liuchuancong/pure_live"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'TarbleFR/RewindBox',
        "asset": lambda n: re.match('^RewindBox\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'RewindBox',
        "developerName": 'TarbleFR',
        "subtitle": '影音娱乐 · 上游 TarbleFR',
        "category": 'entertainment',
        "tintColor": '#456DC9',
        "iconURL": 'https://raw.githubusercontent.com/TarbleFR/RewindBox/main/tools/neoplay-receiver/neoplay-icon.png',
        "screenshots": ['https://raw.githubusercontent.com/TarbleFR/RewindBox/main/assets/readme/neostation-ios-preview.png', 'https://raw.githubusercontent.com/TarbleFR/RewindBox/main/assets/readme/rewindbox-preview.png', 'https://raw.githubusercontent.com/TarbleFR/RewindBox/main/assets/system_art/rewindbox-glacier/preview.webp'],
        "installNotes": '内嵌 MeloNX 等运行时，需 StikJIT 且上游明确「不支持 LiveContainer」。IPA 里的 entitlement 声明本身不等于已获授权，仍需签名/描述文件配合。',
        "installNotesSource": 'https://github.com/TarbleFR/RewindBox',
        "description": (
            'Download 0.0.11 · Build 721 · IPA download · SideStore / AltStore source · Credits and licenses'
            "\n\n上游项目：https://github.com/TarbleFR/RewindBox"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'seanhowarthdev/Roam-Control',
        "asset": lambda n: re.match('^RoamControl\\-[0-9A-Za-z._+-]+\\-Build105\\.ipa$', n) is not None,
        "name": 'Roam Control',
        "developerName": 'seanhowarthdev',
        "subtitle": '实用工具 · 上游 seanhowarthdev',
        "category": 'utilities',
        "tintColor": '#6335C0',
        "iconURL": 'https://raw.githubusercontent.com/seanhowarthdev/Roam-Control/main/Documentation/Images/RoamControl-AppIcon-v2-source.png',
        "screenshots": ['https://raw.githubusercontent.com/seanhowarthdev/Roam-Control/main/Documentation/Images/README/roam-walking-preview.png'],
        "installNotes": '放进 LiveContainer 时，必须在首次运行前打开 Fix Local Notifications，否则配对通知无法送达。',
        "installNotesSource": 'https://github.com/seanhowarthdev/Roam-Control',
        "description": (
            "Choose, test and move an iPhone's reported location from one clean Apple Maps interface"
            "\n\n上游项目：https://github.com/seanhowarthdev/Roam-Control"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'ekomlenovic/rush_hour_ios_android',
        "asset": lambda n: re.match('^rush\\-hours\\-unsigned\\.ipa$', n) is not None,
        "name": 'Rush Hours',
        "developerName": 'ekomlenovic',
        "subtitle": '影音娱乐 · 上游 ekomlenovic',
        "category": 'entertainment',
        "tintColor": '#CAA953',
        "iconURL": 'https://raw.githubusercontent.com/ekomlenovic/rush_hour_ios_android/main/assets/icon.png',
        "screenshots": ['https://raw.githubusercontent.com/ekomlenovic/rush_hour_ios_android/main/assets/android-icon-background.png', 'https://raw.githubusercontent.com/ekomlenovic/rush_hour_ios_android/main/assets/android-icon-foreground.png'],
        "installNotes": '免费 Apple 账号的 Home Screen Widget 是独立 App Extension，会额外占 1 个 App ID（每周上限 10 个）；若 SideStore 询问是否移除扩展，想保留 widget 就选保留。超出 SideStore 3 应用限制时可用 LiveContainer 装载。',
        "installNotesSource": 'https://github.com/ekomlenovic/rush_hour_ios_android',
        "description": (
            'Version française plus bas'
            "\n\n上游项目：https://github.com/ekomlenovic/rush_hour_ios_android"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'donbytyqi/scenebox',
        "asset": lambda n: re.match('^SceneBox\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'SceneBox',
        "developerName": 'donbytyqi',
        "subtitle": '影音娱乐 · 上游 donbytyqi',
        "category": 'entertainment',
        "tintColor": '#38C244',
        "description": (
            'Torrent streaming client for iOS, iPadOS, tvOS and Mac (Catalyst), written in SwiftUI'
            "\n\n上游项目：https://github.com/donbytyqi/scenebox"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'SideStore/SideStore',
        "asset": lambda n: re.match('^SideStore\\.ipa$', n) is not None,
        "name": 'SideStore',
        "developerName": 'SideStore',
        "subtitle": '实用工具 · 上游 SideStore',
        "category": 'utilities',
        "tintColor": '#81C039',
        "installNotes": '官方上游（SideStore/SideStore），Bundle ID com.SideStore.SideStore 属实。本条目取自 0.7.0-alpha 的 SideStore.ipa，上游更新最频繁的是 nightly tag。免电脑续签依赖 LocalDevVPN（需额外 entitlements 的 App Store App）。',
        "installNotesSource": 'https://github.com/SideStore/SideStore#requirements',
        "description": (
            'SideStore is an iOS application that allows you to sideload apps onto your iOS device with just your Apple ID.…'
            "\n\n上游项目：https://github.com/SideStore/SideStore"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'akinal5765-byte/Silverphase',
        "asset": lambda n: re.match('^Silverphase\\-[0-9A-Za-z._+-]+\\-iOS\\-unsigned\\.ipa$', n) is not None,
        "name": 'Silverphase',
        "developerName": 'akinal5765-byte',
        "subtitle": '影音娱乐 · 上游 akinal5765-byte',
        "category": 'entertainment',
        "tintColor": '#5F47CD',
        "iconURL": 'https://raw.githubusercontent.com/akinal5765-byte/Silverphase/main/screenshots/app-icon.png',
        "installNotes": '真机描述文件需包含项目请求的 Increased Memory Limit 能力；模拟器构建不需开发者签名。',
        "installNotesSource": 'https://github.com/akinal5765-byte/Silverphase',
        "description": (
            '面向 macOS、iPhone 与 iPad 的原生胶片工艺模拟器'
            "\n\n上游项目：https://github.com/akinal5765-byte/Silverphase"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'StikDebug/StikDebug',
        "asset": lambda n: re.match('^StikDebug\\-[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'StikDebug',
        "developerName": 'StikDebug',
        "subtitle": '实用工具 · 上游 StikDebug',
        "category": 'utilities',
        "tintColor": '#CD5B65',
        "screenshots": ['https://raw.githubusercontent.com/StikDebug/StikDebug/main/assets/StikDebug_26.icon/Assets/STIKCOIN-10-removebg-preview.png', 'https://raw.githubusercontent.com/StikDebug/StikDebug/main/assets/StikDebug_26.icon/Assets/STIKCOIN-8-removebg-preview.png'],
        "installNotes": 'iOS 17.4+ 的机内调试器 / JIT 启用器，为带 get-task-allow entitlement 的侧载 App 打开 JIT。本应用是前面多个模拟器的前置依赖，不是独立游戏。',
        "installNotesSource": 'https://github.com/StikDebug/StikDebug',
        "description": (
            'See Officially Supported Apps for the apps supported by the StikDebug team and their bundled scripts'
            "\n\n上游项目：https://github.com/StikDebug/StikDebug"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'infinityf4p/TiebaPure-iOS',
        "asset": lambda n: re.match('^TiebaPure\\-v[0-9A-Za-z._+-]+\\-unsigned\\.ipa$', n) is not None,
        "name": 'TiebaPure',
        "developerName": 'infinityf4p',
        "subtitle": '影音娱乐 · 上游 infinityf4p',
        "category": 'entertainment',
        "tintColor": '#4757D1',
        "screenshots": ['https://raw.githubusercontent.com/infinityf4p/TiebaPure-iOS/main/docs/images/home-light.png', 'https://raw.githubusercontent.com/infinityf4p/TiebaPure-iOS/main/docs/images/search-light.png', 'https://raw.githubusercontent.com/infinityf4p/TiebaPure-iOS/main/docs/images/thread-guest-light.png'],
        "description": (
            '基于 SwiftUI 的第三方百度贴吧客户端，支持 iOS 16.4 及更高版本。'
            "\n\n上游项目：https://github.com/infinityf4p/TiebaPure-iOS"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'Suwayomi/Suwayomi-Tsumiru',
        "asset": lambda n: re.match('^tsumiru\\-v[0-9A-Za-z._+-]+\\-ios\\.ipa$', n) is not None,
        "name": 'Tsumiru',
        "developerName": 'Suwayomi',
        "subtitle": '阅读 · 上游 Suwayomi',
        "category": 'books',
        "tintColor": '#9A33D7',
        "iconURL": 'https://raw.githubusercontent.com/Suwayomi/Suwayomi-Tsumiru/main/web/icons/Icon-192.png',
        "installNotes": '构建未签名，必须侧载；上游 README 里也给出了自己的 AltStore 源地址。',
        "installNotesSource": 'https://github.com/Suwayomi/Suwayomi-Tsumiru',
        "description": (
            "Tsumiru is a client for Suwayomi-Server, so you'll need a server running first. Your library and reading progress are stored on the server, and Tsumiru reads them on Android, iOS, Linux, Windows, macOS or the web. Guides and the FAQ are at tsumiru.app"
            "\n\n上游项目：https://github.com/Suwayomi/Suwayomi-Tsumiru"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'utmapp/UTM',
        "asset": lambda n: re.match('^UTM\\.ipa$', n) is not None,
        "name": 'UTM',
        "developerName": 'utmapp',
        "subtitle": '影音娱乐 · 上游 utmapp',
        "category": 'entertainment',
        "tintColor": '#B3D256',
        "screenshots": ['https://raw.githubusercontent.com/utmapp/UTM/main/Icons/AIX.png', 'https://raw.githubusercontent.com/utmapp/UTM/main/Icons/IOS.png', 'https://raw.githubusercontent.com/utmapp/UTM/main/Icons/amigaos.png'],
        "installNotes": 'UTM/QEMU 依赖动态代码生成（JIT）达到可用性能；上游说明 iOS 上的 JIT 需要越狱或针对特定 iOS 版本的 workaround。UTM SE（slow edition）用线程解释器，不需要 JIT。',
        "installNotesSource": 'https://github.com/utmapp/UTM#install',
        "description": (
            'UTM is a full featured system emulator and virtual machine host for iOS, macOS, and visionOS. It is based off of QEMU. In short, it allows you to run Windows, Linux, and more on your Mac, iPhone, and iPad.…'
            "\n\n上游项目：https://github.com/utmapp/UTM"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'mrdrvt99/YouProEXTRA',
        "asset": lambda n: re.match('^YouProExtra_[0-9A-Za-z._+-]+\\.ipa$', n) is not None,
        "name": 'YouProEXTRA',
        "developerName": 'mrdrvt99',
        "subtitle": '影音娱乐 · 上游 mrdrvt99',
        "category": 'entertainment',
        "tintColor": '#36D9AD',
        "installNotes": 'YouTube 改包（YTLite/YouPro），故意使用官方 YouTube 的 Bundle ID com.google.ios.youtube；安装前须先卸载设备上同 ID 的 App，否则上游提示不要直接点 Update，应先删除再全新安装。上游另有自己的官方源 mrdrvt99/Altstore-Repository。README 说明自制构建需自备解密 IPA（作者因法律原因不提供）。',
        "installNotesSource": 'https://github.com/mrdrvt99/YouProEXTRA#main-features',
        "description": (
            'YouTube IPA builder packed with customizable tweaks. Also Known as Youtubemaxxing'
            "\n\n上游项目：https://github.com/mrdrvt99/YouProEXTRA"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
    {
        "repo": 'huamurui/zhihu-minus-minus',
        "asset": lambda n: re.match('^zhihu\\-minus\\-minus\\-v[0-9A-Za-z._+-]+\\-unsigned\\.ipa$', n) is not None,
        "name": 'ZhihuMinusMinus',
        "developerName": 'huamurui',
        "subtitle": '影音娱乐 · 上游 huamurui',
        "category": 'entertainment',
        "tintColor": '#42D142',
        "screenshots": ['https://raw.githubusercontent.com/huamurui/zhihu-minus-minus/main/docs/screenshot/v0.0.2/photo_10_2026-03-09_01-45-47.jpg', 'https://raw.githubusercontent.com/huamurui/zhihu-minus-minus/main/docs/screenshot/v0.0.2/photo_11_2026-03-09_01-45-47.jpg', 'https://raw.githubusercontent.com/huamurui/zhihu-minus-minus/main/docs/screenshot/v0.0.2/photo_12_2026-03-09_01-45-47.jpg'],
        "description": (
            '一款轻量、无广告的第三方知乎客户端，支持 Android 与 iOS。'
            "\n\n上游项目：https://github.com/huamurui/zhihu-minus-minus"
            "\nIPA 直连该项目 GitHub Release 官方资产，需自行签名安装。"
        ),
    },
]
