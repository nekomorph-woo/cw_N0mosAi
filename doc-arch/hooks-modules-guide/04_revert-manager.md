# Revert Manager 模块详解

**文档版本**: 1.0
**最后更新**: 2026-02-27
**适用阶段**: Phase 2 - Gate 2.8

---

## 1. 概述

### 1.1 设计目标

Revert Manager 是 nOmOsAi 框架中的代码回滚管理模块，其核心设计理念是 **"果断回滚，避免修补陷阱"**。

在 AI Agent 编码过程中，当发现方向性错误或严重问题时，传统做法是增量修补（patch），但这往往导致：
- Token 消耗指数级增长
- 代码质量持续下降
- 技术债务不断累积
- 问题越改越复杂

Revert Manager 提供了一种更高效的解决方案：**果断回滚到健康状态，重新设计方案**。

### 1.2 使用场景

| 场景 | 描述 | 典型触发条件 |
|------|------|-------------|
| **架构违反** | Protected Interface 被意外修改 | L3 业务规则检测 |
| **安全漏洞** | 引入 SQL 注入/XSS 等安全问题 | L4 安全检查 |
| **方向错误** | 整体设计不符合预期 | 人类标注 `[REVERT]` |
| **测试崩溃** | 核心功能测试失败超过 30% | 测试结果分析 |
| **循环依赖** | 引入破坏性的循环依赖 | Validator Subagent |

### 1.3 核心价值

