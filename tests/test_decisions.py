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


def test_rejects_blank_title(skill_dir):
    """标题全空白同样拒绝——title 是第 5 个必填位, 且拒绝时不落盘。"""
    result = log_decision(str(skill_dir), "   ", "d", "r", "e", "x")
    assert not result["ok"]
    assert "title" in result["errors"][0]
    assert not (skill_dir / "references" / "decision-log.md").exists()


def test_roundtrip_titles_read_back(skill_dir):
    """追加两条后 read_decisions 能按序读回; title 两侧空白被剥除。"""
    first = log_decision(str(skill_dir), "  往返一  ", "d", "r", "e", "接受")
    assert first["ok"] and first["title"] == "往返一"
    log_decision(str(skill_dir), "往返二", "d", "r", "e", "拒绝")
    summary = read_decisions(str(skill_dir))
    assert summary["exists"]
    assert len(summary["entries"]) == 2
    assert summary["entries"][0].endswith("— 往返一")
    assert summary["entries"][1].endswith("— 往返二")


def test_read_decisions_missing_path(tmp_path):
    """不存在技能路径的读回是空概要而非报错（错误路径契约）。"""
    assert read_decisions(str(tmp_path / "none")) == {"exists": False, "entries": []}
