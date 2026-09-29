"""corruption 扫描测试: skill-evolution §7 的三类损坏 + 入参形态/不可读文件。"""

from __future__ import annotations

from pathlib import Path

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


def test_single_file_path_and_dedup(skill_dir):
    """单文件入参走 is_file 分支; 目录与文件混合入参 set 去重不重复计数。"""
    guide = skill_dir / "references" / "guide.md"
    result = scan_paths([str(guide), str(skill_dir), str(guide)])
    assert result["files_scanned"] == 2  # guide.md + SKILL.md, guide.md 只算一次
    assert result["clean"]


def test_unreadable_file_reported(tmp_path, monkeypatch):
    """读取抛 OSError 的文件报告 unreadable（行号 0, 快照为错误信息, 不中断整轮扫描）。"""
    target = tmp_path / "locked.md"
    target.write_bytes(b"ok\n")
    original = Path.read_bytes

    def fake_read_bytes(self):
        if self == target:
            raise OSError(13, "permission denied")
        return original(self)

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)
    result = scan_paths([str(target)])
    assert not result["clean"]
    assert result["issues"] == [
        {"file": str(target), "line": 0, "kind": "unreadable", "snippet": "[Errno 13] permission denied"}
    ]


def test_untracked_extensions_skipped(tmp_path):
    """扫描 glob 之外的扩展名（如 .txt）不计数——即便含损坏字符也不误报。"""
    root = tmp_path / "skill-x"
    root.mkdir()
    (root / "SKILL.md").write_bytes(b"ok\n")
    (root / "notes.txt").write_bytes(b"tab\there\x0c\n")
    result = scan_paths([str(root)])
    assert result["files_scanned"] == 1
    assert result["clean"]
