# N0mosAi - API 文档

> 版本: 1.0
> 最后更新: 2026-02-25
> 状态: Draft

本文档定义了 Nomos 系统的所有 API 接口规范，包括 Task Viewer HTTP API、WebSocket 通信协议和内部接口。

---

## 目录

1. [概述](#1-概述)
2. [Task Viewer HTTP API](#2-task-viewer-http-api)
3. [WebSocket 通信协议](#3-websocket-通信协议)
4. [内部接口](#4-内部接口)
5. [SKILL 命令接口](#5-skill-命令接口)
6. [数据结构](#6-数据结构)
7. [错误处理](#7-错误处理)

---

## 1. 概述

### 1.1 API 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API 架构总览                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐         ┌─────────────────────────────────┐   │
│  │ Task Viewer     │         │ Python 后端服务器               │   │
│  │ Frontend        │◄───────►│ (localhost:8765)                │   │
│  │ (Browser)       │  HTTP   │                                 │   │
│  │                 │  WS     │  ┌─────────────────────────┐    │   │
│  │  - marked.js    │         │  │ HTTP 服务层             │    │   │
│  │  - mermaid.js   │         │  │ - 静态文件服务          │    │   │
│  │  - 标注交互     │         │  │ - REST API 端点         │    │   │
│  └─────────────────┘         │  │ - WebSocket 服务        │    │   │
│                              │  └─────────────────────────┘    │   │
│                              │  ┌─────────────────────────┐    │   │
│                              │  │ 文件操作层              │    │   │
│                              │  │ - 读取 MD 文件          │    │   │
│                              │  │ - 保存 MD 文件          │    │   │
│                              │  │ - 解析 YAML Frontmatter │    │   │
│                              │  └─────────────────────────┘    │   │
│                              └─────────────────────────────────┘   │
│                                              │                      │
│                                              ▼                      │
│                              ┌─────────────────────────────────┐   │
│                              │ 任务文件系统                     │   │
│                              │ tasks/t1-YYYY-MM-DD-feature/     │   │
│                              │ ├── plan.md                      │   │
│                              │ ├── research.md                  │   │
│                              │ └── code_review.md               │   │
│                              └─────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 基础信息

| 项目 | 值 |
|------|-----|
| **Base URL** | `http://localhost:8765` |
| **API 前缀** | `/api` |
| **协议** | HTTP/1.1, WebSocket |
| **数据格式** | JSON |
| **字符编码** | UTF-8 |

### 1.3 端口管理

| 策略 | 说明 |
|------|------|
| **起始端口** | 8765 |
| **冲突处理** | 自动递增 (8766, 8767, ...) |
| **多实例** | 每个任务可使用独立端口 |
| **自动关闭** | 30 分钟无活动自动关闭 |

---

## 2. Task Viewer HTTP API

### 2.1 API 端点总览

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 获取 Task Viewer 主页面 |
| GET | `/api/task` | 获取当前任务信息 |
| GET | `/api/file/{filename}` | 读取指定文件内容 |
| PUT | `/api/file/{filename}` | 保存文件内容 |
| GET | `/api/file/{filename}/mtime` | 获取文件修改时间 |
| POST | `/api/annotations` | 创建/更新标注 |
| DELETE | `/api/annotations/{rc_id}` | 删除标注 |
| GET | `/api/annotations` | 获取所有标注 |
| POST | `/api/annotations/{rc_id}/reply` | 回复标注（追加历史） |

---

### 2.2 获取主页面

获取 Task Viewer HTML 页面。

**请求**

```http
GET / HTTP/1.1
Host: localhost:8765
```

**响应**

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
<head>
    <title>Task Viewer - t1-2026-02-25-user-login</title>
    ...
</head>
<body>
    ...
</body>
</html>
```

---

### 2.3 获取任务信息

获取当前任务的基本信息。

**请求**

```http
GET /api/task HTTP/1.1
Host: localhost:8765
```

**响应**

```json
{
  "task_id": "t1",
  "full_id": "t1-2026-02-25-user-login",
  "path": "tasks/t1-2026-02-25-user-login",
  "status": "executing",
  "current_phase": "Phase 2",
  "created": "2026-02-25T10:30:00",
  "updated": "2026-02-25T14:45:00",
  "files": {
    "research": "research.md",
    "plan": "plan.md",
    "code_review": "code_review.md",
    "progress": "progress.md"
  },
  "review_stats": {
    "total": 3,
    "pending": 1,
    "pending_ai_question": 1,
    "addressed": 1
  }
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 短 ID (如 t1, t2) |
| `full_id` | string | 完整 ID (如 t1-2026-02-25-user-login) |
| `path` | string | 任务文件夹路径 |
| `status` | string | 任务状态 |
| `current_phase` | string | 当前执行阶段 |
| `created` | string | 创建时间 (ISO 8601) |
| `updated` | string | 最后更新时间 (ISO 8601) |
| `files` | object | 关联文件列表 |
| `review_stats` | object | Review Comments 统计 |

---

### 2.4 读取文件内容

读取指定文件的内容。

**请求**

```http
GET /api/file/{filename} HTTP/1.1
Host: localhost:8765
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| `filename` | string | 文件名 (research.md, plan.md, code_review.md, progress.md) |

**响应**

```json
{
  "filename": "plan.md",
  "content": "# Plan: 用户登录功能\n\n---\ntask_id: t1\nstatus: executing\n---\n\n## 1. 目标与范围\n...",
  "mtime": "2026-02-25T14:45:00",
  "size": 4521,
  "frontmatter": {
    "task_id": "t1",
    "status": "executing",
    "created": "2026-02-25T10:30:00"
  }
}
```

**错误响应**

```json
{
  "code": "FILE_NOT_FOUND",
  "message": "文件不存在",
  "details": {
    "filename": "nonexistent.md"
  }
}
```

---

### 2.5 保存文件内容

保存文件内容。

**请求**

```http
PUT /api/file/{filename} HTTP/1.1
Host: localhost:8765
Content-Type: application/json

{
  "content": "# Plan: 用户登录功能\n\n---\ntask_id: t1\nstatus: executing\n---\n\n## 1. 目标与范围\n..."
}
```

**请求体字段**

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `content` | string | 是 | 文件完整内容 |

**响应**

```json
{
  "success": true,
  "filename": "plan.md",
  "mtime": "2026-02-25T15:00:00",
  "size": 4580,
  "frontmatter": {
    "task_id": "t1",
    "status": "executing",
    "updated": "2026-02-25T15:00:00"
  }
}
```

---

### 2.6 获取文件修改时间

获取文件的最后修改时间，用于轮询检测文件变化。

**请求**

```http
GET /api/file/{filename}/mtime HTTP/1.1
Host: localhost:8765
```

**响应**

```json
{
  "filename": "plan.md",
  "mtime": "2026-02-25T15:00:00",
  "changed": true
}
```

**查询参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| `since` | string | 上次已知修改时间 (ISO 8601)，用于比较是否变化 |

**示例**

```http
GET /api/file/plan.md/mtime?since=2026-02-25T14:45:00 HTTP/1.1
```

---

### 2.7 创建/更新标注

创建新的 Review Comment 或更新现有标注。

**请求**

```http
POST /api/annotations HTTP/1.1
Host: localhost:8765
Content-Type: application/json

{
  "file": "plan.md",
  "location": {
    "type": "line",
    "line": 47
  },
  "severity": "MAJOR",
  "content": "需要补充微信登录的边界条件，如用户取消授权、网络超时等场景",
  "author": "developer"
}
```

**请求体字段**

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file` | string | 是 | 目标文件名 |
| `rc_id` | string | 否 | 更新时提供 (如 RC-1) |
| `location` | object | 是 | 位置信息 |
| `severity` | string | 是 | 严重程度 (CRITICAL/MAJOR/MINOR/SUGGEST/REVERT) |
| `content` | string | 是 | 标注内容 |
| `author` | string | 是 | 作者标识 |

**Location 对象**

| 类型 | 字段 | 示例 |
|------|------|------|
| `line` | `line` | `{"type": "line", "line": 47}` |
| `code` | `block_index`, `line_in_block`, `source_line` | `{"type": "code", "block_index": 1, "line_in_block": 3, "source_line": 50}` |
| `mermaid` | `block_index`, `source_start`, `source_end` | `{"type": "mermaid", "block_index": 1, "source_start": 55, "source_end": 60}` |
| `table` | `table_index`, `row`, `source_line` | `{"type": "table", "table_index": 1, "row": 2, "source_line": 65}` |

**响应**

```json
{
  "success": true,
  "rc_id": "RC-1",
  "annotation": {
    "id": "RC-1",
    "title": "需要补充微信登录的边界条件",
    "location": {
      "type": "line",
      "line": 47
    },
    "created": "2026-02-25T15:00:00",
    "updated": "2026-02-25T15:00:00",
    "severity": "MAJOR",
    "status": "pending",
    "history": [
      {
        "time": "2026-02-25T15:00:00",
        "author": "developer",
        "type": "user",
        "content": "需要补充微信登录的边界条件，如用户取消授权、网络超时等场景"
      }
    ]
  }
}
```

---

### 2.8 删除标注

删除指定的 Review Comment。

**请求**

```http
DELETE /api/annotations/{rc_id} HTTP/1.1
Host: localhost:8765
Query: file=plan.md
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| `rc_id` | string | 标注 ID (如 RC-1) |

**查询参数**

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file` | string | 是 | 目标文件名 |

**响应**

```json
{
  "success": true,
  "rc_id": "RC-1",
  "message": "标注已删除"
}
```

---

### 2.9 获取所有标注

获取指定文件的所有 Review Comments。

**请求**

```http
GET /api/annotations?file=plan.md HTTP/1.1
Host: localhost:8765
```

**查询参数**

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file` | string | 是 | 目标文件名 |
| `status` | string | 否 | 按状态过滤 |

**响应**

```json
{
  "file": "plan.md",
  "total": 3,
  "annotations": [
    {
      "id": "RC-1",
      "title": "需要补充微信登录的边界条件",
      "location": {
        "type": "line",
        "line": 47
      },
      "created": "2026-02-25T15:00:00",
      "updated": "2026-02-25T15:30:00",
      "severity": "MAJOR",
      "status": "pending_ai_question",
      "history": [
        {
          "time": "2026-02-25T15:00:00",
          "author": "developer",
          "type": "user",
          "content": "需要补充微信登录的边界条件..."
        },
        {
          "time": "2026-02-25T15:15:00",
          "author": "agent",
          "type": "agent",
          "content": "已在 Phase Gates 中补充 Gate 1.4..."
        },
        {
          "time": "2026-02-25T15:16:00",
          "author": "agent",
          "type": "ai_question",
          "content": "请确认：微信服务不可用时是否需要降级处理？"
        }
      ]
    },
    {
      "id": "RC-2",
      "title": "数据库表设计建议",
      "location": {
        "type": "line",
        "line": 52
      },
      "severity": "MINOR",
      "status": "addressed"
    }
  ]
}
```

---

### 2.10 回复标注

在标注历史中追加回复。

**请求**

```http
POST /api/annotations/{rc_id}/reply HTTP/1.1
Host: localhost:8765
Content-Type: application/json

{
  "file": "plan.md",
  "author": "developer",
  "type": "user",
  "content": "是的，需要降级。降级方案：显示"微信服务暂时不可用，请使用手机号登录""
}
```

**请求体字段**

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file` | string | 是 | 目标文件名 |
| `author` | string | 是 | 作者标识 |
| `type` | string | 是 | 类型 (user/agent/ai_question) |
| `content` | string | 是 | 回复内容 |
| `update_status` | string | 否 | 更新状态 |

**响应**

```json
{
  "success": true,
  "rc_id": "RC-1",
  "history_entry": {
    "time": "2026-02-25T16:00:00",
    "author": "developer",
    "type": "user",
    "content": "是的，需要降级。降级方案：显示"微信服务暂时不可用，请使用手机号登录""
  },
  "new_status": "pending"
}
```

---

## 3. WebSocket 通信协议

### 3.1 连接

**连接端点**

```
ws://localhost:8765/ws
```

**连接示例**

```javascript
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onopen = () => {
  console.log('WebSocket 连接已建立');
  // 发送心跳
  ws.send(JSON.stringify({ type: 'ping' }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};
```

### 3.2 消息类型

#### 3.2.1 客户端 → 服务器

| 类型 | 描述 | 用途 |
|------|------|------|
| `ping` | 心跳 | 保持连接活跃 |
| `browser_close` | 浏览器关闭通知 | 服务器优雅关闭 |
| `subscribe` | 订阅文件变化 | 监听特定文件变化 |

**心跳消息**

```json
{
  "type": "ping"
}
```

**浏览器关闭通知**

```json
{
  "type": "browser_close",
  "task_id": "t1"
}
```

**订阅文件变化**

```json
{
  "type": "subscribe",
  "files": ["plan.md", "research.md"]
}
```

#### 3.2.2 服务器 → 客户端

| 类型 | 描述 | 用途 |
|------|------|------|
| `pong` | 心跳响应 | 确认连接正常 |
| `file_changed` | 文件变化通知 | 触发内容刷新 |
| `annotation_updated` | 标注更新通知 | 实时同步标注状态 |

**心跳响应**

```json
{
  "type": "pong",
  "time": "2026-02-25T16:00:00"
}
```

**文件变化通知**

```json
{
  "type": "file_changed",
  "file": "plan.md",
  "mtime": "2026-02-25T16:00:00",
  "source": "agent"
}
```

**标注更新通知**

```json
{
  "type": "annotation_updated",
  "file": "plan.md",
  "rc_id": "RC-1",
  "status": "pending_ai_question",
  "has_ai_question": true
}
```

### 3.3 通信流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WebSocket 通信流程                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Frontend                          Backend                           │
│     │                                │                               │
│     │──── WebSocket 连接 ───────────►│                               │
│     │                                │                               │
│     │──── ping (每 30s) ────────────►│                               │
│     │◄─── pong ──────────────────────│                               │
│     │                                │                               │
│     │──── subscribe ────────────────►│                               │
│     │     ["plan.md"]                │                               │
│     │                                │                               │
│     │                                │   [Agent 修改 plan.md]        │
│     │                                │                               │
│     │◄─── file_changed ──────────────│                               │
│     │     {"file": "plan.md"}        │                               │
│     │                                │                               │
│     │──── GET /api/file/plan.md ────►│  (重新获取内容)               │
│     │◄─── 文件内容 ──────────────────│                               │
│     │                                │                               │
│     │     [用户关闭浏览器]           │                               │
│     │                                │                               │
│     │──── browser_close ────────────►│                               │
│     │                                │                               │
│     │                                │── 优雅关闭服务器              │
│     │                                │                               │
│     X                                X                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 内部接口

### 4.1 Why-First 引擎接口

#### generate_why_questions()

生成 Why 问题列表。

**函数签名**

```python
def generate_why_questions(
    requirement: str,
    project_why_path: str,
    affected_modules: List[str]
) -> List[WhyQuestion]:
    """
    生成 Why 问题列表

    Args:
        requirement: 需求描述
        project_why_path: project-why.md 文件路径
        affected_modules: 受影响的模块列表

    Returns:
        Why 问题列表
    """
    pass
```

**返回结构**

```python
@dataclass
class WhyQuestion:
    id: str                    # WHY-001
    question: str              # 为什么 Auth 使用 Redis 缓存？
    module: str                # Auth
    source: str                # project-why.md L47 / 新增
    ai_understanding: str      # AI 的初步理解
    needs_confirmation: bool   # 是否需要人类确认
```

#### update_project_why()

更新 project-why.md 知识库。

**函数签名**

```python
def update_project_why(
    project_why_path: str,
    new_entries: List[WhyEntry],
    task_id: str
) -> bool:
    """
    更新 project-why.md

    Args:
        project_why_path: project-why.md 文件路径
        new_entries: 新的知识条目
        task_id: 来源任务 ID

    Returns:
        是否更新成功
    """
    pass
```

---

### 4.2 Task 状态管理器接口

#### create_task()

创建新任务。

**函数签名**

```python
def create_task(
    task_name: str,
    task_type: str = "feat"
) -> TaskInfo:
    """
    创建新任务

    Args:
        task_name: 任务名称
        task_type: 任务类型 (feat/fix/refactor/test/docs)

    Returns:
        任务信息
    """
    pass
```

**返回结构**

```python
@dataclass
class TaskInfo:
    task_id: str           # t1
    full_id: str           # t1-2026-02-25-user-login
    path: str              # tasks/t1-2026-02-25-user-login
    branch_name: str       # feat/2026-02-25-user-login
    created: datetime
```

#### switch_task()

切换任务上下文。

**函数签名**

```python
def switch_task(
    task_id: str
) -> TaskContext:
    """
    切换任务

    Args:
        task_id: 目标任务 ID (t1 或完整 ID)

    Returns:
        任务上下文
    """
    pass
```

#### get_current_task()

获取当前任务。

**函数签名**

```python
def get_current_task() -> Optional[TaskInfo]:
    """
    获取当前任务

    Returns:
        当前任务信息，如果没有则返回 None
    """
    pass
```

---

### 4.3 Agent Linter Engine 接口

#### run_linter()

运行 Linter 检查。

**函数签名**

```python
def run_linter(
    file_path: str,
    content: str,
    rules: List[str] = None
) -> LinterResult:
    """
    运行 Linter 检查

    Args:
        file_path: 文件路径
        content: 文件内容
        rules: 指定规则列表 (None 表示全部)

    Returns:
        Linter 检查结果
    """
    pass
```

**返回结构**

```python
@dataclass
class LinterResult:
    passed: bool
    errors: List[LinterError]
    warnings: List[LinterWarning]

@dataclass
class LinterError:
    rule: str              # 规则名称
    message: str           # 错误消息
    line: int              # 行号
    column: int            # 列号
    severity: str          # error/warning
    suggestion: str        # 修复建议
```

---

### 4.4 Validator Subagent 接口

#### validate_plan()

验证 plan.md 设计。

**函数签名**

```python
async def validate_plan(
    plan_path: str,
    research_path: str
) -> ValidationResult:
    """
    验证 plan.md 设计

    Args:
        plan_path: plan.md 文件路径
        research_path: research.md 文件路径

    Returns:
        验证结果
    """
    pass
```

**返回结构**

```python
@dataclass
class ValidationResult:
    score: int                    # 0-100
    passed: bool                  # 是否通过 (>=70)
    issues: List[ValidationIssue]
    suggestions: List[str]

@dataclass
class ValidationIssue:
    type: str              # architecture/logic/missing/risk
    severity: str          # critical/major/minor
    location: str          # 位置描述
    description: str       # 问题描述
    suggestion: str        # 建议
```

---

## 5. SKILL 命令接口

### 5.1 命令列表

| 命令 | 功能 | 参数 |
|------|------|------|
| `/nomos` | 显示帮助 | 无 |
| `/nomos:start` | 启动新任务 | `[task_name]` |
| `/nomos:new-task` | 创建任务文件夹 | `<task_name>` |
| `/nomos:research` | 执行 Research 阶段 | 无 |
| `/nomos:plan` | 执行 Plan 阶段 | 无 |
| `/nomos:execute` | 执行 Execute 阶段 | 无 |
| `/nomos:view-task` | 启动 Task Viewer | `[task_id]` |
| `/nomos:list-tasks` | 列出所有任务 | `[--status=...] [--recent=N]` |
| `/nomos:switch-task` | 切换任务 | `<task_id>` |
| `/nomos:update-why` | 更新 project-why.md | 无 |
| `/nomos:update-diagram` | 更新 Mermaid 图 | 无 |
| `/nomos:archive` | 归档任务 | `[task_id]` |
| `/nomos:validate` | 触发验证 | 无 |

### 5.2 命令详细说明

#### /nomos:start

启动完整的 Why-First 流程。

**流程**

```
1. Why-First 阶段: 生成 Why 问题
2. Research 阶段: 生成 research.md
3. Plan 阶段: 生成 plan.md
4. Execute 阶段: 开始编码实现
```

**示例**

```
/nomos:start 实现用户登录功能
```

#### /nomos:view-task

启动 Task Viewer 服务器并打开浏览器。

**参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 可选，默认当前任务 |

**示例**

```
/nomos:view-task
/nomos:view-task t2
```

#### /nomos:list-tasks

列出所有任务及其状态。

**参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| `--status` | string | 按状态过滤 |
| `--recent` | int | 只显示最近 N 天的任务 |

**示例**

```
/nomos:list-tasks
/nomos:list-tasks --status=executing
/nomos:list-tasks --recent=7
```

**输出示例**

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 Task List (共 5 个任务)                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🔵 执行中                                                           │
│  ├── t1-2026-02-25-user-login        [executing]   Phase 2/3       │
│  └── t3-2026-02-24-payment-api       [executing]   Phase 1/2       │
│                                                                      │
│  🟡 等待中                                                           │
│  └── t2-2026-02-23-auth-refactor     [needs_replan] 等待重新规划    │
│                                                                      │
│  ✅ 已完成                                                           │
│  ├── t4-2026-02-20-logger-fix        [done]        PR #42          │
│  └── t5-2026-02-18-db-migration      [archived]    2026-02-20      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### /nomos:validate

触发验证检查，显示标注状态。

**输出示例**

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔍 标注状态检查                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📋 research.md                                                      │
│  ├── RC-1: [MAJOR] addressed ✅                                     │
│  └── RC-2: [MINOR] addressed ✅                                     │
│  结果: ✅ 可以进入 Plan 阶段                                         │
│                                                                      │
│  📋 plan.md                                                          │
│  ├── RC-1: [MAJOR] pending_ai_question ❓                           │
│  ├── RC-2: [CRITICAL] pending ⚠️                                    │
│  └── RC-3: [MINOR] addressed ✅                                     │
│  结果: ❌ 还有 2 个待处理标注，无法进入 Execute 阶段                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. 数据结构

### 6.1 Review Comment

```typescript
interface ReviewComment {
  id: string;                        // RC-1
  title: string;                     // 批注标题
  location: Location;                // 位置信息
  created: string;                   // ISO 8601
  updated: string;                   // ISO 8601
  severity: Severity;                // 严重程度
  status: ReviewStatus;              // 状态
  history: HistoryEntry[];           // 标注历史
}

interface Location {
  type: 'line' | 'code' | 'mermaid' | 'table';
  line?: number;
  block_index?: number;
  line_in_block?: number;
  source_line?: number;
  source_start?: number;
  source_end?: number;
  table_index?: number;
  row?: number;
}

type Severity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'SUGGEST' | 'REVERT';

type ReviewStatus =
  | 'pending'
  | 'pending_ai_question'
  | 'pending_user_clarify'
  | 'addressed'
  | 'wont_fix';

interface HistoryEntry {
  time: string;                      // ISO 8601
  author: string;                    // 作者标识
  type: 'user' | 'agent' | 'ai_question';
  content: string;                   // 内容
}
```

### 6.2 Task Info

```typescript
interface TaskInfo {
  task_id: string;                   // t1
  full_id: string;                   // t1-2026-02-25-user-login
  path: string;                      // tasks/t1-2026-02-25-user-login
  status: TaskStatus;
  current_phase: string;
  created: string;
  updated: string;
  files: TaskFiles;
  review_stats: ReviewStats;
}

type TaskStatus =
  | 'draft'
  | 'in_review'
  | 'approved'
  | 'executing'
  | 'needs_replan'
  | 'done'
  | 'archived';

interface TaskFiles {
  research: string;
  plan: string;
  code_review: string;
  progress: string;
}

interface ReviewStats {
  total: number;
  pending: number;
  pending_ai_question: number;
  pending_user_clarify: number;
  addressed: number;
  wont_fix: number;
}
```

### 6.3 Short ID Mapping

```typescript
interface ShortIdMapping {
  [shortId: string]: {
    full_id: string;
    path: string;
    status: TaskStatus;
    archived: boolean;
  };
}
```

**JSON 示例**

```json
{
  "t1": {
    "full_id": "t1-2026-02-25-user-login",
    "path": "tasks/t1-2026-02-25-user-login",
    "status": "executing",
    "archived": false
  },
  "t2": {
    "full_id": "t2-2026-02-24-payment-fix",
    "path": "tasks/archive/2026-02/t2-2026-02-24-payment-fix",
    "status": "archived",
    "archived": true
  }
}
```

---

## 7. 错误处理

### 7.1 标准错误格式

所有 API 错误返回统一的格式：

```json
{
  "code": "ERROR_CODE",
  "message": "人类可读的错误描述",
  "details": {
    "key": "value"
  }
}
```

### 7.2 错误码列表

| 错误码 | HTTP 状态码 | 描述 |
|--------|------------|------|
| `FILE_NOT_FOUND` | 404 | 文件不存在 |
| `INVALID_FILE_TYPE` | 400 | 不支持的文件类型 |
| `PARSE_ERROR` | 400 | 文件解析失败 |
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `ANNOTATION_NOT_FOUND` | 404 | 标注不存在 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
| `WEBSOCKET_ERROR` | 500 | WebSocket 连接错误 |

### 7.3 错误响应示例

**文件不存在**

```json
{
  "code": "FILE_NOT_FOUND",
  "message": "文件不存在",
  "details": {
    "filename": "nonexistent.md",
    "task_id": "t1"
  }
}
```

**验证失败**

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数验证失败",
  "details": {
    "field": "severity",
    "value": "INVALID",
    "allowed_values": ["CRITICAL", "MAJOR", "MINOR", "SUGGEST", "REVERT"]
  }
}
```

**解析错误**

```json
{
  "code": "PARSE_ERROR",
  "message": "YAML Frontmatter 解析失败",
  "details": {
    "filename": "plan.md",
    "line": 5,
    "error": "Invalid YAML syntax"
  }
}
```

---

## 附录

### A. cURL 示例

**获取任务信息**

```bash
curl http://localhost:8765/api/task
```

**读取文件**

```bash
curl http://localhost:8765/api/file/plan.md
```

**保存文件**

```bash
curl -X PUT http://localhost:8765/api/file/plan.md \
  -H "Content-Type: application/json" \
  -d '{"content": "# Plan: ..."}'
```

**创建标注**

```bash
curl -X POST http://localhost:8765/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "file": "plan.md",
    "location": {"type": "line", "line": 47},
    "severity": "MAJOR",
    "content": "需要补充边界条件",
    "author": "developer"
  }'
```

### B. JavaScript 客户端示例

```javascript
class TaskViewerClient {
  constructor(baseUrl = 'http://localhost:8765') {
    this.baseUrl = baseUrl;
    this.ws = null;
  }

  // 获取任务信息
  async getTask() {
    const response = await fetch(`${this.baseUrl}/api/task`);
    return response.json();
  }

  // 读取文件
  async getFile(filename) {
    const response = await fetch(`${this.baseUrl}/api/file/${filename}`);
    return response.json();
  }

  // 保存文件
  async saveFile(filename, content) {
    const response = await fetch(`${this.baseUrl}/api/file/${filename}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    return response.json();
  }

  // 创建标注
  async createAnnotation(file, location, severity, content, author) {
    const response = await fetch(`${this.baseUrl}/api/annotations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file, location, severity, content, author })
    });
    return response.json();
  }

  // 连接 WebSocket
  connectWebSocket(onFileChanged, onAnnotationUpdated) {
    this.ws = new WebSocket(`ws://${this.baseUrl.split('//')[1]}/ws`);

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'file_changed' && onFileChanged) {
        onFileChanged(message);
      } else if (message.type === 'annotation_updated' && onAnnotationUpdated) {
        onAnnotationUpdated(message);
      }
    };

    // 心跳
    setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  // 关闭连接
  close() {
    if (this.ws) {
      this.ws.send(JSON.stringify({ type: 'browser_close' }));
      this.ws.close();
    }
  }
}
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-02-25 | 初始版本，基于架构文档生成 |
