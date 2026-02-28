# Task Manager 模块详解

> 本文档深入讲解 nOmOsAi 任务管理系统的设计理念、架构实现和代码细节。

---

## 1. 概述

### 1.1 设计目标

任务管理系统（Task Manager）是 nOmOsAi 工作流框架的核心基础设施，旨在解决 AI Agent 编码过程中的以下痛点：

| 痛点 | 解决方案 |
|------|----------|
| 多次迭代需求容易混淆 | Task 文件夹隔离，每个任务独立空间 |
| 上下文丢失，需反复解释 | 状态持久化在 Markdown 文件中，支持跨会话恢复 |
| 任务引用繁琐 | Short ID 系统（t1, t2, t3...）简化引用 |
| 无法并行开发多任务 | 独立分支 + 快照机制支持任务切换 |

**核心价值主张**：

1. **零上下文污染** - 每个任务独立文件夹，Agent 专注当前任务
2. **跨会话持久** - 状态在 MD 文件里积累，关闭重开自动恢复
3. **人机分工明确** - 人类只做高阶决策，Agent 专注执行

### 1.2 核心文件

| 文件路径 | 职责 |
|----------|------|
| `.claude/hooks/lib/task_manager.py` | 任务状态管理器核心实现 |
| `.claude/hooks/lib/phase_manager.py` | 阶段状态管理（Research/Plan/Execute/Review） |
| `.claude/hooks/lib/utils.py` | 通用工具函数 |
| `tasks/short-id-mapping.json` | 短 ID 到完整任务路径的映射 |
| `.claude/current-task.txt` | 当前活跃任务路径 |

---

## 2. 系统架构设计

### 2.1 架构文档中的设计要求

根据 `03_System_Architecture.md` 第 3.4 节，Task 状态管理器的设计要求：

**职责**：
- 创建/切换任务文件夹
- 维护 short ID 映射
- 保存/恢复任务上下文
- 管理任务快照（并行任务切换）

**状态文件结构**：

```
tasks/t1-2026-02-23-feature/
├── research.md          # 调研文档
├── plan.md              # 计划文档
├── code_review.md       # 审查文档
├── .task-viewer.html    # 查看器界面
├── snapshot.md          # 上下文快照(切换任务时)
└── plan-diagram.mmd     # Mermaid 流程图
```

### 2.2 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Task Manager 架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      用户交互层                                 │ │
│  │  /nomos:start → 创建任务                                       │ │
│  │  /nomos:switch-task → 切换任务                                  │ │
│  │  /nomos:list-tasks → 列出任务                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   TaskManager 核心                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ create_task  │  │ get_current  │  │ list_tasks   │         │ │
│  │  │              │  │ _task        │  │              │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ _next_short  │  │ _load/save   │  │ _init_       │         │ │
│  │  │ _id          │  │ _mapping     │  │ templates    │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     持久化层                                    │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  tasks/                                                   │  │ │
│  │  │  ├── t1-2026-02-25-user-login/                           │  │ │
│  │  │  │   ├── research.md                                     │  │ │
│  │  │  │   ├── plan.md                                         │  │ │
│  │  │  │   ├── code_review.md                                  │  │ │
│  │  │  │   └── phase_state.json                                │  │ │
│  │  │  ├── t2-2026-02-26-payment-api/                          │  │ │
│  │  │  └── short-id-mapping.json                               │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  .claude/                                                │  │ │
│  │  │  └── current-task.txt                                    │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 与其他模块的交互

