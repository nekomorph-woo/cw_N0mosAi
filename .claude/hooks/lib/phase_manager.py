"""
Phase Manager - 阶段状态管理器
实现 Research → Plan → Execute → Review 的刚性门控
"""

import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum


class Phase(Enum):
    """阶段枚举"""
    RESEARCH = "research"
    PLAN = "plan"
    EXECUTE = "execute"
    REVIEW = "review"
    DONE = "done"


@dataclass
class PhaseState:
    """单个阶段的状态"""
    completed: bool = False
    approved_by: Optional[str] = None  # "human" or "agent"
    approved_at: Optional[str] = None
    gates_total: int = 0
    gates_completed: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'PhaseState':
        return cls(
            completed=data.get('completed', False),
            approved_by=data.get('approved_by'),
            approved_at=data.get('approved_at'),
            gates_total=data.get('gates_total', 0),
            gates_completed=data.get('gates_completed', 0)
        )


@dataclass
class TaskPhaseState:
    """任务的完整阶段状态"""
    task_id: str
    current_phase: str  # Phase enum value
    research: PhaseState
    plan: PhaseState
    execute: PhaseState
    review: PhaseState
    created: str
    updated: str

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "current_phase": self.current_phase,
            "research": self.research.to_dict(),
            "plan": self.plan.to_dict(),
            "execute": self.execute.to_dict(),
            "review": self.review.to_dict(),
            "created": self.created,
            "updated": self.updated
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskPhaseState':
        return cls(
            task_id=data.get('task_id', ''),
            current_phase=data.get('current_phase', Phase.RESEARCH.value),
            research=PhaseState.from_dict(data.get('research', {})),
            plan=PhaseState.from_dict(data.get('plan', {})),
            execute=PhaseState.from_dict(data.get('execute', {})),
            review=PhaseState.from_dict(data.get('review', {})),
            created=data.get('created', ''),
            updated=data.get('updated', '')
        )


