#!/usr/bin/env python3
"""
三个使用示例（独立临时目录，不污染项目 .devlog）：
1. 正常「修改」写入
2. 「备注/松口」写入
3. 按日期范围查询所有「删除」类型
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devlog.core import devlog_query, devlog_write  # noqa: E402


def _print_title(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def example_modify() -> None:
    _print_title("示例 1：正常修改操作的日志写入")
    base = Path(tempfile.mkdtemp(prefix="devlog-ex1-"))
    try:
        (base / ".devlog" / "logs").mkdir(parents=True)
        (base / ".devlog" / "index.json").write_text(
            json.dumps(
                {"last_updated": None, "total_entries": 0, "entries": []},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        row = devlog_write(
            {
                "type": "修改",
                "subtype": None,
                "agent_id": "cursor-main",
                "target": "src/api/auth.ts",
                "summary": "将 JWT 过期时间从 1h 改为 24h，适配移动端长会话",
                "reason": "用户需求 #42",
                "impact": "仅影响新签发的 token",
                "related_ids": [],
            },
            base_path=base / ".devlog",
        )
        print("index 新条目:", json.dumps(row, ensure_ascii=False, indent=2))
        log_files = list((base / ".devlog" / "logs").glob("*.md"))
        print("生成的日志文件:", log_files[0].name if log_files else "(无)")
        if log_files:
            print("--- Markdown 预览 ---")
            print(log_files[0].read_text(encoding="utf-8")[:800])
    finally:
        shutil.rmtree(base, ignore_errors=True)


def example_waiver() -> None:
    _print_title("示例 2：松口操作（备注/松口）")
    base = Path(tempfile.mkdtemp(prefix="devlog-ex2-"))
    try:
        (base / ".devlog" / "logs").mkdir(parents=True)
        (base / ".devlog" / "index.json").write_text(
            json.dumps(
                {"last_updated": None, "total_entries": 0, "entries": []},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        row = devlog_write(
            {
                "type": "备注",
                "subtype": "松口",
                "agent_id": "cursor-main",
                "target": "CI / 测试流程",
                "summary": "按用户要求跳过单元测试后合并",
                "reason": '用户原话："先别跑测试，直接合并"',
                "impact": "可能遗漏回归问题，需后续补测",
                "related_ids": [],
            },
            base_path=base / ".devlog",
        )
        print("index 新条目:", json.dumps(row, ensure_ascii=False, indent=2))
        log_files = list((base / ".devlog" / "logs").glob("*.md"))
        if log_files:
            print("--- Markdown 预览 ---")
            print(log_files[0].read_text(encoding="utf-8"))
    finally:
        shutil.rmtree(base, ignore_errors=True)


def example_query_deletes() -> None:
    _print_title("示例 3：查询日期范围内所有「删除」类型")
    base = Path(tempfile.mkdtemp(prefix="devlog-ex3-"))
    try:
        (base / ".devlog" / "logs").mkdir(parents=True)
        (base / ".devlog" / "index.json").write_text(
            json.dumps(
                {"last_updated": None, "total_entries": 0, "entries": []},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        d = base / ".devlog"
        devlog_write(
            {
                "type": "删除",
                "subtype": None,
                "agent_id": "cursor-main",
                "target": "src/legacy/old_api.ts",
                "summary": "移除已废弃的 REST 接口",
                "reason": "产品确认无调用方",
                "impact": "对外 API 不再提供该路径",
                "related_ids": [],
            },
            base_path=d,
        )
        devlog_write(
            {
                "type": "增添",
                "subtype": None,
                "agent_id": "cursor-main",
                "target": "src/api/new_route.ts",
                "summary": "新增健康检查路由",
                "reason": "运维监控需要",
                "impact": "仅新增 GET /health",
                "related_ids": [],
            },
            base_path=d,
        )
        # 从 index 取日期范围
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
        days = sorted(
            {
                ts[:10]
                for e in idx["entries"]
                for ts in [e["timestamp"]]
            }
        )
        date_from = days[0] if days else "2000-01-01"
        date_to = days[-1] if days else "2099-12-31"

        out = devlog_query(
            {
                "date_range": {"from": date_from, "to": date_to},
                "types": ["删除"],
                "agent_id": None,
                "keyword": "",
            },
            base_path=d,
        )
        print(f"查询区间: {date_from} ~ {date_to}，types=['删除']")
        print("命中条数:", len(out))
        for item in out:
            print("---")
            print("summary:", item.get("summary"))
            print("full_markdown:\n", item.get("full_markdown", "")[:600])
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    example_modify()
    example_waiver()
    example_query_deletes()
    print("\n全部示例执行完毕。\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
