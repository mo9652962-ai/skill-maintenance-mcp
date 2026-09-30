# skill-maintenance-mcp

<!-- mcp-name: io.github.mo9652962-ai/skill-maintenance-mcp -->

技能库维护 MCP server：把 [skill-evolution] 技能的**机械环节**（备份 / 损坏扫描 / 决策日志 / 体检）固化成 5 个 MCP 工具，供任意 MCP 客户端调用。蒸馏、修剪等**判断力环节仍在技能侧**，本仓库只负责不会走样、不该被跳过的部分。

## 背景

skill-evolution 技能沉淀了一套技能维护方法论：修订前必备份、写入后必损坏扫描、决策留痕、定期体检。这些环节本身没有难度，难的是**每次都不跳步**。把它们固化成 MCP 工具之后：

- agent 修订技能时的机械动作变成工具调用，不再依赖 prompt 纪律；
- 铁律由工具语义兜底（如同日同名备份拒绝覆盖，防止快照语义被静默破坏）；
- 决策记录格式统一为四字段，未来 agent 修订前先读历史，不重复踩坑。

对应 skill-evolution 五步闭环：

| 工具 | 对应环节 | 一句话说明 |
|:---|:---|:---|
| `skill_backup` | §7 改前备份 | cp 技能目录到 `~/.agents/skill-backups/<今天>/`；同日同名拒绝覆盖 |
| `skill_scan_corruption` | §7 损坏扫描（铁律） | formfeed(`\x0c`) / 真 tab / 行中 CR——JSON 序列化转义被解释的隐性损坏；CRLF 行尾不误报 |
| `skill_log_decision` | §2 决策历史 | 四字段（诊断/修订/证据/结果）追加 `references/decision-log.md`，字段缺失拒绝 |
| `skill_read_decisions` | §2 | 条目标题列表，修订前先看防重复踩坑 |
| `skill_validate` | §3/§4 体检 | frontmatter 必填 + 损坏扫描 + 孤儿 reference（未挂链=不可发现）+ decision-log 概要 |

## 快速开始

无需克隆仓库，uvx 直接运行（入口名 `skill-maintenance-mcp`，见 pyproject 的 `[project.scripts]`）：

```bash
uvx skill-maintenance-mcp
```

ZCode 客户端注册（`~/.zcode/cli/config.json` → `mcp.servers`）：

```json
{
  "mcp": {
    "servers": {
      "skill-maintenance": {
        "command": "uvx",
        "args": ["skill-maintenance-mcp"]
      }
    }
  }
}
```

从源码开发安装：

```bash
git clone https://github.com/mo9652962-ai/skill-maintenance-mcp
cd skill-maintenance-mcp
uv venv && uv pip install -e ".[dev]"
uv run pytest -q    # 18 例；含对真实技能库的只读联动测试（无技能库环境自动 skip）
```

## 工具详解

以下参数表与 `src/skill_maintenance_mcp/server.py` 的实际工具签名一一核对，非文档虚构。「必填」指 MCP 调用时无默认值的参数。

### skill_backup — 改前备份

把技能目录备份到 `<backup_root>/<今天>/`（skill-evolution 铁律：修订前必备份）。同日同名已存在时**拒绝覆盖**，如需重备份先手动挪走第一份。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| `skill_names` | `list[str]` | 是 | — | 技能目录名列表（如 `["esq-question-bank-import"]`） |
| `skills_root` | `str` | 否 | `C:/Users/31954/.agents/skills` | 技能库根目录（默认值为作者本机路径，跨机器部署建议显式传入） |
| `backup_root` | `str \| None` | 否 | `None` → `~/.agents/skill-backups` | 备份目标根 |

返回 `{ok, backup_root, backed_up, errors}`；`ok=false` 时 `errors` 内含逐技能原因（目录不存在 / 今日已有同名备份）。

### skill_scan_corruption — 损坏扫描（铁律）

检测内容经 JSON 序列化写入时转义序列被解释造成的隐性损坏：formfeed(`\x0c`)、真 tab、行中 CR（CRLF 行尾的 `\r` 不算）。每次写入/修订技能文件后必跑（见下方铁律）。目录会按技能结构（`SKILL.md`、`references/`、`templates/`、`scripts/`、`*.md`）展开扫描。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| `paths` | `list[str]` | 是 | — | 文件或技能目录列表 |
| `skills_root` | `str \| None` | 否 | `None` | 传入相对路径时的根目录 |

