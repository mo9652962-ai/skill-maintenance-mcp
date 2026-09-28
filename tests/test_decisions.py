"""decisions 测试: 四字段格式 + 追加不覆盖。"""

from __future__ import annotations

from skill_maintenance_mcp.decisions import log_decision, read_decisions


def test_creates_log_with_header(skill_dir):
    result = log_decision(str(skill_dir), "测试修订", "诊断内容", "修订内容", "证据内容", "接受")
    assert result["ok"]
    log = skill_dir / "references" / "decision-log.md"
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert text.startswith("# 决策日志")
    assert "## " in text and "测试修订" in text
    assert "- **诊断**：诊断内容" in text
    assert "- **结果**：接受" in text


def test_appends_without_overwrite(skill_dir):
    log_decision(str(skill_dir), "第一条", "d1", "r1", "e1", "接受")
    log_decision(str(skill_dir), "第二条", "d2", "r2", "e2", "拒绝: 证据不足")
    text = (skill_dir / "references" / "decision-log.md").read_text(encoding="utf-8")
    assert "第一条" in text and "第二条" in text
    assert text.index("第一条") < text.index("第二条")


def test_rejects_empty_fields(skill_dir):
    result = log_decision(str(skill_dir), "空壳", "", "r", "e", "x")
    assert not result["ok"]
    assert "诊断" in result["errors"][0]
    assert not (skill_dir / "references" / "decision-log.md").exists()


def test_read_decisions_summary(skill_dir):
    assert read_decisions(str(skill_dir))["exists"] is False
    log_decision(str(skill_dir), "记录甲", "d", "r", "e", "接受")
    summary = read_decisions(str(skill_dir))
    assert summary["exists"] and len(summary["entries"]) == 1
    assert "记录甲" in summary["entries"][0]
