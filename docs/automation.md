# 自动更新

`.github/workflows/update-source.yml` **每小时**检查一次上游（在每小时的第 7 分钟运行）。也可以随时手动触发：Actions → 更新 SideStore 源 → Run workflow。

> ⚠️ GitHub 的定时任务是 **best-effort**，不是保证：实测会迟到几分钟，负载高时还会直接丢掉这一轮，而且**频率越高丢得越多**（对照实测：每天一次 100% 准点、每小时基本不漏、10 分钟粒度只跑到约一半）。
> 丢一轮不影响结果——下一轮会补上，所以实际延迟通常 15~40 分钟，偶发更长。
> 另：**新建的工作流，cron 要先被 GitHub「认领」**。本仓库实测：cron 变更后 **4 小时 48 分**才跑出第一次定时；推一个默认分支上的提交能有效催熟。这期间配置是对的，**别反复改表达式 —— 每改一次，认领倒计时就重置一次**。

每轮做的事：

```
检查上游 Release（--refresh） → 重新生成 apps.json → verify_source.py 结构校验
  → 有变更才提交到本仓库 → 发布/滚动更新 Release → 同步产物到 cnb.cool
```

- 单次实测约 **12 秒**，公开仓库的 Actions 分钟数免费不限量
- 只在检测到真实变更时才产生提交，没有新版本就不动
- Releases 页那个 `latest` 是**固定 tag 滚动覆盖**的：只在内容变化时重传，永远只留**一个** release。之所以不做成「一次更新一个 tag」，是因为这条流水线每小时跑一轮 —— 那样一天就是 24 个 tag
- **校验不通过就不提交**：宁可这轮不动，也不把一个结构坏掉的源推上去（某个 app 的 `releases` 变成空数组时，SideStore 会整体解码失败、整个源都加载不了）
- 某个仓库抓取失败时会**沿用上一次生成的数据**，不会把那个应用从源里抹掉
- 同步到 cnb.cool 需要仓库里配好 `CNB_TOKEN` 与 `CNB_USER` 两个 Secrets；没配就自动跳过，只更新本仓库
- 有变化时同时刷新 README 的应用清单，并把这一轮的版本变化追加到 [Changelog.md](Changelog.md)

## 为什么是轮询，不是「上游发版就触发」

想做到「上游一发版立刻同步」，需要在别的仓库发生 release 事件时触发本仓库的工作流。**GitHub 做不到这件事**：release 事件只在事件发生的那一个仓库里触发工作流，跨仓库收不到；官方给外部事件准备的机制是 `repository_dispatch`，但那需要上游主动往我们的 API 发请求——而给别人的仓库配 webhook，得先有那个仓库的管理权限。

所以现实可行的就是短间隔轮询。按官方文档，定时任务最短只能 5 分钟一次，且负载高时会被延迟、甚至丢弃排队中的任务（整点前后最严重，所以这里错开了整点）。对轮询来说偶尔丢一轮无所谓，下一轮会补上。

真想要「秒级」的话，工作流已经留了 `repository_dispatch` 入口（事件类型 `upstream-release`）：用 Cloudflare Workers 的 1 分钟定时之类去轮询上游 release，命中就打一次这个接口即可。

> 为什么不用 cnb.cool 自带的定时构建：CNB 免费额度只有 160 核时/月，且构建前要预冻结 5 分钟（0.08 核时），额度见底时**所有构建**都会在 Prepare 阶段失败（2026-09 就被 `laincat/Rules` 一个仓库烧光了）。GitHub 公开仓库的 Actions 分钟数免费不限量，且 runner 原生直连 GitHub Release，不需要任何镜像代理。

## 仓库自身的依赖更新（Dependabot）

这个仓库**没有任何传统依赖** —— `tools/` 下的脚本 import 全部来自 Python 标准库，仓库里也没有 `requirements.txt` / `pyproject.toml` / `package.json`。所以依赖图里**唯一**的依赖，就是流水线用的那两个 Action。

`.github/dependabot.yml` 因此只配了 `github-actions` 一个生态：每天 09:00（北京时间）检查一次，minor + patch 合并成一个 PR，**major 单独开**（这条流水线负责发布源文件，major 升级可能改行为，要单独看清再合）。

Action 已固定到完整 commit SHA（保留版本注释）；Dependabot 每日提出更新，patch/minor 仅在对应提交验证通过后自动合并，major 单独审核。生成与发布前会在同一 checkout 上执行离线回归测试、结构校验和客户端模拟。

## 网络与缓存安全

- 所有 HTTPS 使用系统 CA 与主机名校验；不修改全局 SSL 上下文，不回退公共 GitHub 代理。
- GitHub token 仅发送到 `https://api.github.com`；携带认证的请求拒绝全部重定向，普通资源禁止降级 HTTP。
- IPA Range 必须返回精确的 206、Content-Range 和响应长度；单次最多 8 MiB，IPA 总长上限 8 GiB，Info.plist 压缩与展开均最多 2 MiB。ZIP64、多卷 ZIP、不支持的压缩算法和损坏 CRC 会失败并保留上一版条目。
- IPA 探测缓存绑定资产 ID、updated_at、size、digest；旧的仅 URL 缓存会重新探测。`--refresh` 重新抓取发布和资产身份；`--reprobe` 强制探测。缺少资产身份时不永久缓存。
- 完整发布时间用于排序，再按版本和构建号确定顺序；BETA 标记按完整发布身份判断，不能只比较版本号。
- 如果曾在旧脚本中使用 GitHub token 且触发公共代理回退，应自行检查相关 token 的历史使用与撤销需求。本次代码修复不更改凭据或账号设置。

离线测试：`python -m unittest discover -s tests -v`，再运行 `.github/scripts` 的合并门禁测试。测试使用模拟网络和虚拟 token，不访问真实凭据。

## 手动更新

```bash
# 本地跑（需要 Python 3.8+，只用标准库）
python tools/build_source.py --refresh      # 重新抓上游
python tools/verify_source.py --min-apps 27  # 校验（数字取「等于当前应用数」）
python tools/render_docs.py                  # 刷新 README 清单并记录 Changelog
```
