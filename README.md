# DevLog

DevLog 是一套面向多 Agent 协作的代码工程变更日志系统。

它不替代 Git，而是在 prompt 层补全 Git 看不到的语义层：为什么改、是哪个 Agent 改的、改动意图是什么。

***

## 核心特性

- **语义化记录**：不仅记录"改了什么"，更记录"为什么改"
- **多 Agent 支持**：清晰标识每个 Agent 的操作边界
- **可追溯性**：通过关联 ID 串联相关变更
- **影响范围说明**：明确标注改动的影响范围

***

## 快速开始

### 初始化项目

```bash
python scripts/init_devlog.py
```

该脚本将自动完成以下工作：

- 创建 `.devlog/` 目录结构
- 生成 `agents.json` 配置文件
- 注册默认 Agent（`cursor-main`）

### 配置 Agent

在 `agents.json` 中注册当前 Agent：

```json
{
  "agents": {
    "cursor-main": {
      "name": "Cursor 主 Agent",
      "role": "主开发 Agent"
    }
  }
}
```

***

## 使用方式

### 写入日志

完成代码或配置变更后，使用以下格式记录：

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

#### 类型说明

| 类型 | 说明        | 备注           |
| -- | --------- | ------------ |
| 新增 | 新增功能或文件   | -            |
| 修改 | 修改现有代码    | -            |
| 删除 | 删除代码或文件   | -            |
| 修复 | 修复 Bug    | -            |
| 重构 | 代码重构      | -            |
| 备注 | 需要特别说明的操作 | 必须填写 subtype |

#### Subtype（仅"备注"类型需要）

- `调试`：调试相关操作
- `松口`：放宽限制或约束
- `外部`：外部依赖变更
- `其他`：其他需要说明的情况

### 查询日志

```json
{
  "date_range": { "from": "2026-04-10", "to": "2026-04-13" },
  "types": ["修改", "删除"],
  "agent_id": null,
  "keyword": "auth"
}
```

***

## 目录结构

```
.devlog/
├── logs/
│   └── YYYY-MM-DD.md    # 按日期组织的日志文件
├── index.json           # 日志索引
└── agents.json          # Agent 注册信息
```

***

## 重要原则

1. **追加-only**：日志文件仅允许追加，不得手动删改历史记录
2. **自动维护**：`index.json` 由 `devlog_write` 自动维护，避免手动修改
3. **松口留痕**：任何放宽限制的操作必须记录，这是设计要求而非限制

***

## 本地工具

| 脚本                            | 用途            |
| ----------------------------- | ------------- |
| `scripts/init_devlog.py`      | 初始化 DevLog 环境 |
| `examples/devlog_examples.py` | 使用示例          |

### 在代码中调用

```python
from devlog import devlog_write, devlog_query

# 写入日志
devlog_write({
    "type": "修改",
    "agent_id": "cursor-main",
    "target": "src/main.py",
    "summary": "优化数据库查询性能",
    "reason": "解决慢查询问题",
    "impact": "提升页面加载速度约 30%"
})

# 查询日志
results = devlog_query({
    "date_range": {"from": "2026-04-01", "to": "2026-04-13"},
    "keyword": "性能"
})
```

***

## 与 Git 的关系

DevLog 不替代 Git，而是与 Git 互补：

| 维度   | Git     | DevLog   |
| ---- | ------- | -------- |
| 记录内容 | 代码 diff | 变更意图与上下文 |
| 作者标识 | 提交者邮箱   | Agent ID |
| 查询方式 | 文件/提交历史 | 语义化筛选    |
| 使用场景 | 版本控制    | 协作追溯     |

建议在重要变更时同时使用 Git commit 和 DevLog 记录。

***
## 注意！
本项目完全由AI生成，当前版本未进行任何调试完善，如需直接使用请自行注意风险控制代码审计或期待后续版本推进。
## 许可证

MIT License
