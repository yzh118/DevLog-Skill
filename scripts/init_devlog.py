#!/usr/bin/env python3
"""一键初始化 DevLog 目录结构，并在 agents.json 注册默认 cursor-main。"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    devlog = root / ".devlog"
    logs = devlog / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    now = datetime.now().astimezone().isoformat(timespec="milliseconds")

    index_path = devlog / "index.json"
    if not index_path.is_file():
        index_data = {
            "last_updated": None,
            "total_entries": 0,
            "entries": [],
        }
        index_path.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"已创建: {index_path.relative_to(root)}")
    else:
        print(f"已存在，跳过: {index_path.relative_to(root)}")

    agents_path = devlog / "agents.json"
    if agents_path.is_file():
        agents_data = json.loads(agents_path.read_text(encoding="utf-8"))
        agents_list = list(agents_data.get("agents") or [])
        ids = {a.get("id") for a in agents_list if isinstance(a, dict)}
        if "cursor-main" not in ids:
            agents_list.append(
                {
                    "id": "cursor-main",
                    "role": "主开发 Agent",
                    "registered_at": now,
                }
            )
            agents_data["agents"] = agents_list
            agents_path.write_text(
                json.dumps(agents_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"已合并注册 cursor-main: {agents_path.relative_to(root)}")
        else:
            print(f"已存在 cursor-main，跳过: {agents_path.relative_to(root)}")
    else:
        agents_data = {
            "agents": [
                {
                    "id": "cursor-main",
                    "role": "主开发 Agent",
                    "registered_at": now,
                }
            ]
        }
        agents_path.write_text(
            json.dumps(agents_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"已写入: {agents_path.relative_to(root)}（默认 Agent cursor-main）")

    print(f"日志目录: {(logs).relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
