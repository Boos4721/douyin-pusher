"""
Prompt Engineer Agent - 优化视频生成提示词
"""

from typing import Any


class PromptEngineer:
    """Prompt Engineer - 负责优化视频生成提示词"""

    SYSTEM_PROMPT = """你是一个专业的 AI 视频提示词工程师。你的任务是：
1. 将镜头描述转换为适合 AI 视频生成的提示词
2. 添加视觉细节和氛围描述
3. 指定运镜方式
4. 添加光照和色彩描述
5. 确保提示词简洁但富有表现力

请直接返回优化后的提示词，不要添加解释。"""

    def __init__(self, client):
        self.client = client

    def optimize(self, description: str, style: str = "电影") -> str:
        """优化提示词"""
        user_prompt = f"""请优化以下镜头描述用于 AI 视频生成：

风格: {style}
描述: {description}

请返回优化后的提示词（简洁，适合 AI 视频生成），直接返回文本，不要 JSON。"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()