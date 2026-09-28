"""共享 fixture: 合成技能目录。"""

from __future__ import annotations

import pytest

SKILL_MD = """---
name: demo-skill
description: 测试技能
version: 1.0.0
---

# Demo

正文引用 references/guide.md 作为参考。
"""

GUIDE_MD = "# Guide\n\n正常内容, CRLF 行尾也算正常。\n"


@pytest.fixture
def skill_dir(tmp_path):
    """合法最小技能。"""
    root = tmp_path / "demo-skill"
    (root / "references").mkdir(parents=True)
    (root / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (root / "references" / "guide.md").write_text(GUIDE_MD, encoding="utf-8")
    return root


@pytest.fixture
def corrupted_skill_dir(tmp_path):
    """带三种损坏的技能: formfeed / 真 tab / 行中 CR（skill-evolution §7 场景）。"""
    root = tmp_path / "broken-skill"
    (root / "references").mkdir(parents=True)
    (root / "SKILL.md").write_bytes(
        b"---\nname: broken\ndescription: x\nversion: 0.1.0\n---\n\n# B\n\nfind_by_\x0cname \xe5\x8f\x98 ind_by_name\n"
    )
    (root / "references" / "bad.md").write_bytes(b"line one\rhidden: tab\there\nlast line with mid\x0dline cr\r\n")
    return root
