"""MCP 工具层集成测试: fastmcp Client + 真实技能库联动。"""

from __future__ import annotations

import pytest

from skill_maintenance_mcp.server import mcp

try:
    from fastmcp import Client
except ImportError:  # pragma: no cover
    pytest.skip("fastmcp 未安装", allow_module_level=True)

from pathlib import Path

REAL_SKILLS_ROOT = Path("C:/Users/31954/.agents/skills")


async def test_list_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == {
            "skill_backup",
            "skill_scan_corruption",
            "skill_log_decision",
            "skill_read_decisions",
            "skill_validate",
        }


async def test_scan_tool_on_corrupted_fixture(corrupted_skill_dir):
    async with Client(mcp) as client:
        result = await client.call_tool("skill_scan_corruption", {"paths": [str(corrupted_skill_dir)]})
        data = result.data
        assert data["clean"] is False
        assert any(i["kind"] == "formfeed" for i in data["issues"])


async def test_decision_tool_roundtrip(skill_dir):
    async with Client(mcp) as client:
        wrote = await client.call_tool(
            "skill_log_decision",
            {
                "skill_path": str(skill_dir),
                "title": "工具层回写",
                "diagnosis": "d",
                "revision": "r",
                "evidence": "e",
                "result": "接受",
            },
        )
        assert wrote.data["ok"] is True
        summary = await client.call_tool("skill_read_decisions", {"skill_path": str(skill_dir)})
        assert summary.data["entries"] and "工具层回写" in summary.data["entries"][0]


@pytest.mark.skipif(not REAL_SKILLS_ROOT.exists(), reason="本机无技能库")
async def test_validate_real_skill():
    """真联动: 对 mcp-server-craft 技能跑体检（该技能结构已知良好）。"""
    target = REAL_SKILLS_ROOT / "mcp-server-craft"
    async with Client(mcp) as client:
        result = await client.call_tool("skill_validate", {"skill_path": str(target)})
        data = result.data
        assert data["frontmatter"] == {"name": True, "description": True, "version": True}
        assert data["corruption"]["clean"] if "clean" in data["corruption"] else not data["corruption"]["issues"]
