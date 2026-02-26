"""
诚实追问引擎
检测 Agent 理解程度并生成追问
"""

import re
from typing import List, Dict, Optional
from pathlib import Path


class HonestQuestioningEngine:
    """诚实追问引擎 - 检测理解并生成追问"""

    def __init__(self):
        """初始化引擎"""
        self.uncertainty_keywords = [
            '可能', '也许', '大概', '应该', '似乎',
            '不确定', '不清楚', '不太明白', '需要确认',
            'maybe', 'probably', 'perhaps', 'might', 'unclear'
        ]

        self.vague_patterns = [
            r'等等',
            r'之类的',
            r'或者.*或者',
            r'不太.*',
            r'有点.*'
        ]

    def detect_understanding(self, agent_response: str) -> Dict[str, any]:
        """
        检测 Agent 理解程度

        Args:
            agent_response: Agent 的回复

        Returns:
            检测结果
        """
        # 检测不确定性关键词
        uncertainty_count = sum(
            1 for keyword in self.uncertainty_keywords
            if keyword in agent_response.lower()
        )

        # 检测模糊表达
        vague_count = sum(
            1 for pattern in self.vague_patterns
            if re.search(pattern, agent_response)
        )

        # 检测问号数量（Agent 反问）
        question_count = agent_response.count('？') + agent_response.count('?')

        # 计算理解度分数 (0-100)
        understanding_score = 100
        understanding_score -= uncertainty_count * 10
        understanding_score -= vague_count * 15
        understanding_score -= question_count * 5
        understanding_score = max(0, min(100, understanding_score))

        return {
            'score': understanding_score,
            'uncertainty_count': uncertainty_count,
            'vague_count': vague_count,
            'question_count': question_count,
            'needs_clarification': understanding_score < 70
        }

    def generate_questions(self, context: str, agent_response: str) -> List[str]:
        """
        生成追问问题

        Args:
            context: 上下文（用户需求）
            agent_response: Agent 回复

        Returns:
            追问问题列表
        """
        questions = []

        # 检测理解程度
        understanding = self.detect_understanding(agent_response)

        if understanding['needs_clarification']:
            # 提取不确定的部分
            uncertain_parts = self._extract_uncertain_parts(agent_response)

            for part in uncertain_parts:
                questions.append(f"关于「{part}」，你是否确定理解了需求？")

        # 检测缺失的关键信息
        missing_info = self._detect_missing_info(context, agent_response)
        for info in missing_info:
            questions.append(f"你是否考虑了{info}？")

        # 检测假设
        assumptions = self._detect_assumptions(agent_response)
        for assumption in assumptions:
            questions.append(f"你假设了「{assumption}」，这个假设是否正确？")

        return questions

    def _extract_uncertain_parts(self, text: str) -> List[str]:
        """提取不确定的部分"""
        uncertain_parts = []

        # 查找包含不确定关键词的句子
        sentences = re.split(r'[。！？\n]', text)
        for sentence in sentences:
            for keyword in self.uncertainty_keywords:
                if keyword in sentence.lower():
                    # 提取关键短语
                    words = sentence.split()
                    if len(words) > 3:
                        uncertain_parts.append(' '.join(words[:10]) + '...')
                    else:
                        uncertain_parts.append(sentence)
                    break

        return uncertain_parts[:3]  # 最多 3 个

    def _detect_missing_info(self, context: str, response: str) -> List[str]:
        """检测缺失的关键信息"""
        missing = []

        # 关键信息类别
        key_info_categories = [
            ('性能要求', ['性能', '速度', '延迟', 'performance']),
            ('安全要求', ['安全', '权限', '认证', 'security']),
            ('错误处理', ['错误', '异常', '失败', 'error']),
            ('边界条件', ['边界', '极限', '最大', '最小', 'edge case']),
            ('兼容性', ['兼容', '版本', '浏览器', 'compatibility'])
        ]

        for category, keywords in key_info_categories:
            # 如果上下文提到但回复没提到
            context_mentions = any(kw in context.lower() for kw in keywords)
            response_mentions = any(kw in response.lower() for kw in keywords)

            if context_mentions and not response_mentions:
                missing.append(category)

        return missing

    def _detect_assumptions(self, text: str) -> List[str]:
        """检测假设"""
        assumptions = []

        # 假设关键词
        assumption_patterns = [
            r'假设(.*?)(?=[。，])',
            r'假定(.*?)(?=[。，])',
            r'认为(.*?)(?=[。，])',
            r'应该是(.*?)(?=[。，])'
        ]

        for pattern in assumption_patterns:
            matches = re.findall(pattern, text)
            assumptions.extend(matches[:2])  # 最多 2 个

        return assumptions

    def create_ai_question_annotation(
        self,
        question: str,
        context: str,
        location: str
    ) -> Dict[str, str]:
        """
        创建 AI 追问标注

        Args:
            question: 追问问题
            context: 上下文
            location: 位置

        Returns:
            标注数据
        """
        return {
            'type': 'AI_QUESTION',
            'status': 'pending_ai_question',
            'question': question,
            'context': context,
            'location': location,
            'timestamp': None  # 由调用者填充
        }

    def should_ask_question(self, understanding_score: int) -> bool:
        """
        判断是否应该追问

        Args:
            understanding_score: 理解度分数

        Returns:
            是否应该追问
        """
        return understanding_score < 70
