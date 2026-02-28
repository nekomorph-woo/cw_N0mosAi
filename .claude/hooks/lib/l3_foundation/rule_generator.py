"""
规则生成模块 - 从 plan.md 自动生成规则脚本

l3_foundation 基础能力层核心模块
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .rule_context import RuleContext
from .ai_client import AIClient
from .prompt_builder import (
    PromptTemplate,
    COMMAND_HANDLER_TEMPLATE,
    PROMPT_HANDLER_TEMPLATE
)


class RuleSpec:
    """规则规范"""

    def __init__(self, index: int, description: str, handler_type: str = "command",
                 severity: str = "warning", target_files: List[str] = None,
                 details: str = ""):
        self.index = index
        self.description = description
        self.handler_type = handler_type
        self.severity = severity
        self.target_files = target_files or []
        self.details = details

        # 缓存规则名称
        self._rule_name = self._generate_rule_name()

    def _generate_rule_name(self) -> str:
        """生成规则名称 (snake_case)"""
        # 常见关键词映射 (中文 -> 英文)
        keywords_map = {
            "trace": "trace_id",
            "api": "api",
            "返回": "return",
            "敏感": "sensitive",
            "数据": "data",
            "日志": "log",
            "logger": "logger",
            "密码": "password",
            "密钥": "key",
            "token": "token",
            "错误": "error",
            "处理": "handler",
            "接口": "interface",
            "模块": "module",
            "隔离": "isolation",
            "国际化": "i18n",
        }

        # 从描述中提取英文单词和映射的关键词
        words = []
        description_lower = self.description.lower()

        # 1. 提取英文单词
        for word in re.findall(r'[a-z]+', description_lower):
            if len(word) >= 3:
                words.append(word)

        # 2. 检查映射关键词
        for cn, en in keywords_map.items():
            if cn in self.description and en not in words:
                words.append(en)

        # 去重并取前 4 个
        seen = set()
        unique_words = []
        for w in words:
            if w not in seen:
                unique_words.append(w)
                seen.add(w)

        if len(unique_words) >= 2:
            return "_".join(unique_words[:4])
        else:
            # 如果没有足够的单词，使用规则编号
            return f"rule_{self.index}"

    @property
    def rule_name(self) -> str:
        """获取规则名称 (snake_case)"""
        return self._rule_name

    @property
    def class_name(self) -> str:
        """生成类名 (PascalCase)"""
        # 将 snake_case 转换为 PascalCase
        return "".join(word.capitalize() for word in self.rule_name.split("_"))


class RuleGenerator:
    """规则生成器 - 从 plan.md 生成规则脚本"""

    def __init__(self, task_dir: str = None):
        """
        初始化生成器

        Args:
            task_dir: task 目录路径 (None=自动检测)
        """
        self.context = RuleContext()
        if task_dir:
            self.context._task_dir = task_dir

        self.ai_client = AIClient()

    def parse_business_rules(self, plan_content: str = None) -> List[RuleSpec]:
        """
        从 plan.md 解析业务规则

        Args:
            plan_content: plan.md 内容 (None=自动读取)

        Returns:
            规则规范列表
        """
        if plan_content is None:
            plan_content = self.context.plan_content

        if not plan_content:
            return []

        # 查找业务规则章节
        lines = plan_content.split('\n')
        rules_start = -1

        for i, line in enumerate(lines):
            if line.strip() == "## 业务规则":
                rules_start = i
                break

        if rules_start == -1:
            return []

        # 提取业务规则内容 (到下一个二级标题或文件结束)
        rules_lines = []
        for i in range(rules_start + 1, len(lines)):
            if lines[i].startswith("## ") and i > rules_start + 1:
                break
            rules_lines.append(lines[i])

        rules_text = '\n'.join(rules_lines)

        # 解析规则 (支持两种格式)
        return self._parse_rules_format(rules_text)

    def _parse_rules_format(self, rules_text: str) -> List[RuleSpec]:
        """
        解析规则文本

        支持两种格式:
        1. Markdown 列表格式 (新模板)
        2. 纯文本编号列表 (旧格式兼容)
        """
        rules = []
        current_rule = None

        lines = rules_text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            orig_line = lines[i]  # 保留原始行用于检查

            # 跳过空行
            if not line:
                i += 1
                continue

            # 格式 1: "#### 规则 N: [规则名称]" (必须在跳过 # 之前检查)
            if line.startswith("#### 规则") or line.startswith("#### Rule"):
                if current_rule:
                    rules.append(current_rule)

                # 提取规则名称
                parts = line.split(":", 1)
                rule_name = parts[1].strip() if len(parts) > 1 else f"Rule {len(rules) + 1}"

                current_rule = {
                    "name": rule_name,
                    "description": rule_name,
                    "handler": "command",
                    "severity": "warning",
                    "files": [],
                    "details": ""
                }
                i += 1
                continue

            # 跳过其他章节标题
            if line.startswith("#"):
                i += 1
                continue
                if current_rule:
                    rules.append(current_rule)

                # 提取规则名称
                parts = line.split(":", 1)
                rule_name = parts[1].strip() if len(parts) > 1 else f"Rule {len(rules) + 1}"

                current_rule = {
                    "name": rule_name,
                    "description": rule_name,
                    "handler": "command",
                    "severity": "warning",
                    "files": [],
                    "details": ""
                }

            # 格式 2: "N. [描述]" (编号列表)
            elif re.match(r'^\d+\.\s+', line):
                if current_rule:
                    rules.append(current_rule)

                parts = line.split(". ", 1)
                current_rule = {
                    "name": f"Rule {parts[0]}",
                    "description": parts[1] if len(parts) > 1 else "",
                    "handler": "command",
                    "severity": "warning",
                    "files": [],
                    "details": ""
                }

            # 规则属性
            elif current_rule:
                # 处理带 - 前缀的属性行
                attr_line = line.lstrip("- ").strip()  # 移除前缀的 "- "

                if "**描述**:" in attr_line or "描述:" in attr_line:
                    current_rule["description"] = attr_line.split(":", 1)[1].strip()

                elif "**Handler**:" in attr_line or "Handler:" in attr_line:
                    handler = attr_line.split(":", 1)[1].strip().lower()
                    if "`" in handler:
                        handler = handler.split("`")[1].split("`")[0]
                    current_rule["handler"] = handler

                elif "**严重程度**:" in attr_line or "严重程度:" in attr_line:
                    severity = attr_line.split(":", 1)[1].strip().lower()
                    if "`" in severity:
                        severity = severity.split("`")[1].split("`")[0]
                    current_rule["severity"] = severity

                elif "**目标文件**:" in attr_line or "目标文件:" in attr_line:
                    files = attr_line.split(":", 1)[1].strip()
                    if "`" in files:
                        files = files.split("`")[1].split("`")[0]
                    current_rule["files"] = [f.strip() for f in files.split(",")]

                elif "**详细说明**:" in attr_line or "详细说明:" in attr_line:
                    # 详细说明可能跨多行
                    detail_lines = []
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        # 停止条件: 空行、新规则标题、新属性
                        if (not next_line or
                            next_line.startswith("####") or
                            (next_line.startswith("-") and
                             ("**" in next_line or next_line.startswith("- #")))):
                            break
                        if next_line:  # 只添加非空行
                            detail_lines.append(next_line)
                        j += 1
                    current_rule["details"] = "\n".join(detail_lines)
                    i = j - 1  # 调整索引

            i += 1

        if current_rule:
            rules.append(current_rule)

        # 转换为 RuleSpec 对象
        specs = []
        for i, rule in enumerate(rules, 1):
            specs.append(RuleSpec(
                index=i,
                description=rule.get("description", ""),
                handler_type=rule.get("handler", "command"),
                severity=rule.get("severity", "warning"),
                target_files=rule.get("files", []),
                details=rule.get("details", "")
            ))

        return specs

    def generate_rule_script(self, rule_spec: RuleSpec) -> Optional[str]:
        """
        生成规则脚本

        Args:
            rule_spec: 规则规范

        Returns:
            生成的 Python 脚本，失败返回 None
        """
        if not self.ai_client.available:
            print("⚠️  AI 服务不可用，无法生成规则脚本")
            return None

        # 选择模板
        if rule_spec.handler_type == "prompt":
            template = PROMPT_HANDLER_TEMPLATE
        else:
            template = COMMAND_HANDLER_TEMPLATE

        # 填充模板
        prompt = template.render(
            task_id=self.context.task_id or "unknown",
            task_dir=self.context.task_dir or ".",
            project_root=str(self.context.project_root or "."),
            rule_description=self._format_rule_description(rule_spec)
        )

        # 调用 AI 生成
        result = self.ai_client.call(prompt, "", max_tokens=4096)

        if not result:
            return None

        # 提取 Python 代码块
        script_content = result.get("raw_response", str(result))
        code_match = re.search(r'```python\s*([\s\S]*?)\s*```', script_content)
        if code_match:
            return code_match.group(1)
        else:
            # 尝试提取任何代码块
            any_match = re.search(r'```\s*([\s\S]*?)\s*```', script_content)
            if any_match:
                return any_match.group(1)
            return script_content

    def _format_rule_description(self, rule_spec: RuleSpec) -> str:
        """格式化规则描述供 AI 使用"""
        parts = [
            f"规则名称: {rule_spec.rule_name}",
            f"规则描述: {rule_spec.description}",
            f"Handler 类型: {rule_spec.handler_type}",
            f"严重程度: {rule_spec.severity}",
        ]

        if rule_spec.target_files:
            parts.append(f"目标文件: {', '.join(rule_spec.target_files)}")

        if rule_spec.details:
            parts.append(f"\n详细说明:\n{rule_spec.details}")

        return "\n".join(parts)

    def save_rule_script(self, script: str, rule_spec: RuleSpec) -> Optional[str]:
        """
        保存规则脚本到 task/rules/ 目录

        Args:
            script: 脚本内容
            rule_spec: 规则规范

        Returns:
            保存的文件路径，失败返回 None
        """
        task_dir = self.context.task_dir
        if not task_dir:
            print("⚠️  无法确定 task 目录")
            return None

        rules_dir = Path(task_dir) / "rules"
        rules_dir.mkdir(exist_ok=True)

        script_path = rules_dir / f"{rule_spec.rule_name}.py"

        # 添加头部注释
        header = f'''# Auto-generated by Nomos
# Task: {self.context.task_id or "unknown"}
# Rule: {rule_spec.rule_name}
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
# Source: plan.md 业务规则 #{rule_spec.index}
#
# ⚠️  此文件由 AI 自动生成，请 review 后使用
# 如需修改规则，请直接编辑此文件

'''

        script_with_header = header + script

        try:
            script_path.write_text(script_with_header, encoding='utf-8')
            print(f"✅ 规则脚本已生成: {script_path}")
            return str(script_path)
        except IOError as e:
            print(f"❌ 保存失败: {e}")
            return None

    def generate_all_rules(self) -> List[str]:
        """
        生成所有规则脚本

        Returns:
            生成的脚本路径列表
        """
        rule_specs = self.parse_business_rules()
        if not rule_specs:
            print("ℹ️  没有找到业务规则")
            return []

        print(f"📝 找到 {len(rule_specs)} 个业务规则，开始生成...")

        generated = []
        for spec in rule_specs:
            print(f"  → 生成规则: {spec.rule_name}")
            script = self.generate_rule_script(spec)
            if script:
                path = self.save_rule_script(script, spec)
                if path:
                    generated.append(path)

        return generated


class RuleSyncer:
    """规则同步器 - plan.md 变更时同步规则脚本"""

    def __init__(self, task_dir: str = None):
        """
        初始化同步器

        Args:
            task_dir: task 目录路径 (None=自动检测)
        """
        self.context = RuleContext()
        if task_dir:
            self.context._task_dir = task_dir

        self.generator = RuleGenerator(task_dir)

    def sync_on_plan_change(self, old_plan: str, new_plan: str) -> Dict[str, Any]:
        """
        plan.md 变更时同步规则脚本

        Args:
            old_plan: 旧的 plan.md 内容
            new_plan: 新的 plan.md 内容

        Returns:
            同步结果报告
        """
        old_rules = self.generator.parse_business_rules(old_plan)
        new_rules = self.generator.parse_business_rules(new_plan)

        diff = self._compute_diff(old_rules, new_rules)

        report = {
            "added": [],
            "changed": [],
            "deleted": [],
            "skipped": []
        }

        # 处理新增规则
        for rule in diff["added"]:
            script = self.generator.generate_rule_script(rule)
            if script:
                path = self.generator.save_rule_script(script, rule)
                if path:
                    report["added"].append({"rule": rule.rule_name, "path": path})

        # 处理修改规则
        for rule in diff["changed"]:
            script_path = Path(self.context.rules_dir) / f"{rule.rule_name}.py"
            if script_path.exists():
                if self._has_user_modifications(script_path):
                    report["skipped"].append({
                        "rule": rule.rule_name,
                        "reason": "用户已修改，需要手动确认"
                    })
                else:
                    script = self.generator.generate_rule_script(rule)
                    if script:
                        path = self.generator.save_rule_script(script, rule)
                        if path:
                            report["changed"].append({"rule": rule.rule_name, "path": path})

        # 处理删除规则
        for rule in diff["deleted"]:
            script_path = Path(self.context.rules_dir) / f"{rule.rule_name}.py"
            if script_path.exists():
                script_path.unlink()
                report["deleted"].append({"rule": rule.rule_name})

        return report

    def _compute_diff(self, old_rules: List[RuleSpec], new_rules: List[RuleSpec]) -> Dict[str, List]:
        """计算规则差异"""
        old_map = {r.rule_name: r for r in old_rules}
        new_map = {r.rule_name: r for r in new_rules}

        added = [r for r in new_rules if r.rule_name not in old_map]
        deleted = [r for r in old_rules if r.rule_name not in new_map]

        # 检查修改 (描述或 handler 类型变化)
        changed = []
        for name in new_map:
            if name in old_map:
                old = old_map[name]
                new = new_map[name]
                if (old.description != new.description or
                    old.handler_type != new.handler_type):
                    changed.append(new)

        return {"added": added, "changed": changed, "deleted": deleted}

    def _has_user_modifications(self, script_path: Path) -> bool:
        """
        检查脚本是否被用户修改过

        通过检查脚本头部的生成时间戳和文件修改时间
        """
        content = script_path.read_text(encoding='utf-8')

        # 提取生成时间戳
        match = re.search(r'# Generated: (.+)', content)
        if not match:
            return True  # 没有时间戳，认为是用户修改过

        generated_time_str = match.group(1)
        try:
            generated_time = datetime.strptime(generated_time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return True

        # 检查文件修改时间
        file_mtime = datetime.fromtimestamp(script_path.stat().st_mtime)

        # 如果文件修改时间晚于生成时间 5 分钟以上，认为是用户修改过
        return (file_mtime - generated_time).total_seconds() > 300


# 便捷函数
def generate_rules_from_plan(task_dir: str = None) -> List[str]:
    """
    从 plan.md 生成所有规则脚本

    Args:
        task_dir: task 目录路径 (None=自动检测)

    Returns:
        生成的脚本路径列表
    """
    generator = RuleGenerator(task_dir)
    return generator.generate_all_rules()
