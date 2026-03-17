"""
Shot Designer Agent - 设计镜头
"""

import json
from typing import Any, Dict, List

from ..generator import VideoGenerator


class ShotDesigner:
    """Shot Designer - 负责设计镜头"""

    SYSTEM_PROMPT = """你是一个专业的分镜设计师。你的任务是：
1. 根据剧本设计具体镜头
2. 指定镜头类型（远景、全景、中景、近景、特写）
3. 指定运镜方式（推、拉、摇、移、跟拍等）
4. 规划镜头时长
5. 描述画面内容

请直接返回分镜信息，使用 JSON 格式。"""

    def __init__(self, client):
        self.client = client

    def design_shots(self, script: Dict[str, Any], total_shots: int) -> List[Any]:
        """设计镜头"""
        scenes = script.get("scenes", [])
        title = script.get("title", "Untitled")

        # 计算每个场景的镜头数
        shots_per_scene = max(1, total_shots // max(1, len(scenes)))

        user_prompt = f"""请为短剧 "{title}" 设计 {total_shots} 个镜头：

剧本:
{json.dumps(scenes, ensure_ascii=False, indent=2)}

请为每个场景设计镜头，返回 JSON 格式：
{{
    "scenes": [
        {{
            "index": 1,
            "title": "场景标题",
            "shots": [
                {{
                    "index": 1,
                    "description": "镜头描述",
                    "duration": 5,
                    "camera_angle": "中景",
                    "movement": "推",
                    "action": "角色动作"
                }}
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
                data = json.loads(content_text[start:end])

                # 转换为 Scene 对象
                from .main import Scene, Shot
                result = []
                for scene_data in data.get("scenes", []):
                    shots = []
                    for shot_data in scene_data.get("shots", []):
                        shots.append(Shot(
                            index=shot_data.get("index", len(shots) + 1),
                            description=shot_data.get("description", ""),
                            duration=shot_data.get("duration", 5),
                            camera_angle=shot_data.get("camera_angle", "中景"),
                            action=shot_data.get("action", ""),
                        ))
                    result.append(Scene(
                        index=scene_data.get("index", len(result) + 1),
                        title=scene_data.get("title", ""),
                        shots=shots,
                    ))
                return result
        except Exception as e:
            print(f"   警告: 镜头解析失败，使用默认设计: {e}")

        # 降级处理：自动生成镜头
        from .main import Scene, Shot
        result = []
        shot_index = 1
        for i, scene in enumerate(scenes):
            shots = []
            for j in range(shots_per_scene):
                shots.append(Shot(
                    index=shot_index,
                    description=scene.get("description", ""),
                    duration=5,
                    camera_angle="中景",
                    action="角色动作",
                ))
                shot_index += 1
            result.append(Scene(
                index=i + 1,
                title=scene.get("title", f"场景{i+1}"),
                shots=shots,
            ))
        return result