```
┌──────────────────┐    创建任务     ┌──────────────────┐
│   SKILL Layer    │ ──────────────► │   TaskManager    │
│  /nomos:start    │                 │                  │
└──────────────────┘                 └────────┬─────────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     │                        │                        │
                     ▼                        ▼                        ▼
           ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
           │  PhaseManager    │     │   GitManager     │     │  TaskViewer      │
           │  初始化阶段状态   │     │   创建分支       │     │  生成 HTML 界面   │
           └──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## 3. 代码实现详解

### 3.1 核心数据结构：TaskInfo

**文件**: `.claude/hooks/lib/task_manager.py:19-27`

```python
@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str           # t1
    full_id: str           # t1-2026-02-26-user-login
    path: str              # tasks/t1-2026-02-26-user-login
    status: str            # draft/in_review/approved/executing/done
    created: str           # ISO 8601
```

**设计说明**：

| 字段 | 用途 | 示例值 |
|------|------|--------|
| `task_id` | 短 ID，用于快速引用 | `t1`, `t2` |
| `full_id` | 完整 ID，包含日期和名称 | `t1-2026-02-26-user-login` |
| `path` | 相对于项目根目录的路径 | `tasks/t1-2026-02-26-user-login` |
| `status` | 任务当前状态 | `draft` / `in_review` / `approved` / `executing` / `done` |
| `created` | 创建时间（ISO 8601 格式） | `2026-02-26T10:30:00.123456` |

### 3.2 TaskManager 类常量定义

**文件**: `.claude/hooks/lib/task_manager.py:29-36`

```python
class TaskManager:
    """Task 状态管理器"""

    TASKS_DIR = "tasks"
    MAPPING_FILE = "tasks/short-id-mapping.json"
    CURRENT_TASK_FILE = ".claude/current-task.txt"
    TEMPLATES_DIR = ".claude/skills/nomos/templates"
```

**目录结构映射**：

```
project_root/
├── tasks/                          # TASKS_DIR
│   ├── short-id-mapping.json       # MAPPING_FILE
│   ├── t1-2026-02-25-feature/
│   └── t2-2026-02-26-bugfix/
└── .claude/
    ├── current-task.txt            # CURRENT_TASK_FILE
    └── skills/nomos/templates/     # TEMPLATES_DIR
        ├── research.md
        ├── plan.md
        ├── code_review.md
        └── progress.md
```

### 3.3 初始化方法

**文件**: `.claude/hooks/lib/task_manager.py:37-48`

```python
def __init__(self, project_root: Optional[str] = None):
    """
    初始化 TaskManager

    Args:
        project_root: 项目根目录，默认为当前目录
    """
    self.project_root = Path(project_root or os.getcwd())
    self.tasks_dir = self.project_root / self.TASKS_DIR
    self.mapping_file = self.project_root / self.MAPPING_FILE
    self.current_task_file = self.project_root / self.CURRENT_TASK_FILE
    self.templates_dir = self.project_root / self.TEMPLATES_DIR
```

**设计要点**：
- 使用 `pathlib.Path` 提供跨平台路径处理
- 默认使用 `os.getcwd()` 获取当前工作目录
- 所有路径都相对于 `project_root` 计算

### 3.4 创建任务：create_task()

**文件**: `.claude/hooks/lib/task_manager.py:50-100`

```python
def create_task(self, task_name: str, task_type: str = "feat") -> TaskInfo:
    """
    创建新任务文件夹并初始化四件套

    Args:
        task_name: 任务名称 (如 user-login)
        task_type: 任务类型 (feat/fix/refactor/test/docs)

    Returns:
        TaskInfo 对象
    """
    # 1. 分配短 ID
    task_id = self._next_short_id()

    # 2. 生成完整 ID
    date_str = datetime.now().strftime("%Y-%m-%d")
    full_id = f"{task_id}-{date_str}-{task_name}"

    # 3. 创建目录
    task_path = self.tasks_dir / full_id
    task_path.mkdir(parents=True, exist_ok=True)

    # 4. 初始化四件套（从模板复制）
    created_time = datetime.now().isoformat()
    task_info = TaskInfo(
        task_id=task_id,
        full_id=full_id,
        path=str(task_path.relative_to(self.project_root)),
        status="draft",
        created=created_time
    )
    self._init_templates(task_path, task_info)

    # 5. 更新映射文件
    mapping = self._load_mapping()
    mapping[task_id] = {
        "full_id": full_id,
        "path": task_info.path,
        "status": "draft",
        "archived": False,
        "created": created_time
    }
    self._save_mapping(mapping)

    # 6. 初始化阶段状态文件
    self._init_phase_state(task_path, task_info)

    # 7. 设置当前任务
    self.set_current_task(task_id)

    return task_info
