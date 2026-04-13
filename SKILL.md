# DevLog Skill

## 这是什么

DevLog 是一套面向多 Agent 协作的代码工程变更日志系统。  
它不替代 Git，而是在 prompt 层补全 Git 看不到的语义层：为什么改、是哪个 Agent 改的、改动意图是什么。

## 快速开始

### 初始化

1. 确认 `.devlog/` 目录已创建（可运行 `python scripts/init_devlog.py` 一键初始化）
2. 确认 `.cursor/rules/devlog.mdc` 已加载
3. 在 `agents.json` 中注册当前 Agent（init 脚本已注册默认 `cursor-main`）

### Agent 写入示例（DEVLOG_WRITE）

完成代码或配置变更后，将下列 JSON 作为写入协议（由工具/脚本落地为 `devlog_write`）：

```json
{
  "type": "修改",
  "subtype": null,
  "agent_id": "cursor-main",
  "target": "src/api/auth.ts",
  "summary": "将 JWT 过期时间从 1h 改为 24h",
  "reason": "用户需求 #42",
  "impact": "仅影响新签发的 token",
  "related_ids": []
}
```

`备注` 类型必须填写 `subtype`：`调试` | `松口` | `外部` | `其他`。

### Agent 查询示例（DEVLOG_QUERY）

```json
{
  "date_range": { "from": "2026-04-10", "to": "2026-04-13" },
  "types": ["修改", "删除"],
  "agent_id": null,
  "keyword": "auth"
}
```

实现见 Python：`devlog_query(filters)`，返回按时间戳倒序的列表，每项含索引字段与 `full_markdown`。

## 日志文件位置

`.devlog/logs/YYYY-MM-DD.md`

## 注意事项

- 日志文件 append-only，不得手动删改历史记录
- `index.json` 建议由 `devlog_write` 自动维护，避免手改导致不一致
- 松口操作必须留痕，这是设计要求而非限制

## 本地工具

- 初始化：`python scripts/init_devlog.py`
- 示例：`python examples/devlog_examples.py`
- 在代码中调用：`from devlog import devlog_write, devlog_query`
