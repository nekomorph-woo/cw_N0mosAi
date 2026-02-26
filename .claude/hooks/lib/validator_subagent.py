"""
Validator Subagent
审查 research.md 和 plan.md，检查 Protected Interfaces
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """验证问题"""
    severity: str  # CRITICAL/MAJOR/MINOR
    category: str  # 分类
    message: str   # 问题描述
    suggestion: str  # 修复建议
    location: str  # 位置（文件:行号）


class ValidatorSubagent:
    """Validator Subagent - 审查文档质量"""

    def __init__(self, task_path: str):
        """
        初始化 Validator

        Args:
            task_path: 任务路径
        """
        self.task_path = Path(task_path)

    def validate_research(self) -> List[ValidationIssue]:
        """
        验证 research.md

        Returns:
            问题列表
        """
        issues = []
        research_file = self.task_path / 'research.md'

        if not research_file.exists():
            issues.append(ValidationIssue(
                severity='CRITICAL',
                category='文件缺失',
                message='research.md 不存在',
                suggestion='创建 research.md 文件',
                location='research.md'
            ))
            return issues

        with open(research_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查必需章节
        required_sections = [
            ('需求理解', 'research.md:需求理解'),
            ('代码调研', 'research.md:代码调研'),
            ('Protected Interfaces', 'research.md:Protected Interfaces'),
            ('Why Questions', 'research.md:Why Questions')
        ]

        for section, location in required_sections:
            if section not in content:
                issues.append(ValidationIssue(
                    severity='MAJOR',
                    category='章节缺失',
                    message=f'缺少必需章节: {section}',
                    suggestion=f'添加 {section} 章节',
                    location=location
                ))

        # 检查 Why Questions 是否回答
        if 'Why Questions' in content:
            why_section = self._extract_section(content, 'Why Questions')
            if '（待填充）' in why_section or len(why_section) < 100:
                issues.append(ValidationIssue(
                    severity='MAJOR',
                    category='内容不完整',
                    message='Why Questions 未充分回答',
                    suggestion='回答所有 Why 问题，每个问题至少 2-3 句话',
                    location='research.md:Why Questions'
                ))

        # 检查 Protected Interfaces
        if 'Protected Interfaces' in content:
            pi_section = self._extract_section(content, 'Protected Interfaces')
            if '（待填充）' in pi_section or len(pi_section) < 50:
                issues.append(ValidationIssue(
                    severity='MINOR',
                    category='内容不完整',
                    message='Protected Interfaces 未明确列出',
                    suggestion='列出所有不可修改的接口和原因',
                    location='research.md:Protected Interfaces'
                ))

        # 检查 YAML Frontmatter
        if not content.startswith('---'):
            issues.append(ValidationIssue(
                severity='MINOR',
                category='格式问题',
                message='缺少 YAML Frontmatter',
                suggestion='添加 YAML Frontmatter（task_id, created, status）',
                location='research.md:1'
            ))

        return issues

    def validate_plan(self) -> List[ValidationIssue]:
        """
        验证 plan.md

        Returns:
            问题列表
        """
        issues = []
        plan_file = self.task_path / 'plan.md'

        if not plan_file.exists():
            issues.append(ValidationIssue(
                severity='CRITICAL',
                category='文件缺失',
                message='plan.md 不存在',
                suggestion='创建 plan.md 文件',
                location='plan.md'
            ))
            return issues

        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查必需章节
        required_sections = [
            ('目标', 'plan.md:目标'),
            ('架构设计', 'plan.md:架构设计'),
            ('Phase Gates', 'plan.md:Phase Gates'),
            ('实施步骤', 'plan.md:实施步骤')
        ]

        for section, location in required_sections:
            if section not in content:
                issues.append(ValidationIssue(
                    severity='MAJOR',
                    category='章节缺失',
                    message=f'缺少必需章节: {section}',
                    suggestion=f'添加 {section} 章节',
                    location=location
                ))

        # 检查 Phase Gates
        if 'Phase Gates' in content:
            gates = re.findall(r'- \[[ x]\] (Gate \d+\.\d+:.*)', content)
            if len(gates) == 0:
                issues.append(ValidationIssue(
                    severity='CRITICAL',
                    category='内容缺失',
                    message='没有定义 Phase Gates',
                    suggestion='定义至少 3 个 Phase Gates',
                    location='plan.md:Phase Gates'
                ))
            elif len(gates) < 3:
                issues.append(ValidationIssue(
                    severity='MINOR',
                    category='内容不足',
                    message=f'Phase Gates 数量较少（{len(gates)} 个）',
                    suggestion='建议定义至少 3 个 Phase Gates',
                    location='plan.md:Phase Gates'
                ))

        # 检查是否有未处理的 Review Comments
        critical_pending = re.findall(
            r'### RC-\d+:.*?CRITICAL.*?pending',
            content,
            re.DOTALL
        )
        major_pending = re.findall(
            r'### RC-\d+:.*?MAJOR.*?pending',
            content,
            re.DOTALL
        )

        if critical_pending:
            issues.append(ValidationIssue(
                severity='CRITICAL',
                category='Review Comments',
                message=f'有 {len(critical_pending)} 个 CRITICAL Review Comments 未处理',
                suggestion='处理所有 CRITICAL Review Comments',
                location='plan.md:Review Comments'
            ))

        if major_pending:
            issues.append(ValidationIssue(
                severity='MAJOR',
                category='Review Comments',
                message=f'有 {len(major_pending)} 个 MAJOR Review Comments 未处理',
                suggestion='处理所有 MAJOR Review Comments',
                location='plan.md:Review Comments'
            ))

        return issues

    def validate_protected_interfaces(self, code_files: List[str]) -> List[ValidationIssue]:
        """
        检查是否修改了 Protected Interfaces

        Args:
            code_files: 修改的代码文件列表

        Returns:
            问题列表
        """
        issues = []

        # 读取 research.md 中的 Protected Interfaces
        research_file = self.task_path / 'research.md'
        if not research_file.exists():
            return issues

        with open(research_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 Protected Interfaces
        pi_section = self._extract_section(content, 'Protected Interfaces')
        if not pi_section:
            return issues

        # 简单检查：查找接口名称
        # 实际实现中应该使用 AST 解析
        protected_patterns = re.findall(r'`([^`]+)`', pi_section)

        for code_file in code_files:
            if not os.path.exists(code_file):
                continue

            with open(code_file, 'r', encoding='utf-8') as f:
                code_content = f.read()

            for pattern in protected_patterns:
                # 检查是否修改了 protected interface
                if f'def {pattern}' in code_content or f'class {pattern}' in code_content:
                    issues.append(ValidationIssue(
                        severity='CRITICAL',
                        category='Protected Interface',
                        message=f'可能修改了 Protected Interface: {pattern}',
                        suggestion=f'确认是否真的需要修改 {pattern}，如果是，请在 research.md 中说明原因',
                        location=f'{code_file}:{pattern}'
                    ))

        return issues

    def generate_checklist(self) -> Dict[str, List[str]]:
        """
        生成审查 Checklist

        Returns:
            Checklist 字典
        """
        return {
            'Research 审查': [
                '需求理解是否清晰？',
                '代码调研是否充分？',
                'Protected Interfaces 是否明确？',
                'Why Questions 是否回答？',
                '是否有遗漏的关键信息？'
            ],
            'Plan 审查': [
                '目标是否明确可验证？',
                '架构设计是否合理？',
                'Phase Gates 是否完整？',
                '实施步骤是否详细？',
                '风险是否识别？'
            ],
            'Protected Interfaces': [
                '是否列出所有不可修改的接口？',
                '是否说明了不可修改的原因？',
                '是否有替代方案？'
            ],
            'Review Comments': [
                '所有 CRITICAL 是否 addressed？',
                '所有 MAJOR 是否 addressed？',
                'MINOR 是否合理处理？'
            ]
        }

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        提取章节内容

        Args:
            content: 文档内容
            section_name: 章节名称

        Returns:
            章节内容
        """
        # 查找章节
        pattern = rf'##+ {re.escape(section_name)}\n\n(.*?)(?=\n##+ |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        return ''

    def run_validation(self) -> Dict[str, List[ValidationIssue]]:
        """
        运行完整验证

        Returns:
            验证结果
        """
        return {
            'research': self.validate_research(),
            'plan': self.validate_plan()
        }