class PhaseManager:
    """阶段状态管理器"""

    PHASE_STATE_FILE = "phase_state.json"

    # 阶段顺序
    PHASE_ORDER = [
        Phase.RESEARCH.value,
        Phase.PLAN.value,
        Phase.EXECUTE.value,
        Phase.REVIEW.value,
        Phase.DONE.value
    ]

    def __init__(self, task_path: str, project_root: Optional[str] = None):
        """
        初始化 PhaseManager

        Args:
            task_path: 任务路径（相对或绝对）
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())

        # 处理相对路径
        if not os.path.isabs(task_path):
            self.task_path = self.project_root / task_path
        else:
            self.task_path = Path(task_path)

        self.state_file = self.task_path / self.PHASE_STATE_FILE

    def initialize(self, task_id: str) -> TaskPhaseState:
        """
        初始化阶段状态文件

        Args:
            task_id: 任务 ID (如 t1)

        Returns:
            初始化后的 TaskPhaseState
        """
        now = datetime.now().isoformat()

        state = TaskPhaseState(
            task_id=task_id,
            current_phase=Phase.RESEARCH.value,
            research=PhaseState(),
            plan=PhaseState(),
            execute=PhaseState(),
            review=PhaseState(),
            created=now,
            updated=now
        )

        self._save_state(state)
        return state

    def load_state(self) -> Optional[TaskPhaseState]:
        """
        加载阶段状态

        Returns:
            TaskPhaseState 或 None（如果不存在）
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TaskPhaseState.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_state(self, state: TaskPhaseState) -> None:
        """保存阶段状态"""
        state.updated = datetime.now().isoformat()
        self.task_path.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    def get_current_phase(self) -> Optional[str]:
        """获取当前阶段"""
        state = self.load_state()
        return state.current_phase if state else None

    def can_proceed_to(self, target_phase: str) -> tuple[bool, str]:
        """
        检查是否可以进入目标阶段

        Args:
            target_phase: 目标阶段

        Returns:
            (是否允许, 原因说明)
        """
        state = self.load_state()
        if not state:
            return False, "阶段状态文件不存在，请先初始化任务"

        current = state.current_phase
        target_idx = self.PHASE_ORDER.index(target_phase) if target_phase in self.PHASE_ORDER else -1
        current_idx = self.PHASE_ORDER.index(current) if current in self.PHASE_ORDER else -1

        # 目标阶段无效
        if target_idx == -1:
            return False, f"无效的阶段: {target_phase}"

        # 已经在目标阶段或更后面的阶段
        if current_idx >= target_idx:
            return True, f"当前已在 {current} 阶段"

        # 检查前置阶段是否完成
        # 要进入 Plan，需要 Research 完成
        if target_phase == Phase.PLAN.value:
            if not state.research.completed:
                return False, "Research 阶段未完成"
            if not state.research.approved_by:
                return False, "Research 阶段未获人类审阅批准"

        # 要进入 Execute，需要 Plan 完成
        if target_phase == Phase.EXECUTE.value:
            if not state.plan.completed:
                return False, "Plan 阶段未完成"
            if not state.plan.approved_by:
                return False, "Plan 阶段未获人类审阅批准"

        # 要进入 Review，需要 Execute 完成
        if target_phase == Phase.REVIEW.value:
            if not state.execute.completed:
                return False, "Execute 阶段未完成"

        return True, "可以进入"

    def can_write_code(self) -> tuple[bool, str]:
        """
        检查当前是否允许写入代码文件

        Returns:
            (是否允许, 原因说明)
        """
        state = self.load_state()
        if not state:
            return False, "阶段状态文件不存在"

        current = state.current_phase

        # Research 和 Plan 阶段不允许写代码
        if current == Phase.RESEARCH.value:
            return False, "当前在 Research 阶段，不允许写入代码文件。请先完成 Research 并获得人类审阅批准"

        if current == Phase.PLAN.value:
            return False, "当前在 Plan 阶段，不允许写入代码文件。请先完成 Plan 并获得人类审阅批准"

        # Execute 和 Review 阶段允许写代码
        if current in [Phase.EXECUTE.value, Phase.REVIEW.value]:
            return True, f"当前在 {current} 阶段，允许写入代码"

        if current == Phase.DONE.value:
            return True, "任务已完成，允许写入代码"

        return False, f"未知阶段: {current}"

    def complete_phase(self, phase: str, approved_by: Optional[str] = None) -> bool:
        """
        标记阶段完成并推进到下一阶段

        Args:
            phase: 要完成的阶段
            approved_by: 批准者 ("human" or "agent")

        Returns:
            是否成功
        """
        state = self.load_state()
        if not state:
            return False

        now = datetime.now().isoformat()

        # 更新对应阶段的状态
        phase_state = getattr(state, phase, None)
        if phase_state:
            phase_state.completed = True
            phase_state.approved_by = approved_by
            phase_state.approved_at = now

        # 推进到下一阶段
        current_idx = self.PHASE_ORDER.index(state.current_phase)
        phase_idx = self.PHASE_ORDER.index(phase)

        if phase_idx >= current_idx:
            next_idx = min(phase_idx + 1, len(self.PHASE_ORDER) - 1)
            state.current_phase = self.PHASE_ORDER[next_idx]

        self._save_state(state)
        return True

    def update_gates(self, phase: str, total: int, completed: int) -> bool:
        """
        更新阶段的 Gates 进度

        Args:
            phase: 阶段名称
            total: 总 Gates 数
            completed: 已完成 Gates 数

        Returns:
            是否成功
        """
        state = self.load_state()
        if not state:
            return False

        phase_state = getattr(state, phase, None)
        if phase_state:
            phase_state.gates_total = total
            phase_state.gates_completed = completed

            # 如果所有 Gates 完成，自动标记阶段完成
            if total > 0 and completed >= total:
                phase_state.completed = True

            self._save_state(state)
            return True

        return False

    def get_progress(self) -> Dict:
        """
        获取整体进度

        Returns:
            进度信息字典
        """
        state = self.load_state()
        if not state:
            return {"error": "状态文件不存在"}

        return {
            "task_id": state.task_id,
            "current_phase": state.current_phase,
            "progress": {
                "research": {
                    "completed": state.research.completed,
                    "approved": bool(state.research.approved_by)
                },
                "plan": {
                    "completed": state.plan.completed,
                    "approved": bool(state.plan.approved_by),
                    "gates": f"{state.plan.gates_completed}/{state.plan.gates_total}"
                },
                "execute": {
                    "completed": state.execute.completed,
                    "gates": f"{state.execute.gates_completed}/{state.execute.gates_total}"
                },
                "review": {
                    "completed": state.review.completed
                }
            }
        }


def check_phase_for_file(task_path: str, file_path: str, project_root: str = None) -> tuple[bool, str]:
    """
    便捷函数：检查是否允许写入指定文件

    Args:
        task_path: 任务路径
        file_path: 要写入的文件路径
        project_root: 项目根目录

    Returns:
        (是否允许, 原因说明)
    """
    # 代码文件扩展名
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.vue', '.svelte'
    }

    # 非代码文件直接允许
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in CODE_EXTENSIONS:
        return True, "非代码文件，不受阶段限制"

    # 检查阶段状态
    manager = PhaseManager(task_path, project_root)
    state = manager.load_state()

    if not state:
        # 没有状态文件，可能是旧任务，允许写入（向后兼容）
        return True, "未找到阶段状态文件（向后兼容模式）"

    return manager.can_write_code()
