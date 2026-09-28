# Security

## Mimosa deep scan（2026-09-28）

| 项 | 值 |
|:---|:---|
| scanId | `scan-2026-09-28T05-05-46.948Z-b4a5e2362fe4` |
| seal | `sha256:2002a60e33ee64c3f458c6ae1009b5470dde5a96e6fc52fd745a70a043a399a1` |
| depth | deep |
| findings | **0**（high 0 / medium 0 / low 0 / info 0 / businessLogic 0） |
| run status | **inconclusive** |
| verdict effect | none |

### 覆盖说明（如实）

- 结论为 inconclusive 而非 clean：调用图部分不完整（动态派发/超出分析规模），跨文件可达性可能不完整；威胁模型阶段 partial（MCP 工具经 `@mcp.tool` 装饰器动态注册，静态分析未识别为 entry points）。
- 即：已审查范围内零发现，但不是全量安全认证。
- 复核：扫描工件（含封印）在 `~/.mimosa/security-scans/project-47500b7235761f8141b3f0d5/scan-2026-09-28T05-05-46.948Z-b4a5e2362fe4/`。

### 安全边界备注

- 工具读写范围限于参数指定的路径：备份默认写 `~/.agents/skill-backups/`，其余操作读 `skills_root` 下的技能文件。
- `skill_log_decision` / `skill_backup` 对文件系统的写入以调用方传入的路径为准——MCP 客户端应将本 server 暴露给可信会话。
- 无网络行为、无 subprocess、无遥测。
