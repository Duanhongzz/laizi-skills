# 剑网三主播赖子蒸馏skills

[框架] 一套基于既有角色规则、直播文字转录与研究笔记整理的中文角色技能，用于赖子视角聊天、口吻模拟和对白创作。

[已知] 当前仓库收录可独立使用的技能包及检索工具。原聊天网站、语音服务、用户数据库、认证文件和大体积音视频素材没有打包进来。

## 使用

将 `skills/laizi-perspective` 整个目录放入所用工具的技能目录，保留里面的参考资料和脚本。技能入口是 [SKILL.md](skills/laizi-perspective/SKILL.md)，不是长篇资料存档。

可以这样提出请求：

> 用赖子视角回复这句话，控制在三句以内。

> 用赛博赖子的口吻写一段游戏失败后的对白，明确这是模拟对白。

> 查一下某个人物在现有资料中的记录，区分资料记载和无法确认的部分。

## 内容

| 位置 | 用途 |
|---|---|
| [技能入口](skills/laizi-perspective/SKILL.md) | 角色使用方式、资料路由和事实边界 |
| [完整角色资料](skills/laizi-perspective/references/persona.md) | 原有角色长文与场景示例 |
| [资料索引](skills/laizi-perspective/references/source-index.md) | 编年史、人物关系、来源笔记与转录说明 |
| `skills/laizi-perspective/laizi_corpus.json` | 1,471 条既有检索语料 |
| `skills/laizi-perspective/references/sources/transcripts/` | 75 份文字转录 |
| `skills/laizi-perspective/scripts/` | 便携检索、重建工具及回归检查 |
| [来源清单](source-provenance.json) | 当前文件与校验值 |
| [完整性清单](package-manifest.json) | 当前文件集、大小及校验值 |

## 本地检索

需要 Python 3.10 或以上。中文及别名检索使用标准库即可；需要拼音召回时安装可选依赖。

```bash
python -m pip install -r skills/laizi-perspective/requirements.txt
python skills/laizi-perspective/scripts/search_corpus.py "双塘是谁" --top-k 3
```

[已知] 脚本使用自身位置定位资料，可以从其他工作目录启动。检索结果保留来源；相关度分数不代表真实性。

## 检查与维护

在仓库目录运行以下只读检查：

```bash
python scripts/validate_package.py
python skills/laizi-perspective/scripts/build_corpus.py --test
python skills/laizi-perspective/scripts/test_search_regression.py
```

需要重建语料时，先检查已有修改，再执行：

```bash
python skills/laizi-perspective/scripts/build_corpus.py --build --patch-manual --test
python scripts/validate_package.py --update-manifest
```

[已知] 重建命令会修改语料文件，默认检索和测试不会写回语料。维护后应检查差异并更新完整性清单。拼音依赖缺失时，回归脚本会明确跳过仅拼音输入的用例。

## 资料口径

[已知] 这是既有资料的整理发布，并未重新核验全部历史说法。长文中的个人评价、模拟对白和旧统计保留为来源内容；不能把它们当作已核实的现实事实或真实原话。实际用户要求和事实核查优先于角色设定。

[已知] 本次整理包括：补齐标准技能入口、拆出完整角色资料、保留文字来源、修复本机绝对路径、提供检索命令与文件完整性检查。
