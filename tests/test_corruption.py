"""corruption 扫描测试: skill-evolution §7 的三类损坏。"""

from __future__ import annotations

from skill_maintenance_mcp.corruption import scan_paths


def test_clean_skill(skill_dir):
    result = scan_paths([str(skill_dir)])
    assert result["clean"]
    assert result["files_scanned"] == 2  # SKILL.md + references/guide.md


def test_detects_formfeed_tab_midline_cr(corrupted_skill_dir):
    result = scan_paths([str(corrupted_skill_dir)])
    assert not result["clean"]
    kinds = {(i["kind"], i["file"].split("/")[-1].split("\\")[-1]) for i in result["issues"]}
    assert ("formfeed", "SKILL.md") in kinds
    assert ("tab", "bad.md") in kinds
    assert ("mid-line-cr", "bad.md") in kinds


def test_crlf_line_ending_not_flagged(skill_dir):
    """CRLF 行尾的 \\r 不算损坏（grep -P '\\r(?!$)' 语义）。"""
    (skill_dir / "references" / "crlf.md").write_bytes(b"a\r\nb\r\n")
    result = scan_paths([str(skill_dir)])
    assert result["clean"]


def test_missing_path_tolerated(tmp_path):
    result = scan_paths([str(tmp_path / "no-such-dir")])
    assert result["clean"] and result["files_scanned"] == 0
