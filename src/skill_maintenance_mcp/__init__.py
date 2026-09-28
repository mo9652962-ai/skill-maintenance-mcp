"""skill-maintenance-mcp: 技能库维护 MCP 工具链。"""

from .corruption import scan_paths
from .decisions import log_decision, read_decisions
from .inventory import backup_skills, validate_skill

__version__ = "0.1.0"
__all__ = ["scan_paths", "log_decision", "read_decisions", "backup_skills", "validate_skill", "__version__"]
