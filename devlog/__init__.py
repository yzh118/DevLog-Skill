"""DevLog：纯 Markdown + JSON 驱动的工程变更日志（标准库实现）。"""

from devlog.core import devlog_query, devlog_write

__all__ = ["devlog_write", "devlog_query"]
