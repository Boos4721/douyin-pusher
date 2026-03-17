"""
短剧生成器 - 6 Agent 协作 (showrunner → writer → shot → prompt → generator → editor → finalizer)
"""

import os
from dataclasses import dataclass
from typing import List, Optional

from openai import OpenAI

from .showrunner import ShowRunner
from .writer import Writer
from .shot import ShotDesigner
from .prompt import PromptEngineer
from .generator import VideoGenerator as MovieVideoGenerator
from .editor import VideoEditor
from .finalizer import Finalizer


@dataclass
class Shot:
    """镜头"""
    index: int
    description: str
    duration: int
    camera_angle: str
    action: str
    prompt: str = ""


@dataclass
class Scene:
    """场景"""
    index: int
    title: str
    shots: List[Shot]


class MovieGenerator:
    """短剧生成器 - 6 Agent 协作"""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        video_model: str = "auto",
        **video_kwargs,
    ):
        self.client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))

        # 初始化 6 个 Agent
        self.showrunner = ShowRunner(self.client)
        self.writer = Writer(self.client)
        self.shot_designer = ShotDesigner(self.client)
        self.prompt_engineer = PromptEngineer(self.client)
        self.video_generator = MovieVideoGenerator(model=video_model, **video_kwargs)
        self.editor = VideoEditor()
        self.finalizer = Finalizer()

    def generate(
        self,
        content: str,
        style: str = "电影",
        num_shots: int = 6,
        output_dir: str = "output/movie",
    ) -> str:
        """
        生成短剧

        Args:
            content: 短剧内容描述
            style: 风格 (电影、动画、纪录片等)
            num_shots: 镜头数量
            output_dir: 输出目录

        Returns:
            最终视频路径
        """
        print(f"\n🎬 开始生成短剧: {content}")
        print(f"   风格: {style}, 镜头数: {num_shots}")
        print("=" * 50)

        # Step 1: ShowRunner - 规划整体结构
        print("\n[1/6] 📋 ShowRunner 规划剧情结构...")
        story_structure = self.showrunner.create_story(content, style, num_shots)
        print(f"   故事结构: {story_structure.get('title', 'Untitled')}")

        # Step 2: Writer - 编写剧本
        print("\n[2/6] ✍️ Writer 编写剧本...")
        script = self.writer.write_script(story_structure)
        print(f"   场景数: {len(script.get('scenes', []))}")

        # Step 3: Shot Designer - 设计镜头
        print("\n[3/6] 🎥 Shot Designer 设计镜头...")
        scenes = self.shot_designer.design_shots(script, num_shots)
        print(f"   镜头总数: {sum(len(s.shots) for s in scenes)}")

        # Step 4: Prompt Engineer - 优化提示词
        print("\n[4/6] 🔧 Prompt Engineer 优化提示词...")
        for scene in scenes:
            for shot in scene.shots:
                shot.prompt = self.prompt_engineer.optimize(shot.description, style)
        print("   提示词优化完成")

        # Step 5: Generator - 生成视频
        print("\n[5/6] 🎬 Generator 生成视频...")
        video_paths = []
        for scene in scenes:
            for shot in scene.shots:
                print(f"   生成镜头 {shot.index}: {shot.description[:30]}...")
                video_url = self.video_generator.generate(
                    shot.prompt,
                    duration=shot.duration,
                )
                local_path = self.video_generator.download(video_url, f"{output_dir}/shot_{shot.index}.mp4")
                video_paths.append(local_path)

        # Step 6: Editor - 剪辑视频
        print("\n[6/6] ✂️ Editor 剪辑合成...")
        final_path = self.editor.concat_videos(video_paths, f"{output_dir}/final.mp4")

        # Finalizer - 最终处理
        print("\n✅ Finalizer 最终处理...")
        self.finalizer.finalize(final_path)

        print(f"\n{'=' * 50}")
        print(f"🎉 短剧生成完成: {final_path}")
        return final_path


# 兼容旧接口
class Generator:
    """短剧生成器 - 兼容旧接口"""

    def __init__(self, **kwargs):
        self._gen = MovieGenerator(**kwargs)

    def generate(self, style: str = "电影", content: str = "", **kwargs) -> str:
        return self._gen.generate(content=content, style=style, **kwargs)