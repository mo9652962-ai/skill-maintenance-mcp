"""MCP 工具层集成测试: fastmcp Client + 包装函数直接调用 + main 入口。"""

from __future__ import annotations

import sys

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


def test_tool_wrappers_direct_call(skill_dir, tmp_path):
    """fastmcp 4 装饰后仍是原函数: 5 个包装可直接调用（含不存在路径错误分支）。"""
    from skill_maintenance_mcp.server import (
        skill_backup,
        skill_log_decision,
        skill_read_decisions,
        skill_scan_corruption,
        skill_validate,
    )

    ghost = str(tmp_path / "ghost")
    assert skill_scan_corruption(paths=[str(skill_dir)])["clean"]
    assert skill_read_decisions(ghost) == {"exists": False, "entries": []}
    assert skill_validate(ghost)["errors"]
    assert not skill_backup(["nope"], skills_root=str(tmp_path), backup_root=str(tmp_path / "bk"))["ok"]
    assert not skill_log_decision(ghost, "t", "", "r", "e", "x")["ok"]


async def test_backup_tool_via_client(skill_dir, tmp_path):
    """协议层: skill_backup 走 fastmcp Client 全链路落到自定义 backup_root。"""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "skill_backup",
            {
                "skill_names": ["demo-skill"],
                "skills_root": str(skill_dir.parent),
                "backup_root": str(tmp_path / "bk"),
            },
        )
    assert result.data["ok"] is True
    assert (Path(result.data["backup_root"]) / "demo-skill" / "SKILL.md").exists()


async def test_validate_tool_on_synthetic_skill(skill_dir):
    """协议层体检用合成技能——CI 无真实技能库时也保持 skill_validate 包装体覆盖。"""
    async with Client(mcp) as client:
        result = await client.call_tool("skill_validate", {"skill_path": str(skill_dir)})
    data = result.data
    assert data["ok"] is True
    assert data["corruption"]["files_scanned"] >= 2 and not data["corruption"]["issues"]


@pytest.mark.filterwarnings("ignore::RuntimeWarning")  # runpy 重执行已在 sys.modules 的模块, 警告无碍
def test_main_entrypoint(monkeypatch):
    """main(): 打桩 FastMCP.run 防阻塞; runpy 以 __main__ 重执行触发入口分支（含 win32 reconfigure）。"""
    import runpy

    from fastmcp import FastMCP

    class FakeStream:
        def __init__(self):
            self.calls = []

        def reconfigure(self, **kwargs):
            self.calls.append(kwargs)

    fake_out, fake_err = FakeStream(), FakeStream()
    monkeypatch.setattr(sys, "stdout", fake_out)
    monkeypatch.setattr(sys, "stderr", fake_err)
    if sys.platform != "win32":  # Linux CI 模拟 win32 分支, 保证双平台同覆盖率
        monkeypatch.setattr(sys, "platform", "win32")

    runs = []
    monkeypatch.setattr(FastMCP, "run", lambda self: runs.append(self.name))
    runpy.run_module("skill_maintenance_mcp.server", run_name="__main__")

    assert runs == ["skill-maintenance"]
    assert fake_out.calls == [{"encoding": "utf-8"}]
    assert fake_err.calls == [{"encoding": "utf-8"}]
