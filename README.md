# 赖子视角（laizi-perspective）

剑网三主播赖子的中文角色技能包。内容基于既有角色设定、直播文字转录和研究笔记整理而成，可用于赖子视角聊天、口吻模拟和对白创作。

> 本项目为爱好者整理的非官方资料，与主播本人及其团队无关。模拟对白不代表本人真实言论。

## 包含与不包含

本仓库包含可独立使用的技能包和本地检索工具。

原聊天网站、语音服务、用户数据库、认证文件和大体积音视频素材**不在**本仓库中。

## 快速开始

将 `skills/laizi-perspective` 整个目录复制到你所用工具的技能目录下，并保留其中的参考资料和脚本。

技能入口是 `SKILL.md`，它负责调度资料，本身不是长篇资料存档。

### 请求示例

- 用赖子视角回复这句话，控制在三句以内。
- 用赛博赖子的口吻写一段游戏失败后的对白，并注明这是模拟对白。
- 查一下某个人物在现有资料中的记录，区分有资料记载的部分和无法确认的部分。

## 目录结构

| 位置 | 用途 |
| --- | --- |
| `skills/laizi-perspective/SKILL.md` | 技能入口：使用方式、资料路由和事实边界 |
| 完整角色资料 | 原有角色长文与场景示例 |
| 资料索引 | 编年史、人物关系、来源笔记与转录说明 |
| `skills/laizi-perspective/laizi_corpus.json` | 1,471 条检索语料 |
| `skills/laizi-perspective/references/sources/transcripts/` | 75 份直播文字转录 |
| `skills/laizi-perspective/scripts/` | 检索、重建工具及回归测试 |
| 来源清单 | 当前文件来源与校验值 |
| 完整性清单 | 当前文件集、大小及校验值 |

## 本地检索

需要 Python 3.10 或更高版本。中文和别名检索只依赖标准库；如需拼音召回，再安装可选依赖：

```bash
python -m pip install -r skills/laizi-perspective/requirements.txt
python skills/laizi-perspective/scripts/search_corpus.py "双塘是谁" --top-k 3
```

脚本根据自身所在位置定位资料，可以从任意工作目录运行。检索结果会保留来源；相关度分数只反映匹配程度，不代表内容真实性。

## 检查与维护

在仓库根目录运行以下只读检查：

```bash
python scripts/validate_package.py
python skills/laizi-perspective/scripts/build_corpus.py --test
python skills/laizi-perspective/scripts/test_search_regression.py
```

如需重建语料，请先确认工作区没有未处理的修改，再执行：

```bash
python skills/laizi-perspective/scripts/build_corpus.py --build --patch-manual --test
python scripts/validate_package.py --update-manifest
```

注意事项：

- 只有重建命令会修改语料文件，默认的检索和测试不会写回。
- 维护完成后，请检查差异并更新完整性清单。
- 未安装拼音依赖时，回归测试会明确跳过仅含拼音输入的用例。

## 资料说明

本仓库是对既有资料的整理发布，没有重新核验全部历史说法。长文中的个人评价、模拟对白和旧统计数据按来源原样保留，不应视为已核实的事实或本人原话。使用时，用户的实际要求和事实核查优先于角色设定。

本次整理内容：

- 补齐标准技能入口 `SKILL.md`
- 拆分出完整角色资料
- 保留文字来源
- 修复本机绝对路径
- 提供检索命令与文件完整性检查
