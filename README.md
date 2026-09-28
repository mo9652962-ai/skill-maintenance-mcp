# skill-maintenance-mcp

技能库维护 MCP server：把 [skill-evolution] 技能的**机械环节**工具化（备份/损坏扫描/决策日志/体检），供任意 MCP 客户端调用。蒸馏、修剪等判断力环节仍在技能侧。

对应 skill-evolution 五步闭环：

| 工具 | 对应环节 | 说明 |
|:---|:---|:---|
| `skill_backup` | §7 改前备份 | cp 技能目录到 `~/.agents/skill-backups/<今天>/`；同日同名拒绝覆盖 |
| `skill_scan_corruption` | §7 损坏扫描（铁律） | formfeed(`\x0c`) / 真 tab / 行中 CR——JSON 序列化转义被解释的隐性损坏；CRLF 行尾不误报 |
| `skill_log_decision` | §2 决策历史 | 四字段（诊断/修订/证据/结果）追加 `references/decision-log.md`，字段缺失拒绝 |
| `skill_read_decisions` | §2 | 条目标题列表，修订前先看防重复踩坑 |
| `skill_validate` | §3/§4 体检 | frontmatter 必填 + 损坏扫描 + 孤儿 reference（未挂链=不可发现）+ decision-log 概要 |

## 安装与注册

```bash
cd D:/skill-maintenance-mcp
uv venv && uv pip install -e ".[dev]"
```

ZCode（`~/.zcode/cli/config.json` → `mcp.servers`）：

```json
{
  "mcp": {
    "servers": {
      "skill-maintenance": {
        "command": "uv",
        "args": ["--directory", "D:/skill-maintenance-mcp", "run", "skill-maintenance-mcp"]
      }
    }
  }
}
```

## 推荐工作流（agent 修订技能时）

```
skill_backup → 修订 → skill_scan_corruption → skill_log_decision → skill_validate
```

## 测试

```bash
uv run pytest -v    # 含对真实技能库的只读联动测试（无技能库环境自动 skip）
```

## 设计边界

- **不做自动字节修复**：修复需要人工判断正确序列（skill-evolution §7 的修复是逐案例的），工具只定位到行号 + kind + snippet。
- 备份默认拒绝同日覆盖：改两次时手动挪走第一份，防止快照语义被静默破坏。
- 上游技能：`~/.agents/skills/skill-evolution/SKILL.md`；骨架方法见 `mcp-server-craft` 技能。