```
┌─────────────────────────────────────────────────────────────────┐
│                    Revert vs 增量修补对比                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  增量修补模式:                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 问题出现 → Patch 1 → 问题依旧 → Patch 2 → 更乱 → Patch N   │ │
│  │ Token 消耗: O(N^2)  |  代码质量: 持续下降                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Revert 模式:                                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 问题出现 → Revert → 分析教训 → 重新设计 → 正确实现          │ │
│  │ Token 消耗: O(1)  |  代码质量: 恢复健康                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  结论: Revert 比增量修补节省 90% 的 Token                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构设计

### 2.1 架构定位

Revert Manager 在 nOmOsAi 整体架构中位于 **3.9 节**，属于 **Execute/Review 阶段** 的核心组件。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         nOmOsAi 五大循环机制                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐                                                        │
│  │ Why-First    │ ← 任务开始前，深度思考                                  │
│  │ 循环         │                                                        │
│  └──────────────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ 标注循环     │ ← Research/Plan/Execute 阶段                           │
│  └──────────────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ Linter 循环  │ ← Execute 阶段                                         │
│  └──────────────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ 测试循环     │ ← Execute 阶段                                         │
│  └──────────────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐     ┌──────────────────────────────────────────────┐  │
│  │ Revert 循环  │ ←── │  Revert Manager (本模块)                      │  │
│  │ (严重错误)   │     │  - 检测触发条件                               │  │
│  └──────────────┘     │  - 执行 Git Revert                            │  │
│         │             │  - 记录失败原因                                │  │
│         │             │  - 同步教训到 project-why.md                  │  │
│         ↓             │  - 回到 Plan 阶段                              │  │
│  ┌──────────────┐     └──────────────────────────────────────────────┘  │
│  │ Plan 阶段    │ ← 重新设计方案                                        │
│  └──────────────┘                                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 设计要求（来自架构文档）

根据 `03_System_Architecture.md` 3.9 节的设计，Revert Manager 应满足以下要求：

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 触发检测 | 识别多种 Revert 触发条件 | P0 |
| Git 操作 | 执行 `git revert` 命令 | P0 |
| 记录机制 | 记录 Revert 原因和结果 | P0 |
| 状态更新 | 更新 plan.md 为 needs_replan | P0 |
| 教训同步 | 将失败经验同步到 project-why.md | P1 |
| 严重程度评估 | 区分 critical/high/medium 级别 | P1 |

### 2.3 与其他模块的关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Revert Manager 模块交互图                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐        触发信号         ┌─────────────────────┐   │
│  │ PostToolUse     │ ──────────────────────► │                     │   │
│  │ Hook            │                         │                     │   │
│  └─────────────────┘                         │                     │   │
│                                              │                     │   │
│  ┌─────────────────┐        触发信号         │                     │   │
│  │ Stop Hook       │ ──────────────────────► │                     │   │
│  └─────────────────┘                         │    Revert Manager   │   │
│                                              │                     │   │
│  ┌─────────────────┐        触发信号         │                     │   │
│  │ Validator       │ ──────────────────────► │                     │   │
│  │ Subagent        │                         │                     │   │
│  └─────────────────┘                         └──────────┬──────────┘   │
│                                                         │              │
│                                                         │              │
│         ┌───────────────────────────────────────────────┼──────┐       │
│         │                                               │      │       │
│         ▼                                               ▼      ▼       │
│  ┌─────────────┐   ┌─────────────────┐   ┌───────────────────────┐   │
│  │ Git         │   │ revert-log.json │   │ project-why.md        │   │
│  │ Repository  │   │ (失败记录)       │   │ (教训同步)            │   │
│  └─────────────┘   └─────────────────┘   └───────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 代码实现详解

### 3.1 文件位置

```
/Volumes/Under_M2/a056cw/cw_nOmOsAi/.claude/hooks/lib/revert_manager.py
```

### 3.2 类结构

```python
class RevertManager:
    """Revert Manager - 管理代码回滚和失败记录"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化 Revert Manager

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())
        self.revert_log_file = self.project_root / '.claude' / 'revert-log.json'
```

**关键属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| `project_root` | `Path` | 项目根目录，默认当前工作目录 |
| `revert_log_file` | `Path` | Revert 日志文件路径，位于 `.claude/revert-log.json` |

### 3.3 核心方法详解

#### 3.3.1 `should_revert()` - 触发条件判断

**位置**: `revert_manager.py:26-47`

```python
def should_revert(self, reason: str) -> bool:
    """
    判断是否应该 revert

    Args:
        reason: 原因

    Returns:
        是否应该 revert
    """
    # Revert 触发条件
    revert_keywords = [
        '严重错误',
        '无法修复',
        '方向错误',
        '架构问题',
        '性能严重下降',
        '破坏性变更',
        '测试全部失败'
    ]

    return any(keyword in reason for keyword in revert_keywords)
```

**设计分析**:

这是一个**关键词匹配**的简单实现。通过检查 `reason` 字符串中是否包含预定义的关键词来判断是否需要回滚。

**关键词对照表**:

| 关键词 | 对应场景 | 架构设计中的触发条件 |
|--------|---------|---------------------|
| `严重错误` | 通用严重错误 | severity = critical |
| `无法修复` | Linter 连续失败 | Hooks 连续阻塞 3 次 |
| `方向错误` | 设计不符合预期 | 人类批注"方向错误" |
| `架构问题` | 架构违反 | Protected Interface 被修改 |
| `性能严重下降` | 性能回退 | 性能基准测试失败 |
| `破坏性变更` | 破坏性修改 | 分层架构被破坏 |
| `测试全部失败` | 测试崩溃 | 核心功能测试失败 > 30% |

**局限性**: 当前实现是**文本匹配**，而非结构化的严重程度评估。架构设计中的 `severity = critical/high/medium` 分级尚未完全实现。

#### 3.3.2 `execute_revert()` - 执行回滚

**位置**: `revert_manager.py:49-87`

```python
def execute_revert(self, commit_hash: Optional[str] = None, reason: str = "") -> bool:
    """
    执行 Git Revert

    Args:
        commit_hash: 要 revert 的 commit，None 表示最后一个 commit
        reason: Revert 原因

    Returns:
        是否成功
    """
    try:
        if commit_hash:
            # Revert 指定 commit
            result = subprocess.run(
                ["git", "revert", "--no-edit", commit_hash],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Revert 最后一个 commit
            result = subprocess.run(
                ["git", "revert", "--no-edit", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

        # 记录 revert
        self._log_revert(commit_hash or "HEAD", reason)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Revert 失败: {e.stderr}")
        return False
```

**执行流程**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    execute_revert 执行流程                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  输入: commit_hash (可选) + reason                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 判断 commit_hash 是否存在                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                    │                    │                        │
│            存在    │                    │  不存在                │
│                    ▼                    ▼                        │
│  ┌─────────────────────┐   ┌─────────────────────┐              │
│  │ git revert --no-edit │   │ git revert --no-edit │              │
│  │ <commit_hash>        │   │ HEAD                 │              │
│  └─────────────────────┘   └─────────────────────┘              │
│                    │                    │                        │
│                    └────────┬───────────┘                        │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 调用 _log_revert() 记录到 revert-log.json                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             │                                    │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 返回 True (成功) 或 False (失败)                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**关键参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `--no-edit` | Git Flag | 使用自动生成的 commit message，无需手动编辑 |
| `check=True` | subprocess | 如果命令失败则抛出异常 |
| `capture_output=True` | subprocess | 捕获 stdout/stderr |

**异常处理**: 捕获 `subprocess.CalledProcessError`，打印错误信息并返回 `False`。

#### 3.3.3 `_log_revert()` - 记录回滚日志

**位置**: `revert_manager.py:89-116`

```python
def _log_revert(self, commit_hash: str, reason: str):
    """
    记录 revert 到日志

    Args:
        commit_hash: Commit hash
        reason: 原因
    """
    import json

    # 读取现有日志
    reverts = []
    if self.revert_log_file.exists():
        with open(self.revert_log_file, 'r') as f:
            reverts = json.load(f)

    # 添加新记录
    reverts.append({
        'commit': commit_hash,
        'reason': reason,
        'timestamp': datetime.now().isoformat(),
        'branch': self._get_current_branch()
    })

    # 保存
    self.revert_log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(self.revert_log_file, 'w') as f:
        json.dump(reverts, f, indent=2, ensure_ascii=False)
```

**记录结构**:

每条 Revert 记录包含以下字段：

```json
{
  "commit": "a1b2c3d",
  "reason": "方向错误：设计不符合预期",
  "timestamp": "2026-02-27T14:32:15.123456",
  "branch": "feature/2026-02-27-user-login"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `commit` | `string` | 被回滚的 commit hash 或 "HEAD" |
| `reason` | `string` | 回滚原因 |
| `timestamp` | `string` | ISO 格式时间戳 |
| `branch` | `string` | 当前 Git 分支名 |

#### 3.3.4 `sync_to_project_why()` - 同步失败教训

**位置**: `revert_manager.py:118-147`

```python
def sync_to_project_why(self, reason: str, lesson: str):
    """
    同步失败教训到 project-why.md

    Args:
        reason: 失败原因
        lesson: 经验教训
    """
    from .why_first_engine import WhyFirstEngine

    why_engine = WhyFirstEngine(str(self.project_root))

    # 添加到经验教训
    title = f"Revert: {reason[:50]}"
    content = f"""