```

**执行流程图**：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      create_task 执行流程                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: 分配短 ID                                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ _next_short_id() → 读取 mapping → 找最大 ID + 1 → 返回 "tN"    │ │
│  │ 例: t1, t2 存在 → 返回 t3                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Step 2: 生成完整 ID                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ full_id = "{task_id}-{date}-{task_name}"                       │ │
│  │ 例: "t3-2026-02-26-user-login"                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Step 3: 创建目录                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ mkdir -p tasks/t3-2026-02-26-user-login/                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Step 4: 初始化四件套                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 从模板复制: research.md, plan.md, code_review.md, progress.md  │ │
│  │ 替换占位符: {TASK_ID}, {FULL_ID}, {CREATED}, {STATUS}          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Step 5: 更新映射文件                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ short-id-mapping.json:                                         │ │
│  │ {                                                              │ │
│  │   "t3": {                                                      │ │
│  │     "full_id": "t3-2026-02-26-user-login",                     │ │
│  │     "path": "tasks/t3-2026-02-26-user-login",                  │ │
│  │     "status": "draft",                                         │ │
│  │     "archived": false                                          │ │
│  │   }                                                            │ │
│  │ }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Step 6: 初始化阶段状态                                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ PhaseManager.initialize() → phase_state.json                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Step 7: 设置当前任务                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ echo "tasks/t3-2026-02-26-user-login" > .claude/current-task.txt│ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.5 短 ID 分配：_next_short_id()

**文件**: `.claude/hooks/lib/task_manager.py:157-173`

```python
def _next_short_id(self) -> str:
    """分配下一个可用短 ID (t1, t2, ...)"""
    mapping = self._load_mapping()
    if not mapping:
        return "t1"

    # 提取所有数字 ID
    ids = []
    for key in mapping.keys():
        if key.startswith("t"):
            try:
                ids.append(int(key[1:]))
            except ValueError:
                continue

    next_id = max(ids) + 1 if ids else 1
    return f"t{next_id}"
```

**算法说明**：
1. 加载现有映射
2. 提取所有 `t{数字}` 格式的 ID
3. 找到最大数字并加 1
4. 返回新的短 ID

### 3.6 模板初始化：_init_templates()

**文件**: `.claude/hooks/lib/task_manager.py:192-216`

```python
def _init_templates(self, task_path: Path, task_info: TaskInfo) -> None:
    """从模板初始化四件套，替换占位符"""
    placeholders = {
        "{TASK_ID}": task_info.task_id,
        "{FULL_ID}": task_info.full_id,
        "{CREATED}": task_info.created,
        "{STATUS}": "draft",
        "{TASK_NAME}": "-".join(task_info.full_id.split("-")[3:])
                       if len(task_info.full_id.split("-")) > 3 else ""
    }

    template_files = ["research.md", "plan.md", "code_review.md", "progress.md"]

    for template_name in template_files:
        src = self.templates_dir / template_name
        dst = task_path / template_name

        if src.exists():
            content = src.read_text()
            for key, value in placeholders.items():
                content = content.replace(key, value)
            dst.write_text(content)
        else:
            # 如果模板不存在，创建基础模板
            dst.write_text(self._get_default_template(template_name, task_info))
