"""
ShowRunner Agent - 规划短剧整体结构
"""

from typing import Any, Dict


class ShowRunner:
    """ShowRunner - 负责规划短剧整体结构"""

    SYSTEM_PROMPT = """你是一个专业的短剧策划专家（ShowRunner）。你的任务是：
1. 分析用户的需求和创意
2. 规划短剧的整体结构
3. 确定剧情走向和情感基调
4. 设计主要场景

请直接返回结构化的剧情规划，不要添加解释。"""

    def __init__(self, client):
        self.client = client

    def create_story(self, content: str, style: str, num_shots: int) -> Dict[str, Any]:
        """创建故事结构"""
        user_prompt = f"""请为以下内容创建短剧规划：

内容: {content}
风格: {style}
镜头数: {num_shots}

请返回 JSON 格式的规划：
{{
    "title": "标题",
    "genre": "类型",
    "mood": "情感基调",
    "duration": "总时长",
    "scenes": [
        {{"index": 1, "title": "场景标题", "description": "场景描述"}}
    ],
    "characters": ["角色1", "角色2"]
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        content_text = response.choices[0].message.content
        # 简单解析 JSON
        import json
        try:
            # 尝试提取 JSON
            if "{" in content_text:
                start = content_text.find("{")
                end = content_text.rfind("}") + 1
                json_str = content_text[start:end]
                return json.loads(json_str)
        except:
            pass

        # 如果解析失败，返回基本结构
        return {
            "title": content[:20],
            "style": style,
            "scenes": [{"index": i + 1, "title": f"场景{i+1}", "description": content} for i in range(num_shots)],
        }