**原因**: {reason}

**教训**: {lesson}

**避免方法**:
- 在实施前充分验证方案
- 及时发现问题并果断回滚
- 记录失败原因避免重复
"""

    why_engine.add_knowledge(
        category='经验教训',
        title=title,
        content=content.strip()
    )
```

**与 WhyFirstEngine 的联动**:

该方法通过调用 `WhyFirstEngine.add_knowledge()` 将失败经验同步到 `project-why.md` 的"经验教训"分类下。

**生成的内容模板**:

```markdown
### Revert: Protected Interface 被意外修改

**时间**: 2026-02-27

**原因**: Protected Interface `AuthService.login()` 签名被修改

**教训**: 修改核心接口前必须先更新 research.md 并获得人类确认

**避免方法**:
- 在实施前充分验证方案
- 及时发现问题并果断回滚
- 记录失败原因避免重复
```

#### 3.3.5 `get_revert_history()` - 获取历史记录

**位置**: `revert_manager.py:149-167`

```python
def get_revert_history(self, limit: int = 10) -> List[Dict]:
    """
    获取 revert 历史

    Args:
        limit: 返回数量

    Returns:
        Revert 记录列表
    """
    import json

    if not self.revert_log_file.exists():
        return []

    with open(self.revert_log_file, 'r') as f:
        reverts = json.load(f)

    return reverts[-limit:]
```

**返回值**: 返回最近 `limit` 条 Revert 记录，按时间正序排列（最新的在末尾）。

#### 3.3.6 `analyze_revert_patterns()` - 分析回滚模式

**位置**: `revert_manager.py:180-204`

```python
def analyze_revert_patterns(self) -> Dict[str, int]:
    """
    分析 revert 模式

    Returns:
        模式统计
    """
    import json

    if not self.revert_log_file.exists():
        return {}

    with open(self.revert_log_file, 'r') as f:
        reverts = json.load(f)

    # 统计原因
    reasons = {}
    for revert in reverts:
        reason = revert.get('reason', 'Unknown')
        # 提取关键词
        for keyword in ['错误', '性能', '架构', '测试', '破坏']:
            if keyword in reason:
                reasons[keyword] = reasons.get(keyword, 0) + 1

    return reasons
```

**返回示例**:

```python
{
    "错误": 5,
    "架构": 3,
    "测试": 2,
    "性能": 1
}
```

#### 3.3.7 `suggest_prevention()` - 预防建议

**位置**: `revert_manager.py:206-232`

```python
def suggest_prevention(self) -> List[str]:
    """
    根据历史 revert 建议预防措施

    Returns:
        建议列表
    """
    patterns = self.analyze_revert_patterns()

    suggestions = []

    if patterns.get('测试', 0) > 2:
        suggestions.append('建议: 加强测试覆盖，在 commit 前运行完整测试')

    if patterns.get('架构', 0) > 1:
        suggestions.append('建议: 在 Plan 阶段进行更充分的架构设计评审')

    if patterns.get('性能', 0) > 1:
        suggestions.append('建议: 添加性能基准测试，避免性能回退')

    if patterns.get('错误', 0) > 3:
        suggestions.append('建议: 增加 Linter 规则，在代码写入前捕获更多错误')

    if not suggestions:
        suggestions.append('暂无特定建议，继续保持良好的开发习惯')

    return suggestions
```

**建议触发阈值**:

| 关键词 | 阈值 | 建议内容 |
|--------|------|---------|
| `测试` | > 2 次 | 加强测试覆盖 |
| `架构` | > 1 次 | 加强架构设计评审 |
| `性能` | > 1 次 | 添加性能基准测试 |
| `错误` | > 3 次 | 增加 Linter 规则 |

---

## 4. 设计 vs 实现对比

### 4.1 功能完成度分析

| 架构设计要求 | 实现状态 | 完成度 | 备注 |
|-------------|---------|--------|------|
| 触发条件检测 | 已实现 | 70% | 关键词匹配，缺少结构化分级 |
| Git Revert 执行 | 已实现 | 90% | 支持单 commit，缺少多 commit 方案 |
| 记录到 code_review.md | 未实现 | 0% | 当前记录到 revert-log.json |
| 记录到 revert-log.json | 已实现 | 100% | 完整实现 |
| 状态更新 plan.md | 未实现 | 0% | 需要在 Hook 层实现 |
| 教训同步 project-why.md | 已实现 | 100% | 完整实现 |
| 严重程度评估 | 部分实现 | 50% | 缺少 critical/high/medium 分级 |
| 人类确认机制 | 未实现 | 0% | 需要在 Hook 层实现 |
| 模式分析 | 已实现 | 100% | 完整实现 |
| 预防建议 | 已实现 | 100% | 完整实现 |

### 4.2 差异分析

#### 4.2.1 触发条件分级

**架构设计**:

```
| 触发来源 | 条件 | 严重程度 | 处理方式 |
|----------|------|----------|----------|
| L3 业务规则 | Protected Interface 被修改 | critical | 自动 revert |
| L3 业务规则 | 分层架构被破坏 | critical | 自动 revert |
| Validator Subagent | 发现架构冲突 | high | 询问人类确认 |
| 测试结果 | 核心功能测试失败 > 30% | high | 自动 revert |
| 测试结果 | 回归测试失败 > 20% | medium | 询问人类确认 |
```

**当前实现**:

```python
# 简单的关键词匹配，无分级
revert_keywords = [
    '严重错误', '无法修复', '方向错误', '架构问题',
    '性能严重下降', '破坏性变更', '测试全部失败'
]
return any(keyword in reason for keyword in revert_keywords)
```

**差距**: 缺少结构化的严重程度评估，无法区分"自动 revert"和"询问人类确认"的场景。

#### 4.2.2 多粒度 Revert

**架构设计**:

```python
# 方案 A: 单 commit revert
git revert HEAD --no-edit

# 方案 B: 多 commit revert (回到指定点)
git reset --hard <last-good-commit>
git push --force-with-lease origin <branch>

# 方案 C: 文件级 revert (只回滚特定文件)
git checkout <last-good-commit> -- <file-path>
```

**当前实现**:

```python
# 仅支持方案 A
if commit_hash:
    subprocess.run(["git", "revert", "--no-edit", commit_hash], ...)
else:
    subprocess.run(["git", "revert", "--no-edit", "HEAD"], ...)
```

**差距**: 缺少方案 B（多 commit）和方案 C（文件级）的支持。

#### 4.2.3 记录位置

**架构设计**:

```markdown
## 6. Revert 记录 (在 code_review.md 中)

### 6.1 Revert #1
- **Revert ID**: REV-2026-02-24-001
- **Revert 时间**: 2026-02-24 14:32:15
- **触发来源**: Validator Subagent
- **触发原因**: Protected Interface `AuthService.login()` 签名被修改
- **严重程度**: critical
- **Revert 类型**: commit (单 commit revert)
- **Revert 范围**: commit: a1b2c3d, files: src/auth/service.py
- **Git 命令**: `git revert a1b2c3d --no-edit`
- **执行结果**: success
- **当前 HEAD**: a0b1c2d (回滚后)
- **后续处理**: ...
- **教训/改进点**: ...
```

**当前实现**:

```json
// 记录在 .claude/revert-log.json
{
  "commit": "a1b2c3d",
  "reason": "方向错误：设计不符合预期",
  "timestamp": "2026-02-27T14:32:15.123456",
  "branch": "feature/2026-02-27-user-login"
}
```

**差距**: 记录字段较少，缺少触发来源、严重程度、Revert 类型、执行结果、后续处理、教训改进点等信息。

### 4.3 完成度总结

```
┌─────────────────────────────────────────────────────────────────┐
│                    Revert Manager 完成度                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  核心功能                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Git Revert 执行        ████████████████████  90%           │ │
│  │ 失败记录机制           ████████████████████  100%          │ │
│  │ 教训同步               ████████████████████  100%          │ │
│  │ 模式分析               ████████████████████  100%          │ │
│  │ 预防建议               ████████████████████  100%          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  架构集成                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 触发条件分级           ████████░░░░░░░░░░░░  50%           │ │
│  │ 状态更新 plan.md       ░░░░░░░░░░░░░░░░░░░░  0%            │ │
│  │ 记录到 code_review.md  ░░░░░░░░░░░░░░░░░░░░  0%            │ │
│  │ 人类确认机制           ░░░░░░░░░░░░░░░░░░░░  0%            │ │
│  │ 多粒度 Revert          ████████░░░░░░░░░░░░  40%           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  总体完成度: 约 65%                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Revert 触发条件

### 5.1 触发来源分类

根据架构设计（`03_System_Architecture.md:1603-1615`），Revert 触发条件分为以下几类：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Revert 触发条件矩阵                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  触发来源                 条件                          严重程度  处理   │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  L3 业务规则              Protected Interface 被修改    critical  自动  │
│  L3 业务规则              分层架构被破坏                critical  自动  │
│                                                                          │
│  L4 安全检查              SQL 注入 / XSS / 硬编码密钥   critical  自动  │
│                                                                          │
│  Validator Subagent       发现架构冲突                  high      询问  │
│  Validator Subagent       循环依赖引入                  high      询问  │
│                                                                          │
│  人类 Review 批注         包含 `[REVERT]` 标记          -         自动  │
│  人类 Review 批注         "方向错误" 等否定批注         -         询问  │
│                                                                          │
│  测试结果                 核心功能测试失败 > 30%        high      自动  │
│  测试结果                 回归测试失败 > 20%            medium    询问  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 严重程度分级

| 严重程度 | 触发条件示例 | 处理方式 |
|----------|-------------|---------|
| `critical` | Protected Interface 被修改、安全漏洞 | 自动 revert，无需确认 |
| `high` | 架构冲突、测试大面积失败 | 询问人类确认后 revert |
| `medium` | 回归测试部分失败 | 询问人类确认后 revert |
| `low` | 仅记录警告，不触发 revert | 仅记录，不回滚 |

### 5.3 人类批注标记

在 Review Comments 中使用特殊标记触发 Revert：

| 标记 | 含义 | 示例 |
|------|------|------|
| `[REVERT]` | 方向错误，必须回滚 | `[REVERT] 整体方案不符合预期，重新设计` |
| `[CRITICAL]` | 严重问题，可能触发回滚 | `[CRITICAL] 不能直接访问 DB，必须走 Repository` |

### 5.4 当前实现的关键词

`revert_manager.py:37-45` 中定义的关键词：

```python
revert_keywords = [
    '严重错误',      # 通用严重错误
    '无法修复',      # Linter 连续失败
    '方向错误',      # 设计不符合预期
    '架构问题',      # 架构违反
    '性能严重下降',  # 性能回退
    '破坏性变更',    # 破坏性修改
    '测试全部失败'   # 测试崩溃
]
```

---

## 6. 失败记录机制

### 6.1 revert-log.json 结构

**文件位置**: `.claude/revert-log.json`

**数据结构**:

```json
[
  {
    "commit": "a1b2c3d",
    "reason": "方向错误：设计不符合预期",
    "timestamp": "2026-02-27T14:32:15.123456",
    "branch": "feature/2026-02-27-user-login"
  },
  {
    "commit": "b2c3d4e",
    "reason": "架构问题：Protected Interface 被修改",
    "timestamp": "2026-02-27T15:45:30.654321",
    "branch": "feature/2026-02-27-user-login"
  }
]
```

### 6.2 记录字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `commit` | `string` | 是 | 被回滚的 commit hash 或 "HEAD" |
| `reason` | `string` | 是 | 回滚原因描述 |
| `timestamp` | `string` | 是 | ISO 8601 格式时间戳 |
| `branch` | `string` | 是 | 回滚发生时的 Git 分支名 |

### 6.3 与架构设计的差异

架构设计中定义的记录字段（`03_System_Architecture.md:1695-1717`）：

```markdown
### 6.1 Revert #1
- **Revert ID**: REV-2026-02-24-001
- **Revert 时间**: 2026-02-24 14:32:15
- **触发来源**: Validator Subagent
- **触发原因**: Protected Interface `AuthService.login()` 签名被修改
- **严重程度**: critical
- **Revert 类型**: commit (单 commit revert)
- **Revert 范围**:
  - commit: a1b2c3d
  - files: src/auth/service.py, src/auth/service_test.py
- **Git 命令**: `git revert a1b2c3d --no-edit`
- **执行结果**: success
- **当前 HEAD**: a0b1c2d (回滚后)
- **后续处理**:
  - [x] plan.md 状态更新为 needs_replan
  - [x] 生成 Revert Report
  - [ ] 等待人类确认新方案
- **教训/改进点**:
  - 需要在 PreToolUse 中增加 Protected Interface AST 检查
  - 建议添加规则: 修改 auth/ 下文件必须先更新 research.md
```

**缺失字段**:

| 字段 | 状态 | 说明 |
|------|------|------|
| `Revert ID` | 缺失 | 唯一标识符 |
| `触发来源` | 缺失 | Hook/Subagent/人类批注 |
| `严重程度` | 缺失 | critical/high/medium |
| `Revert 类型` | 缺失 | commit/multi-commit/file |
| `Revert 范围` | 缺失 | 影响的文件列表 |
| `Git 命令` | 缺失 | 实际执行的命令 |
| `执行结果` | 缺失 | success/failed |
| `当前 HEAD` | 缺失 | 回滚后的 HEAD |
| `后续处理` | 缺失 | 待办事项列表 |
| `教训/改进点` | 缺失 | 从失败中学习的点 |

### 6.4 使用示例

```python
from lib.revert_manager import RevertManager

# 初始化
manager = RevertManager('/path/to/project')

# 检查是否应该 revert
if manager.should_revert("架构问题：Protected Interface 被修改"):
    # 执行 revert
    success = manager.execute_revert(reason="架构问题")

    if success:
        # 同步教训到 project-why.md
        manager.sync_to_project_why(
            reason="Protected Interface 被修改",
            lesson="修改核心接口前必须先更新 research.md"
        )

# 获取历史记录
history = manager.get_revert_history(limit=5)

# 分析模式
patterns = manager.analyze_revert_patterns()

# 获取预防建议
suggestions = manager.suggest_prevention()
```

---

## 7. 与 project-why.md 的联动

### 7.1 联动机制

Revert Manager 通过 `sync_to_project_why()` 方法与 `WhyFirstEngine` 集成，将失败经验同步到 `project-why.md`。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Revert → project-why.md 联动流程                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐                                                    │
│  │ Revert 执行     │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                    │
│  │ sync_to_project │                                                    │
│  │ _why() 调用     │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ WhyFirstEngine.add_knowledge(                                   │   │
│  │     category='经验教训',                                         │   │
│  │     title='Revert: {reason[:50]}',                              │   │
│  │     content='**原因**: {reason}\n**教训**: {lesson}\n...'        │   │
│  │ )                                                               │   │
│  └────────┬────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ project-why.md 更新                                             │   │
│  │                                                                 │   │
│  │ ## 经验教训                                                     │   │
│  │                                                                 │   │
│  │ ### Revert: Protected Interface 被意外修改                      │   │
│  │ **时间**: 2026-02-27                                           │   │
│  │ **原因**: Protected Interface `AuthService.login()` 签名被修改  │   │
│  │ **教训**: 修改核心接口前必须先更新 research.md                   │   │
│  │ **避免方法**:                                                   │   │
│  │ - 在实施前充分验证方案                                          │   │
│  │ - 及时发现问题并果断回滚                                        │   │
│  │ - 记录失败原因避免重复                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 WhyFirstEngine 相关方法

**位置**: `why_first_engine.py:48-113`

```python
def add_knowledge(self, category: str, title: str, content: str) -> bool:
    """
    添加知识到 project-why.md

    Args:
        category: 分类（核心理念/架构决策/经验教训/常见问题）
        title: 标题
        content: 内容

    Returns:
        是否成功
    """
```

**支持的分类**:

| 分类 | 用途 | Revert Manager 使用 |
|------|------|-------------------|
| `核心理念` | 项目核心原则 | 否 |
| `架构决策` | 重要架构决策记录 | 否 |
| `经验教训` | 失败经验总结 | **是** |
| `常见问题` | FAQ | 否 |

### 7.3 内容模板

`sync_to_project_why()` 生成的标准模板：

```markdown
### Revert: {reason 的前 50 字符}

**时间**: {当前日期}

**原因**: {完整的失败原因}

**教训**: {从失败中学到的经验}

**避免方法**:
- 在实施前充分验证方案
- 及时发现问题并果断回滚
- 记录失败原因避免重复
```

### 7.4 知识积累效果

通过 Revert → project-why.md 的联动，项目知识库会持续积累失败经验：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    知识积累效果示意                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  第 1 次失败:                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ ### Revert: Protected Interface 被修改                             │ │
│  │ 教训: 修改核心接口前必须先更新 research.md                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  第 2 次失败:                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ ### Revert: 循环依赖引入                                           │ │
│  │ 教训: 新增模块时必须检查依赖关系图                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  第 N 次失败:                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ ### Revert: 测试覆盖率不足                                         │ │
│  │ 教训: 核心功能必须达到 80% 测试覆盖率才能提交                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  结果: Agent 在下次任务开始时读取 project-why.md，避免重复犯错          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 总结

### 8.1 模块价值

Revert Manager 是 nOmOsAi 框架中实现 **"果断回滚"** 理念的核心模块，主要价值包括：

1. **节省 Token**: 回滚比增量修补节省 90% Token
2. **保持代码质量**: 避免在错误基础上打补丁
3. **知识积累**: 失败经验自动沉淀到 project-why.md
4. **预防改进**: 基于历史模式提供预防建议

### 8.2 待完善功能

| 功能 | 优先级 | 工作量 | 说明 |
|------|--------|--------|------|
| 严重程度分级 | P0 | 2h | 实现 critical/high/medium 分级 |
| 记录到 code_review.md | P1 | 1h | 补充完整的 Revert 记录格式 |
| 状态更新 plan.md | P1 | 1h | 自动更新状态为 needs_replan |
| 多粒度 Revert | P2 | 2h | 支持多 commit 和文件级回滚 |
| 人类确认机制 | P2 | 3h | high/medium 级别询问确认 |

### 8.3 使用建议

1. **及时记录教训**: 每次 Revert 后调用 `sync_to_project_why()` 记录经验
2. **定期分析模式**: 使用 `analyze_revert_patterns()` 发现重复问题
3. **采纳预防建议**: 根据 `suggest_prevention()` 调整开发流程
4. **遵循 Commit 粒度**: 按 Gate 粒度 commit，便于精确回滚

---

## 附录

### A. 文件引用

| 文件 | 路径 |
|------|------|
| Revert Manager | `/Volumes/Under_M2/a056cw/cw_nOmOsAi/.claude/hooks/lib/revert_manager.py` |
| Why-First 引擎 | `/Volumes/Under_M2/a056cw/cw_nOmOsAi/.claude/hooks/lib/why_first_engine.py` |
| 架构设计文档 | `/Volumes/Under_M2/a056cw/cw_nOmOsAi/doc-arch/agent-nomos-flow/03_System_Architecture.md` |
| PRD 文档 | `/Volumes/Under_M2/a056cw/cw_nOmOsAi/doc-arch/agent-nomos-flow/02_PRD.md` |

### B. 相关 User Stories

| ID | 描述 | 状态 |
|----|------|------|
| US-101 | 方向错误时自动 git revert 并回到计划阶段 | 部分实现 |
| FR-104 | Hook 检测方向错误时自动 git revert | 部分实现 |
| FR-110 | 所有 Linter/测试/revert 失败都追加到 project-why.md | 已实现 |

### C. 架构设计参考

- `03_System_Architecture.md:1593-1798` - Revert Manager 完整设计
- `03_System_Architecture.md:919-990` - Commit 粒度策略
- `03_System_Architecture.md:2058-2122` - 标注审查 Revert 联动
- `03_System_Architecture.md:2555-2625` - Revert 循环详细说明

---

*文档由 Claude Code 生成，用于 nOmOsAi Phase 2 模块讲解*