返回 `{files_scanned, clean, issues}`；每个 issue 为 `{file, line, kind, snippet}`，`kind` ∈ `formfeed` / `tab` / `mid-line-cr`。`clean=false` 时按行号做**字节级修复**（参照 skill-evolution §7，工具只定位，不自动改）。

### skill_log_decision — 追加决策记录

向 `<skill_path>/references/decision-log.md` 追加一条决策记录（无则创建含 `# 决策日志` 表头）。四字段缺失会**拒绝**——空壳决策不如不记。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| `skill_path` | `str` | 是 | — | 技能目录绝对路径 |
| `title` | `str` | 是 | — | 一句话标题（自动加 `YYYY-MM-DD` 日期前缀） |
| `diagnosis` | `str` | 是 | — | 诊断——技能在什么场景失效 |
| `revision` | `str` | 是 | — | 修订——改了哪里 |
| `evidence` | `str` | 是 | — | 证据——评估/实测结果 |
| `result` | `str` | 是 | — | 结果——接受/拒绝 + 原因 |

成功返回 `{ok: true, log_path, date, title}`；字段缺失返回 `{ok: false, errors}` 并指明缺哪些。

### skill_read_decisions — 读取决策历史

读取 decision-log 概要（条目标题列表）。**修订前先读**，避免重复踩坑或推翻已有共识。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| `skill_path` | `str` | 是 | — | 技能目录绝对路径 |

返回 `{exists, entries, log_path?}`；`entries` 为各条目的 `## 日期 — 标题` 行内容，日志不存在时 `{exists: false, entries: []}`。

### skill_validate — 技能体检

一键体检：frontmatter 必填项（`name` / `description` / `version`）+ 损坏扫描 + 孤儿 reference（`references/` 下的 .md 未在 SKILL.md 正文出现文件名 = 不可发现）+ decision-log 概要。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| `skill_path` | `str` | 是 | — | 技能目录绝对路径 |

返回 `{ok, skill, frontmatter, missing_frontmatter, orphan_references, corruption, decision_log}`；`ok` 为 false 时优先看 `missing_frontmatter` 与 `corruption.issues`。

## decision-log 四字段格式

`skill_log_decision` 写入 `references/decision-log.md` 的条目格式（记「为什么改」，让未来 agent 不重新推导）：

```markdown
## YYYY-MM-DD — 标题
- **诊断**：技能在什么场景失效
- **修订**：改了哪里
- **证据**：评估/实测结果
- **结果**：接受/拒绝 + 原因
```

## 两条铁律

1. **修订前必备份**：动任何技能文件前先 `skill_backup`；备份目录是快照语义，工具会拒绝同日同名覆盖。
2. **每次写入/修订后必跑损坏扫描**：技能文件多为 JSON 序列化落盘，转义被解释的 formfeed / 真 tab / 行中 CR 肉眼难辨，`skill_scan_corruption` 必须收尾。

## 推荐工作流（agent 修订技能时）

```
skill_backup → 修订 → skill_scan_corruption → skill_log_decision → skill_validate
```

修订前可先 `skill_read_decisions` 看历史决策。

## 设计边界

- **不做自动字节修复**：修复需要人工判断正确序列（skill-evolution §7 的修复是逐案例的），工具只定位到行号 + kind + snippet。
- **备份默认拒绝同日覆盖**：改两次时手动挪走第一份，防止快照语义被静默破坏。
- **不引 yaml 依赖**：frontmatter 用极简顶层 `key: value` 解析，覆盖技能文件的常见写法。
- 上游技能：`~/.agents/skills/skill-evolution/SKILL.md`；骨架方法见 `mcp-server-craft` 技能。

## 版本与变更

版本历史见 [CHANGELOG.md](./CHANGELOG.md)（Keep a Changelog 格式 + 语义化版本，当前 `[Unreleased]` / `[0.1.0] - 2026-09-28`）。

## License

[MIT](./LICENSE)
