"""技能体检与备份（skill-evolution §3/§4/§7 辅助环节工具化）。"""

from __future__ import annotations

import datetime
import re
import shutil
from pathlib import Path

from .corruption import scan_paths
from .decisions import read_decisions

# frontmatter 顶层必填 key（description 用于召回判定, 缺了技能等于不可发现）
REQUIRED_FRONTMATTER = ("name", "description", "version")


def validate_skill(skill_path: str) -> dict:
    """技能体检: frontmatter 必填 + 损坏扫描 + 孤儿 reference + decision-log 概要。"""
    root = Path(skill_path)
    if not (root / "SKILL.md").exists():
        return {"ok": False, "errors": [f"SKILL.md 不存在: {root}"]}

    text = (root / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    frontmatter = _parse_frontmatter(text)
    missing_keys = [k for k in REQUIRED_FRONTMATTER if not frontmatter.get(k)]

    # 孤儿 reference: references/ 下的文件未在 SKILL.md 正文出现文件名（2026-09-05 决策: 挂链才算可发现）
    orphans: list[str] = []
    refs_dir = root / "references"
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.glob("*.md")):
            if ref.name not in text:
                orphans.append(f"references/{ref.name}")

    scan = scan_paths([str(root)])
    decisions = read_decisions(str(root))

    return {
        "ok": not missing_keys and scan["clean"],
        "skill": root.name,
        "frontmatter": {k: bool(frontmatter.get(k)) for k in REQUIRED_FRONTMATTER},
        "missing_frontmatter": missing_keys,
        "orphan_references": orphans,
        "corruption": {"files_scanned": scan["files_scanned"], "issues": scan["issues"]},
        "decision_log": {"exists": decisions["exists"], "entries": len(decisions["entries"])},
    }


def backup_skills(skills_root: str, skill_names: list[str], backup_root: str | None = None) -> dict:
    """改前备份: cp 技能目录到 <backup_root|~/.agents/skill-backups>/YYYY-MM-DD/。"""
    root = Path(skills_root)
    dest_root = Path(backup_root) if backup_root else Path.home() / ".agents" / "skill-backups"
    day_dir = dest_root / datetime.datetime.now().astimezone().date().isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    backed_up, errors = [], []
    for name in skill_names:
        src = root / name
        if not src.is_dir():
            errors.append({"skill": name, "reason": f"技能目录不存在: {src}"})
            continue
        dest = day_dir / name
        if dest.exists():
            errors.append({"skill": name, "reason": f"今日已有同名备份: {dest}（避免覆盖, 如需重备份请先移动）"})
            continue
        shutil.copytree(src, dest)
        backed_up.append({"skill": name, "dest": str(dest)})

    return {"ok": not errors, "backup_root": str(day_dir), "backed_up": backed_up, "errors": errors}


def _parse_frontmatter(text: str) -> dict:
    """极简 frontmatter 解析: --- 之间的顶层 `key: value`（不引 yaml 依赖）。"""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()[1:]
    result: dict[str, str] = {}
    for line in lines:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.+)$", line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result
