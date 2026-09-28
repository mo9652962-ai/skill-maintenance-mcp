"""decision-log 追加（skill-evolution §2 决策历史工具化）。

格式对齐用户现有 decision-log.md:
  ## YYYY-MM-DD — 标题
  - **诊断**：...
  - **修订**：...
  - **证据**：...
  - **结果**：...
"""

from __future__ import annotations

import datetime
from pathlib import Path

REQUIRED_FIELDS = ("diagnosis", "revision", "evidence", "result")
FIELD_LABELS = {"diagnosis": "诊断", "revision": "修订", "evidence": "证据", "result": "结果"}


def log_decision(
    skill_path: str,
    title: str,
    diagnosis: str,
    revision: str,
    evidence: str,
    result: str,
) -> dict:
    """向 <skill_path>/references/decision-log.md 追加一条决策记录（无则创建含表头）。返回 {ok, log_path, errors}。"""
    values = {"diagnosis": diagnosis, "revision": revision, "evidence": evidence, "result": result}
    missing = [FIELD_LABELS[f] for f in REQUIRED_FIELDS if not str(values[f]).strip()]
    if not str(title).strip():
        missing.append("title")
    if missing:
        return {"ok": False, "errors": [f"必填字段为空: {', '.join(missing)}（四字段记录让未来 agent 不用重新推导旧决策）"]}

    log_path = Path(skill_path) / "references" / "decision-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()
    entry_lines = [f"## {today} — {title.strip()}"]
    entry_lines += [f"- **{FIELD_LABELS[f]}**：{str(values[f]).strip()}" for f in REQUIRED_FIELDS]
    entry = "\n".join(entry_lines) + "\n"

    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        separator = "" if content.endswith("\n\n") else ("\n" if content.endswith("\n") else "\n\n")
        log_path.write_text(content + separator + entry, encoding="utf-8")
    else:
        log_path.write_text("# 决策日志\n\n" + entry, encoding="utf-8")
    return {"ok": True, "log_path": str(log_path), "date": today, "title": title.strip()}


def read_decisions(skill_path: str) -> dict:
    """读取 decision-log 概要: 是否存在 + 条目标题列表（防重复修订）。"""
    log_path = Path(skill_path) / "references" / "decision-log.md"
    if not log_path.exists():
        return {"exists": False, "entries": []}
    entries = [
        line.lstrip("# ").strip()
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]
    return {"exists": True, "log_path": str(log_path), "entries": entries}