```

**占位符说明**：

| 占位符 | 替换为 | 示例 |
|--------|--------|------|
| `{TASK_ID}` | 短 ID | `t3` |
| `{FULL_ID}` | 完整 ID | `t3-2026-02-26-user-login` |
| `{CREATED}` | 创建时间 | `2026-02-26T10:30:00` |
| `{STATUS}` | 初始状态 | `draft` |
| `{TASK_NAME}` | 任务名称 | `user-login` |

### 3.7 获取当前任务：get_current_task()

**文件**: `.claude/hooks/lib/task_manager.py:102-128`

```python
def get_current_task(self) -> Optional[TaskInfo]:
    """读取 current-task.txt 获取当前任务"""
    if not self.current_task_file.exists():
        return None

    task_path_str = self.current_task_file.read_text().strip()
    if not task_path_str:
        return None

    # 从路径提取 task_id
    task_path = Path(task_path_str)
    full_id = task_path.name
    task_id = full_id.split("-")[0]

    # 从映射文件获取完整信息
    mapping = self._load_mapping()
    if task_id not in mapping:
        return None

    task_data = mapping[task_id]
    return TaskInfo(
        task_id=task_id,
        full_id=task_data["full_id"],
        path=task_data["path"],
        status=task_data["status"],
        created=task_data.get("created", "")
    )
```

**执行流程**：
1. 检查 `current-task.txt` 是否存在
2. 读取任务路径
3. 从路径中提取短 ID（目录名第一部分）
4. 从映射文件获取完整信息
5. 返回 TaskInfo 对象

### 3.8 列出任务：list_tasks()

**文件**: `.claude/hooks/lib/task_manager.py:140-155`

```python
def list_tasks(self) -> Dict[str, TaskInfo]:
    """列出所有任务"""
    mapping = self._load_mapping()
    tasks = {}

    for task_id, data in mapping.items():
        if not data.get("archived", False):
            tasks[task_id] = TaskInfo(
                task_id=task_id,
                full_id=data["full_id"],
                path=data["path"],
                status=data["status"],
                created=data.get("created", "")
            )

    return tasks
```

**注意**：只返回未归档的任务（`archived: false`）。

---

## 4. 设计 vs 实现对比

### 4.1 功能完成度分析

| 架构设计要求 | 实现状态 | 说明 |
|-------------|---------|------|
| 创建任务文件夹 | 已实现 | `create_task()` |
| 切换任务文件夹 | 部分实现 | `set_current_task()` 存在，但完整的切换逻辑（git stash/checkout）在 SKILL 层 |
| 维护 short ID 映射 | 已实现 | `_load_mapping()` / `_save_mapping()` |
| 保存/恢复任务上下文 | 部分实现 | `get_current_task()` 存在，快照功能尚未实现 |
| 管理任务快照 | 未实现 | `snapshot.md` 在设计中但代码中未实现 |

### 4.2 差异分析

**已实现的功能**：

1. **任务创建** - 完整实现，包括：
   - 短 ID 自动分配
   - 目录创建
   - 模板初始化
   - 映射文件更新
   - 阶段状态初始化

2. **当前任务管理** - 基本实现：
   - 读取 `current-task.txt`
   - 设置当前任务
   - 从映射获取完整信息

3. **任务列表** - 基本实现：
   - 列出所有未归档任务
   - 返回 TaskInfo 字典

**未完全实现的功能**：

1. **任务快照** - 架构设计中提到 `snapshot.md` 用于任务切换时保存上下文，但代码中未实现

2. **归档功能** - 映射文件中有 `archived` 字段，但没有对应的 `archive_task()` 方法

3. **状态更新** - `TaskInfo` 中有 `status` 字段，但没有 `update_status()` 方法

### 4.3 建议补充的功能

```python
# 建议添加的方法

def archive_task(self, task_id: str) -> bool:
    """归档任务"""
    mapping = self._load_mapping()
    if task_id not in mapping:
        return False

    mapping[task_id]["archived"] = True
    mapping[task_id]["archived_at"] = datetime.now().isoformat()
    self._save_mapping(mapping)

    # 移动到 archive 目录
    task_path = self.project_root / mapping[task_id]["path"]
    archive_path = self.tasks_dir / "archive" / task_path.name
    shutil.move(str(task_path), str(archive_path))

    return True

