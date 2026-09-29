# 贡献指南

## 开发环境

```bash
git clone https://github.com/mo9652962-ai/skill-maintenance-mcp.git && cd skill-maintenance-mcp
uv sync --extra dev
uv run pytest -q --cov=skill_maintenance_mcp --cov-report=term-missing
```

## 约定

- **Actions SHA 固定**：`.github/workflows/` 内所有 `uses:` 必须钉全量 commit SHA。
- **覆盖率只升不降**：CI 输出覆盖率（当前度量阶段，门槛待基线稳定后棘轮）。
- **铁律**：skill 修订前必备份、修订后必损坏扫描——这是本工具的业务本体，改动不得削弱。
- **决策日志**：技能行为变更须同步 references/decision-log.md 记录。

## 提交

PR 前跑 `uv run pytest -q`；commit message 用祈使句。
