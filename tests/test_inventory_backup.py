"""inventory 测试: 体检（frontmatter/孤儿 reference）+ 备份 + 决策日志往返。"""

from __future__ import annotations

from pathlib import Path

from skill_maintenance_mcp.decisions import log_decision
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


def test_validate_without_frontmatter(tmp_path):
    """SKILL.md 无 frontmatter: 三个必填位全缺, 体检不通过（解析短路分支）。"""
    root = tmp_path / "plain-skill"
    root.mkdir()
    (root / "SKILL.md").write_text("# 无 frontmatter\n", encoding="utf-8")
    result = validate_skill(str(root))
    assert not result["ok"]
    assert result["frontmatter"] == {"name": False, "description": False, "version": False}
    assert result["missing_frontmatter"] == ["name", "description", "version"]


def test_validate_partial_frontmatter(tmp_path):
    """只有 name: 精确列出缺的 description/version。"""
    root = tmp_path / "partial-skill"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: partial\n---\n\n# P\n", encoding="utf-8")
    result = validate_skill(str(root))
    assert result["missing_frontmatter"] == ["description", "version"]


def test_backup_mixed_success_and_missing(skill_dir, tmp_path):
    """多技能混合备份: 存在的成功落地、不存在的进 errors, 整体 ok=False。"""
    result = backup_skills(str(skill_dir.parent), ["demo-skill", "ghost"], backup_root=str(tmp_path / "bk"))
    assert not result["ok"]
    assert [b["skill"] for b in result["backed_up"]] == ["demo-skill"]
    expected = {"skill": "ghost", "reason": f"技能目录不存在: {skill_dir.parent / 'ghost'}"}
    assert result["errors"] == [expected]
    assert (Path(result["backup_root"]) / "demo-skill" / "SKILL.md").exists()


def test_backup_default_root_under_home(skill_dir, tmp_path, monkeypatch):
    """backup_root 缺省落到 Path.home()/.agents/skill-backups/<今天>/（打桩 home 防碰真实目录）。"""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    result = backup_skills(str(skill_dir.parent), ["demo-skill"])
    assert result["ok"]
    assert result["backup_root"].startswith(str(fake_home / ".agents" / "skill-backups"))
    assert (Path(result["backup_root"]) / "demo-skill" / "SKILL.md").exists()


def test_validate_surfaces_decision_log_summary(skill_dir):
    """决策日志与体检的往返: log_decision 后 validate 的 decision_log 计数同步且不挡体检。"""
    assert log_decision(str(skill_dir), "体检前记录", "d", "r", "e", "接受")["ok"]
    result = validate_skill(str(skill_dir))
    assert result["ok"]
    assert result["decision_log"] == {"exists": True, "entries": 1}