def update_status(self, task_id: str, status: str) -> bool:
    """更新任务状态"""
    mapping = self._load_mapping()
    if task_id not in mapping:
        return False

    mapping[task_id]["status"] = status
    mapping[task_id]["updated_at"] = datetime.now().isoformat()
    self._save_mapping(mapping)
    return True

def create_snapshot(self, task_id: str) -> bool:
    """创建任务快照"""
    mapping = self._load_mapping()
    if task_id not in mapping:
        return False

    task_path = self.project_root / mapping[task_id]["path"]
    snapshot_path = task_path / "snapshot.md"

    # 收集当前上下文
    snapshot_content = self._collect_context(task_path)
    snapshot_path.write_text(snapshot_content)
    return True
```

---

## 5. 任务生命周期

### 5.1 状态流转图

```
┌─────────────────────────────────────────────────────────────────────┐
│                      任务状态流转图                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [/nomos:start]                                                      │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────┐                                                         │
│  │  draft  │ ←── 任务创建后的初始状态                                 │
│  └────┬────┘                                                         │
│       │                                                              │
│       │ [完成 Research 阶段]                                          │
│       ▼                                                              │
│  ┌──────────┐                                                        │
│  │in_review │ ←── 等待人类审阅 research.md                           │
│  └────┬─────┘                                                        │
│       │                                                              │
│       │ [人类批准 Research]                                           │
│       ▼                                                              │
│  ┌──────────┐                                                        │
│  │ approved │ ←── Plan 阶段完成，等待执行                             │
│  └────┬─────┘                                                        │
│       │                                                              │
│       │ [进入 Execute 阶段]                                           │
│       ▼                                                              │
│  ┌───────────┐                                                       │
│  │ executing │ ←── 正在编写代码                                       │
│  └─────┬─────┘                                                       │
│       │                                                              │
│       │ [完成所有 Gates + Review]                                     │
│       ▼                                                              │
│  ┌─────────┐                                                         │
│  │  done   │ ←── 任务完成，可归档                                     │
│  └─────────┘                                                         │
│                                                                      │
│  特殊路径:                                                           │
│  done ──[/nomos:archive]──► archived                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 与 Phase 的对应关系

| 任务状态 | 对应 Phase | 说明 |
|----------|-----------|------|
| `draft` | RESEARCH | 任务刚创建，开始调研 |
| `in_review` | RESEARCH/PLAN | 等待人类审阅 |
| `approved` | PLAN → EXECUTE | Plan 完成，准备执行 |
| `executing` | EXECUTE | 正在实现代码 |
| `done` | REVIEW → DONE | 所有 Gates 完成，Review 通过 |

### 5.3 完整生命周期流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      任务完整生命周期                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 0: 创建                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 用户: /nomos:start user-login                                  │ │
│  │ 系统响应:                                                       │ │
│  │   1. TaskManager.create_task("user-login")                     │ │
│  │   2. 创建 tasks/t1-2026-02-26-user-login/                      │ │
│  │   3. 初始化 research.md, plan.md, code_review.md, progress.md  │ │
│  │   4. PhaseManager.initialize() → phase_state.json              │ │
│  │   5. GitManager.create_branch("feat/2026-02-26-user-login")    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Phase 1: Research                                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Agent: 分析需求，调研现有代码                                    │ │
│  │ 输出: research.md                                               │ │
│  │ 状态: draft → in_review                                         │ │
│  │ 门控: 人类必须审阅并添加 Review Comments                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Phase 2: Plan                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Agent: 制定实施计划，定义 Phase Gates                           │ │
│  │ 输出: plan.md (含 Mermaid 图)                                   │ │
│  │ 状态: in_review → approved                                      │ │
│  │ 门控: 人类必须审阅并批准所有 CRITICAL/MAJOR Review Comments      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Phase 3: Execute                                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Agent: 按 Gate 顺序实现代码                                     │ │
│  │ 每个 Gate 完成后自动 commit                                     │ │
│  │ 状态: approved → executing                                      │ │
│  │ 门控: PreToolUse Hook 检查 Linter, Test-First                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Phase 4: Review                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Agent: 运行测试，生成 code_review.md                            │ │
│  │ 状态: executing → done                                          │ │
│  │ 门控: Stop Hook 检查所有 Gates 完成                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  Phase 5: 归档                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 用户: /nomos:pr                                                 │ │
│  │ 系统响应:                                                       │ │
│  │   1. 生成 PR 描述                                               │ │
│  │   2. 创建 GitHub PR                                             │ │
│  │   3. TaskManager.archive_task()                                 │ │
│  │   4. 移动到 tasks/archive/                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. 数据结构详解

