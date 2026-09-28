"""Skill Maintenance MCP server。

把 skill-evolution 技能的机械环节工具化: 改前备份 → 修订 → 损坏扫描 → decision-log → 体检。
蒸馏/修剪等判断力环节仍在技能侧。
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastmcp import FastMCP

from .corruption import scan_paths
from .decisions import log_decision, read_decisions
from .inventory import backup_skills, validate_skill

DEFAULT_SKILLS_ROOT = "C:/Users/31954/.agents/skills"

mcp = FastMCP(
    "skill-maintenance",
    instructions=(
        "技能库维护工具链（对应 skill-evolution 技能）。推荐流程: skill_backup（改前备份）→ 修订技能 → "
        "skill_scan_corruption（损坏扫描铁律）→ skill_log_decision（四字段决策记录）→ skill_validate（体检）。"
        "蒸馏/修剪判断仍在 skill-evolution 技能侧。"
    ),
)


@mcp.tool
def skill_backup(skill_names: list[str], skills_root: str = DEFAULT_SKILLS_ROOT, backup_root: str | None = None) -> dict:
    """改前备份技能目录到 ~/.agents/skill-backups/<今天>/（skill-evolution 铁律: 修订前必备份）。

    Args:
        skill_names: 技能目录名列表（如 ["esq-question-bank-import"]）
        skills_root: 技能库根目录
        backup_root: 备份目标根（默认 ~/.agents/skill-backups）

    Returns:
        {ok, backup_root, backed_up, errors}。同日同名已存在时拒绝（防覆盖）。
    """
    return backup_skills(skills_root, skill_names, backup_root)


@mcp.tool
def skill_scan_corruption(paths: list[str], skills_root: str | None = None) -> dict:
    """技能文件损坏扫描（铁律: 每次写入/修订后必跑）。检测 formfeed(\\x0c) / 真 tab / 行中 CR——JSON 序列化转义被解释的隐性损坏。

    Args:
        paths: 文件或技能目录列表（目录按 SKILL.md/references/templates/scripts 展开扫描）
        skills_root: 传入相对路径时的根目录

    Returns:
        {files_scanned, clean, issues:[{file, line, kind, snippet}]}。clean=false 时按行号做字节级修复（参照 skill-evolution §7）。
    """
    return scan_paths(paths, skills_root)


@mcp.tool
def skill_log_decision(
    skill_path: str,
    title: str,
    diagnosis: str,
    revision: str,
    evidence: str,
    result: str,
) -> dict:
    """向技能的 references/decision-log.md 追加决策记录（四字段: 诊断/修订/证据/结果——记「为什么改」, 未来 agent 不重新踩坑）。

    Args:
        skill_path: 技能目录绝对路径
        title: 一句话标题（自动加日期前缀）
        diagnosis: 诊断——技能在什么场景失效
        revision: 修订——改了哪里
        evidence: 证据——评估/实测结果
        result: 结果——接受/拒绝 + 原因

    Returns:
        {ok, log_path, date}。字段缺失会拒绝（空壳决策不如不记）。
    """
    return log_decision(skill_path, title, diagnosis, revision, evidence, result)


@mcp.tool
def skill_read_decisions(skill_path: str) -> dict:
    """读取技能 decision-log 概要（条目标题列表），修订前先看避免重复踩坑。"""
    return read_decisions(skill_path)


@mcp.tool
def skill_validate(skill_path: str) -> dict:
    """技能体检: frontmatter 必填（name/description/version）+ 损坏扫描 + 孤儿 reference（未挂链=不可发现）+ decision-log 概要。

    Args:
        skill_path: 技能目录绝对路径

    Returns:
        {ok, frontmatter, missing_frontmatter, orphan_references, corruption, decision_log}
    """
    return validate_skill(skill_path)


def main() -> None:
    if sys.platform == "win32":
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name)
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
    mcp.run()


if __name__ == "__main__":
    main()
