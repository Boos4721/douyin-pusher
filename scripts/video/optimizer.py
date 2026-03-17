"""
提示词优化模块

使用 AI 优化视频生成提示词
"""

import os
from typing import Optional

from openai import OpenAI


class PromptOptimizer:
    """提示词优化器"""

    SYSTEM_PROMPT = """你是一个专业的视频生成提示词优化专家。

请根据以下原则优化用户的提示词：
1. 添加详细的场景描述和视觉细节
2. 指定合适的运镜方式（推、拉、摇、移、跟拍等）
3. 添加光照和氛围描述
4. 确保提示词适合 AI 视频生成
5. 保持简洁但富有表现力

请直接返回优化后的提示词，不要添加解释。"""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def optimize(self, prompt: str) -> str:
        """优化提示词"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()


# 兼容旧接口
class Optimizer:
    """提示词优化器 - 兼容旧接口"""

    def __init__(self, model: str = "gpt-4o", **kwargs):
        self.optimizer = PromptOptimizer(model=model, **kwargs)

    def optimize(self, prompt: str) -> str:
        """优化提示词"""
        return self.optimizer.optimize(prompt)