### 6.1 short-id-mapping.json

**路径**: `tasks/short-id-mapping.json`

```json
{
  "t1": {
    "full_id": "t1-2026-02-25-user-login",
    "path": "tasks/t1-2026-02-25-user-login",
    "status": "done",
    "archived": true,
    "created": "2026-02-25T09:00:00.000000"
  },
  "t2": {
    "full_id": "t2-2026-02-26-payment-api",
    "path": "tasks/t2-2026-02-26-payment-api",
    "status": "executing",
    "archived": false,
    "created": "2026-02-26T14:30:00.000000"
  },
  "t3": {
    "full_id": "t3-2026-02-26-logging-fix",
    "path": "tasks/t3-2026-02-26-logging-fix",
    "status": "draft",
    "archived": false,
    "created": "2026-02-26T16:00:00.000000"
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `full_id` | string | 完整任务 ID（目录名） |
| `path` | string | 相对于项目根的路径 |
| `status` | string | 任务状态 |
| `archived` | boolean | 是否已归档 |
| `created` | string | 创建时间（ISO 8601） |

### 6.2 current-task.txt

**路径**: `.claude/current-task.txt`

```
tasks/t2-2026-02-26-payment-api
```

**说明**：
- 单行文本文件
- 存储当前活跃任务的相对路径
- 由 `set_current_task()` 写入，`get_current_task()` 读取

### 6.3 phase_state.json

**路径**: `tasks/t1-xxx/phase_state.json`

```json
{
  "task_id": "t1",
  "current_phase": "execute",
  "research": {
    "completed": true,
    "approved_by": "human",
    "approved_at": "2026-02-25T10:30:00",
    "gates_total": 0,
    "gates_completed": 0
  },
  "plan": {
    "completed": true,
    "approved_by": "human",
    "approved_at": "2026-02-25T11:00:00",
    "gates_total": 5,
    "gates_completed": 5
  },
  "execute": {
    "completed": false,
    "approved_by": null,
    "approved_at": null,
    "gates_total": 5,
    "gates_completed": 3
  },
  "review": {
    "completed": false,
    "approved_by": null,
    "approved_at": null,
    "gates_total": 0,
    "gates_completed": 0
  },
  "created": "2026-02-25T09:00:00",
  "updated": "2026-02-26T14:30:00"
}
```

### 6.4 任务文件夹结构

```
tasks/t2-2026-02-26-payment-api/
├── research.md              # 调研文档（Phase 1 输出）
├── plan.md                  # 计划文档（Phase 2 输出，含 Phase Gates）
├── code_review.md           # 审查文档（Phase 4 输出）
├── progress.md              # 进度追踪（可选）
├── phase_state.json         # 阶段状态（PhaseManager 管理）
├── .task-viewer.html        # Task Viewer 界面（可选）
└── .annotations/            # 代码标注目录（可选）
    └── code.json            # 代码标注数据
