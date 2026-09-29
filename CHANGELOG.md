# Changelog

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.1.1] - 2026-09-30

### Added

- CI：ruff + bandit lint job（dev extras + [tool.ruff] 配置）
- 测试：18 → 33 例，覆盖率 91% → 100%（损坏扫描逐类 / 备份自定义根 / 决策日志往返 / 体检判定 / 工具包装直调），覆盖率棘轮 88 → 98
- 文档：README 扩充为完整工具文档（5 工具参数表对齐 src 签名 + uvx 快速开始 + 四字段格式与两条铁律）

## [0.1.0] - 2026-09-28

### Added

- FastMCP server：skill 体检（frontmatter 必填 + 损坏扫描 + 孤儿引用）工具链
- 备份 → 损坏扫描 → 决策日志 → 体检 维护流程机械化
- MIT LICENSE + 仓库元数据
- CI：ubuntu/windows 矩阵 + 覆盖率度量 + pip-audit 依赖扫描（本次补齐）
- Publish to PyPI（Trusted Publishing/OIDC）+ CycloneDX SBOM 工作流（本次补齐）
