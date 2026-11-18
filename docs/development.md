# 本地运行与目录结构

## 目录结构

```
apps.json                                    # 源文件本体，客户端消费的就是它
.github/workflows/update-source.yml          # 定时更新流水线
.github/dependabot.yml                       # 只盯 github-actions 的版本（本仓库没有别的依赖）
tools/build_source.py                        # 生成脚本（抓 GitHub Release + 探测 IPA 元数据）
tools/verify_source.py                       # 结构校验，提交前的守门人
tools/simulate_client.py                     # 模拟两个客户端的解析，回答「改完到底看不看得见」
tools/render_docs.py                         # 按 apps.json 刷新 README 清单、追加 Changelog
docs/                                        # 拆分后的说明文档
docs/Changelog.md                            # 更新记录（自动维护）
cache/releases.json                          # 各仓库的 Release 列表缓存
cache/probes.json                            # IPA 元数据缓存（绑定资产 ID、更新时间、大小和 digest）
cache/icons.json                             # 图标可达性缓存
```

## 参数

```bash
python tools/build_source.py                 # 用缓存，联网最少
python tools/build_source.py --refresh       # 重新抓 Release 列表
python tools/build_source.py --reprobe       # 连 IPA 元数据也重探（一般不需要）
python tools/build_source.py --versions 4    # 稳定版轨道保留最近 4 个（便于回退）
```

## 文档生成

```bash
python tools/render_docs.py                  # 刷新 README 清单；有版本变化时追加 docs/Changelog.md
python tools/render_docs.py --no-changelog   # 只刷新清单，不写更新记录
```

README 里的应用清单夹在 `<!-- apps:begin -->` 和 `<!-- apps:end -->` 之间，由脚本整体替换；
`docs/Changelog.md` 的记录插在 `<!-- changelog:begin -->` 之后，最新的在最上面。
两处都不要手工改，改了下一轮会被覆盖。

## 测试

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s .github/scripts
```
