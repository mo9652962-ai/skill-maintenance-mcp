"""inventory 测试: 体检（frontmatter/孤儿 reference）+ 备份。"""

from __future__ import annotations

from pathlib import Path

from skill_maintenance_mcp.inventory import backup_skills, validate_skill


def test_validate_clean_skill(skill_dir):
    result = validate_skill(str(skill_dir))
    assert result["ok"]
    assert result["frontmatter"] == {"name": True, "description": True, "version": True}
    assert result["orphan_references"] == []
    assert result["decision_log"]["exists"] is False


def test_validate_flags_orphan_reference(skill_dir):
    """references/ 下未挂链的文件 = 不可发现（2026-09-05 决策日志场景）。"""
    (skill_dir / "references" / "orphan.md").write_text("# 没人引用我\n", encoding="utf-8")
    result = validate_skill(str(skill_dir))
    assert result["orphan_references"] == ["references/orphan.md"]


def test_validate_flags_corruption(corrupted_skill_dir):
    result = validate_skill(str(corrupted_skill_dir))
    assert not result["ok"]
    assert result["corruption"]["issues"]


def test_validate_missing_skill(tmp_path):
    assert not validate_skill(str(tmp_path / "nope"))["ok"]


def test_backup_and_refuse_same_day(skill_dir, tmp_path):
    backup_root = tmp_path / "backups"
    result = backup_skills(str(skill_dir.parent), ["demo-skill"], backup_root=str(backup_root))
    assert result["ok"]
    day_dir = result["backup_root"]
    assert (Path(day_dir) / "demo-skill" / "SKILL.md").exists()
    # 同日同名校验拒绝
    again = backup_skills(str(skill_dir.parent), ["demo-skill"], backup_root=str(backup_root))
    assert not again["ok"]
    assert "同名备份" in again["errors"][0]["reason"]


def test_backup_missing_skill(skill_dir, tmp_path):
    result = backup_skills(str(skill_dir.parent), ["ghost-skill"], backup_root=str(tmp_path / "b"))
    assert not result["ok"]
    assert "不存在" in result["errors"][0]["reason"]
