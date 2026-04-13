from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_TYPES = frozenset({"修改", "删除", "增添", "备注"})
REMARK_SUBTYPES = frozenset({"调试", "松口", "外部", "其他"})


def _now_iso() -> str:
    dt = datetime.now().astimezone()
    return dt.isoformat(timespec="milliseconds")


def _parse_iso(ts: str) -> datetime:
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _timestamp_to_id(ts: str) -> str:
    dt = _parse_iso(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone()
    ms = local.microsecond // 1000
    return (
        local.strftime("%Y%m%d-%H%M%S-") + f"{ms:03d}"
    )


def _log_date_str(ts: str) -> str:
    dt = _parse_iso(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().strftime("%Y-%m-%d")


def _display_type(entry_type: str, subtype: str | None) -> str:
    if entry_type == "备注" and subtype:
        return f"备注/{subtype}"
    return entry_type


def _validate_entry(entry: dict[str, Any]) -> None:
    t = entry.get("type")
    if t not in VALID_TYPES:
        raise ValueError(f"type 必须是 {sorted(VALID_TYPES)} 之一，收到: {t!r}")
    st = entry.get("subtype")
    if t == "备注":
        if not st or st not in REMARK_SUBTYPES:
            raise ValueError(f"备注类型必须提供 subtype，且为 {sorted(REMARK_SUBTYPES)} 之一")
    elif st is not None and st != "":
        raise ValueError("非备注类型时 subtype 应为 null 或省略")
    for key in ("agent_id", "target", "summary", "reason", "impact"):
        if key not in entry or entry[key] in (None, ""):
            raise ValueError(f"缺少必填字段或为空: {key}")
    summary = str(entry["summary"])
    if len(summary) > 80:
        raise ValueError("summary 不超过 80 字")
    if "related_ids" not in entry:
        raise ValueError("缺少 related_ids 字段（可为空数组）")


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    tmp.replace(path)


def _render_markdown_block(
    ts: str,
    entry_type: str,
    subtype: str | None,
    agent_id: str,
    target: str,
    summary: str,
    reason: str,
    impact: str,
    related_ids: list[str],
) -> str:
    label = _display_type(entry_type, subtype)
    rel = "无"
    if related_ids:
        rel = "、".join(related_ids)
    lines = [
        f"## [{ts}] | {label} | agent:{agent_id}",
        "",
        f"**条目 ID：** `{_timestamp_to_id(ts)}`",
        f"**目标文件/模块：** `{target}`",
        f"**变更摘要：** {summary}",
        f"**触发原因：** {reason}",
        f"**影响范围：** {impact}",
        f"**关联条目：** {rel}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def _split_markdown_entries(content: str) -> list[str]:
    """按二级标题切分，保留各节原文（含标题行）。"""
    lines = content.splitlines()
    chunks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if line.startswith("## "):
            if current is not None:
                chunks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        chunks.append(current)
    return ["\n".join(c).strip() for c in chunks if c]


def _extract_id_from_section(section: str) -> str | None:
    m = re.search(r"\*\*条目 ID：\*\* `([^`]+)`", section)
    if m:
        return m.group(1).strip()
    return None


def devlog_write(entry: dict[str, Any], base_path: str | Path = ".devlog") -> dict[str, Any]:
    """
    将一条日志追加写入当日 .md 文件，并更新 index.json。
    entry 字段与 DEVLOG_WRITE 协议一致。
    """
    _validate_entry(entry)
    root = Path(base_path)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    ts = _now_iso()
    entry_type = str(entry["type"])
    subtype = entry.get("subtype") if entry_type == "备注" else None
    agent_id = str(entry["agent_id"])
    target = str(entry["target"])
    summary = str(entry["summary"])
    reason = str(entry["reason"])
    impact = str(entry["impact"])
    related_ids = list(entry.get("related_ids") or [])

    log_file_name = f"{_log_date_str(ts)}.md"
    log_path = logs / log_file_name

    block = _render_markdown_block(
        ts, entry_type, subtype, agent_id, target, summary, reason, impact, related_ids
    )

    with open(log_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(block)

    entry_id = _timestamp_to_id(ts)
    index_path = root / "index.json"
    if index_path.is_file():
        index_data = _load_json(index_path)
    else:
        index_data = {"last_updated": None, "total_entries": 0, "entries": []}

    new_row = {
        "id": entry_id,
        "timestamp": ts,
        "type": entry_type,
        "subtype": subtype,
        "agent": agent_id,
        "target": target,
        "summary": summary,
        "log_file": log_file_name,
    }
    entries = list(index_data.get("entries") or [])
    entries.append(new_row)
    index_data["entries"] = entries
    index_data["total_entries"] = len(entries)
    index_data["last_updated"] = ts
    _atomic_write_json(index_path, index_data)

    return new_row


def _date_in_range(day: str, date_from: str | None, date_to: str | None) -> bool:
    if date_from and day < date_from:
        return False
    if date_to and day > date_to:
        return False
    return True


def devlog_query(filters: dict[str, Any], base_path: str | Path = ".devlog") -> list[dict[str, Any]]:
    """
    按 DEVLOG_QUERY 协议从 index.json 过滤，再读取对应日志文件中的完整 Markdown 段落。
    返回按时间戳倒序的列表，每项含 index 字段与 full_markdown。
    """
    root = Path(base_path)
    index_path = root / "index.json"
    index_data = _load_json(index_path)
    entries: list[dict[str, Any]] = list(index_data.get("entries") or [])

    dr = filters.get("date_range") or {}
    date_from = dr.get("from")
    date_to = dr.get("to")
    types = filters.get("types")
    if types is not None and not isinstance(types, (list, tuple)):
        types = None
    # 留空或 [] 表示查所有类型
    type_set = set(types) if types else None
    agent_id = filters.get("agent_id")
    keyword = (filters.get("keyword") or "").strip().lower() or None

    filtered: list[dict[str, Any]] = []
    for row in entries:
        ts = row.get("timestamp", "")
        try:
            day = _log_date_str(ts)
        except Exception:
            continue
        if not _date_in_range(day, date_from, date_to):
            continue
        if type_set is not None and row.get("type") not in type_set:
            continue
        if agent_id and row.get("agent") != agent_id:
            continue
        if keyword:
            hay = (str(row.get("summary", "")) + str(row.get("target", ""))).lower()
            if keyword not in hay:
                continue
        filtered.append(row)

    filtered.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

    log_cache: dict[str, str] = {}
    result: list[dict[str, Any]] = []
    for row in filtered:
        lf = row.get("log_file")
        eid = row.get("id")
        if not lf or not eid:
            continue
        log_path = root / "logs" / lf
        if str(log_path) not in log_cache:
            if log_path.is_file():
                with open(log_path, encoding="utf-8") as f:
                    log_cache[str(log_path)] = f.read()
            else:
                log_cache[str(log_path)] = ""
        body = log_cache[str(log_path)]
        full = ""
        for sec in _split_markdown_entries(body):
            sid = _extract_id_from_section(sec)
            if sid == eid:
                full = sec
                break
        item = dict(row)
        item["full_markdown"] = full
        result.append(item)

    return result