```

---

## 7. 工具函数模块

### 7.1 utils.py 概述

**文件**: `.claude/hooks/lib/utils.py`

该模块提供通用工具函数，目前包含：

```python
def create_temp_file(content: str, suffix: str = ".tmp") -> str:
    """创建临时文件并写入内容"""

def detect_language(file_path: str) -> Optional[str]:
    """根据文件扩展名检测语言"""

def is_code_file(file_path: str) -> bool:
    """判断是否为代码文件"""
```

### 7.2 语言检测映射

```python
language_map = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}
```

**用途**：
- Linter 引擎根据语言选择对应规则
- PhaseManager 判断文件是否为代码文件（决定是否受阶段限制）

---

## 8. 与 PhaseManager 的协作

### 8.1 职责分离

| 模块 | 职责 |
|------|------|
| **TaskManager** | 任务生命周期管理（创建、切换、列表） |
| **PhaseManager** | 阶段状态管理（Research/Plan/Execute/Review） |

### 8.2 协作流程

```
TaskManager.create_task()
        │
        ├─── 创建任务目录
        ├─── 初始化四件套
        │
        └─── PhaseManager.initialize()
                  │
                  └─── 创建 phase_state.json
                       设置 current_phase = "research"
```

### 8.3 代码集成点

**文件**: `.claude/hooks/lib/task_manager.py:238-246`

```python
def _init_phase_state(self, task_path: Path, task_info: TaskInfo) -> None:
    """初始化阶段状态文件"""
    try:
        PhaseManager = _import_phase_manager()
        pm = PhaseManager(str(task_path), str(self.project_root))
        pm.initialize(task_info.task_id)
    except Exception:
        # 如果初始化失败，不影响任务创建
        pass
```

**设计说明**：
- 使用延迟导入避免循环依赖
- 初始化失败不阻塞任务创建（优雅降级）

---

## 9. 最佳实践

### 9.1 任务命名规范

```
推荐格式: {action}-{target}-{detail}

示例:
- user-login           # 用户登录功能
- payment-api-refactor # 支付 API 重构
- auth-bug-fix         # 认证 Bug 修复
- test-coverage        # 测试覆盖补充
```

### 9.2 任务类型使用

| 类型 | 前缀 | 使用场景 |
|------|------|----------|
| `feat` | feat/ | 新功能开发 |
| `fix` | fix/ | Bug 修复 |
| `refactor` | refactor/ | 代码重构 |
| `test` | test/ | 测试相关 |
| `docs` | docs/ | 文档更新 |

### 9.3 状态管理建议

1. **及时更新状态** - 每个 Phase 完成后更新 `status`
2. **归档已完成任务** - 避免任务列表膨胀
3. **保持单一当前任务** - 切换任务前先保存状态

---

## 10. 总结

### 10.1 模块价值

Task Manager 是 nOmOsAi 工作流的"任务管家"，提供：

- **隔离性**: 每个任务独立文件夹，上下文纯净
- **可追溯性**: 所有状态持久化在文件中
- **便捷性**: Short ID 简化任务引用
- **协作性**: 与 PhaseManager、GitManager 无缝集成

### 10.2 待完善项

| 项目 | 优先级 | 说明 |
|------|--------|------|
| 归档功能 | P1 | 实现 `archive_task()` 方法 |
| 快照功能 | P2 | 实现任务切换时的上下文保存 |
| 状态更新 | P1 | 实现 `update_status()` 方法 |
| 任务搜索 | P3 | 支持按名称/状态筛选任务 |

### 10.3 相关文档

- [01_overview.md](./01_overview.md) - 模块总览
- [03_phase-manager.md](./03_phase-manager.md) - 阶段管理器详解
- `/doc-arch/agent-nomos-flow/03_System_Architecture.md` - 系统架构设计
- `/doc-arch/agent-nomos-flow/02_PRD.md` - 产品需求文档

---

*文档版本: 1.0*
*最后更新: 2026-02-27*
*作者: Claude Code*
