"""
Writer Agent - 编写剧本
"""

import json
from typing import Any, Dict


class Writer:
    """Writer - 负责编写剧本"""

    SYSTEM_PROMPT = """你是一个专业的编剧。你的任务是：
1. 根据故事结构编写详细剧本
2. 设计对白和情节
3. 确保剧情逻辑通顺
4. 把握节奏和情感冲突

请直接返回剧本内容，使用 JSON 格式。"""

    def __init__(self, client):
        self.client = client

    def write_script(self, story_structure: Dict[str, Any]) -> Dict[str, Any]:
        """编写剧本"""
        title = story_structure.get("title", "Untitled")
        scenes = story_structure.get("scenes", [])

        user_prompt = f"""请为短剧 "{title}" 编写详细剧本：

场景信息:
{json.dumps(scenes, ensure_ascii=False, indent=2)}

请返回 JSON 格式的剧本：
{{
    "title": "标题",
    "scenes": [
        {{
            "index": 1,
            "title": "场景标题",
            "description": "场景描述",
            "dialogue": [
                {{"character": "角色名", "text": "对白"}}
            ]
        }}
    ]
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
        try:
            if "{" in content_text:
                start = content_text.find("{")
                end = content_text.rfind("}") + 1
                return json.loads(content_text[start:end])
        except:
            pass

        # 降级处理
        return {
            "title": title,
            "scenes": [{"index": i + 1, "title": s.get("title", f"场景{i+1}"), "description": s.get("description", "")} for i, s in enumerate(scenes)],
        }