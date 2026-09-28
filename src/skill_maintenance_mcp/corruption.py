"""技能文件损坏扫描（skill-evolution §7 工具化）。

隐性损坏: 内容经 JSON 序列化写入时转义序列被解释——
- \\f → formfeed (\\x0c): find_by_name 变 ind_by_name
- 真 tab: 整章压行/错位
- 行中 CR: 行被截断 (CRLF 行尾的 \\r 不算)

铁律: 每次写入/修订技能文件后必跑。
"""

from __future__ import annotations

from pathlib import Path

MD_SCAN_GLOBS = ["SKILL.md", "references/*.md", "references/*.json", "templates/*.md", "templates/*.py", "scripts/*.py", "scripts/*.mjs", "*.md"]


def scan_paths(paths: list[str], skills_root: str | None = None) -> dict:
    """扫描文件/目录。目录按技能结构展开。返回 {files_scanned, issues: [{file, line, kind, snippet}]}。"""
    root = Path(skills_root) if skills_root else None
    files: list[Path] = []
    for raw in paths:
        path = Path(raw) if not root else root / raw
        if path.is_dir():
            for pattern in MD_SCAN_GLOBS:
                files.extend(p for p in path.glob(pattern) if p.is_file())
        elif path.is_file():
            files.append(path)
    files = sorted(set(files))

    issues: list[dict] = []
    for file in files:
        issues.extend(_scan_file(file))
    return {"files_scanned": len(files), "issues": issues, "clean": not issues}


def _scan_file(path: Path) -> list[dict]:
    """二进制读, 按 \\n 拆行逐行检查; 保留原始行尾以正确判定「行中 CR」。"""
    try:
        data = path.read_bytes()
    except OSError as error:
        return [{"file": str(path), "line": 0, "kind": "unreadable", "snippet": str(error)}]

    issues: list[dict] = []
    for line_no, raw_line in enumerate(data.split(b"\n"), start=1):
        # 去掉行尾 CRLF/LF 的行尾符后再查行中 CR
        body = raw_line[:-1] if raw_line.endswith(b"\r") else raw_line
        for kind, marker in (("formfeed", b"\x0c"), ("tab", b"\t"), ("mid-line-cr", b"\r")):
            if marker in body:
                issues.append(
                    {
                        "file": str(path),
                        "line": line_no,
                        "kind": kind,
                        "snippet": body[:80].decode("utf-8", errors="replace"),
                    }
                )
    return issues
