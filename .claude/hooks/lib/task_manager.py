"""
Task 状态管理器
负责任务文件夹的创建、切换和状态管理
"""

import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict
from pathlib import Path

# 延迟导入避免循环依赖
def _import_phase_manager():
    from .phase_manager import PhaseManager
    return PhaseManager


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str           # t1
    full_id: str           # t1-2026-02-26-user-login
    path: str              # tasks/t1-2026-02-26-user-login
    status: str            # draft/in_review/approved/executing/done
    created: str           # ISO 8601


class TaskManager:
    """Task 状态管理器"""

    TASKS_DIR = "tasks"
    MAPPING_FILE = "tasks/short-id-mapping.json"
    CURRENT_TASK_FILE = ".claude/current-task.txt"
    TEMPLATES_DIR = ".claude/skills/nomos/templates"

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

    def set_current_task(self, task_id: str) -> bool:
        """设置当前任务"""
        mapping = self._load_mapping()
        if task_id not in mapping:
            return False

        task_path = mapping[task_id]["path"]
        self.current_task_file.write_text(task_path)
        return True

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

    def _load_mapping(self) -> dict:
        """加载 short-id-mapping.json"""
        if not self.mapping_file.exists():
            return {}

        try:
            with open(self.mapping_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_mapping(self, mapping: dict) -> None:
        """保存 short-id-mapping.json"""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.mapping_file, "w") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

    def _init_templates(self, task_path: Path, task_info: TaskInfo) -> None:
        """从模板初始化四件套，替换占位符"""
        placeholders = {
            "{TASK_ID}": task_info.task_id,
            "{FULL_ID}": task_info.full_id,
            "{CREATED}": task_info.created,
            "{STATUS}": "draft",
            "{TASK_NAME}": "-".join(task_info.full_id.split("-")[3:]) if len(task_info.full_id.split("-")) > 3 else ""
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

    def _get_default_template(self, template_name: str, task_info: TaskInfo) -> str:
        """获取默认模板内容"""
        base_frontmatter = f"""---
task_id: {task_info.task_id}
created: {task_info.created}
status: draft
---

"""

        if template_name == "research.md":
            return base_frontmatter + f"# Research - {task_info.full_id}\n\n（待填充）\n"
        elif template_name == "plan.md":
            return base_frontmatter + f"# Plan - {task_info.full_id}\n\n（待填充）\n"
        elif template_name == "code_review.md":
            return base_frontmatter + f"# Code Review - {task_info.full_id}\n\n（待填充）\n"
        elif template_name == "progress.md":
            return base_frontmatter + f"# Progress - {task_info.full_id}\n\n（待填充）\n"
        else:
            return base_frontmatter

    def _init_phase_state(self, task_path: Path, task_info: TaskInfo) -> None:
        """初始化阶段状态文件"""
        try:
            PhaseManager = _import_phase_manager()
            pm = PhaseManager(str(task_path), str(self.project_root))
            pm.initialize(task_info.task_id)
        except Exception:
            # 如果初始化失败，不影响任务创建
            pass
