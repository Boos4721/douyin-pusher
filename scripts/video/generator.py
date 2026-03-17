"""
统一视频生成器 - 支持多种模型 (Jimeng, Seedance, Sora)

支持的模型:
- jimeng-pro: 即梦AI 3.0 Pro (图生视频/文生视频)
- jimeng-720p: 即梦AI 720p (文生视频)
- jimeng-1080p: 即梦AI 1080p (文生视频)
- seedance: 火山引擎 Seedance
- sora: Atlas Cloud Sora
- auto: 自动选择最佳模型
"""

import os
import time
import uuid
from typing import Optional

import requests

from .jimeng import JimengGenerator
from .volc import VolcengineSeedanceGenerator
from .atlas import AtlasSoraGenerator


class VideoGenerator:
    """统一视频生成器"""

    MODELS = {
        "jimeng-pro": {"class": "JimengGenerator", "supports_image": True, "max_duration": 10},
        "jimeng-720p": {"class": "JimengGenerator", "supports_image": False, "max_duration": 10},
        "jimeng-1080p": {"class": "JimengGenerator", "supports_image": False, "max_duration": 10},
        "seedance": {"class": "VolcengineSeedanceGenerator", "supports_image": True, "max_duration": 10},
        "sora": {"class": "AtlasSoraGenerator", "supports_image": False, "max_duration": 10},
    }

    def __init__(
        self,
        model: str = "auto",
        api_key: Optional[str] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化视频生成器

        Args:
            model: 模型名称 (jimeng-pro, jimeng-720p, jimeng-1080p, seedance, sora, auto)
            api_key: API Key (用于 Seedance/Sora)
            ak: Access Key (用于 Jimeng)
            sk: Secret Key (用于 Jimeng)
            endpoint: 模型端点 (用于 Seedance)
        """
        if model == "auto":
            # 默认使用 jimeng-pro
            model = "jimeng-pro"

        self.model = model
        self._generator = self._create_generator(model, api_key, ak, sk, endpoint, **kwargs)

    def _create_generator(self, model: str, api_key: Optional[str], ak: Optional[str], sk: Optional[str], endpoint: Optional[str], **kwargs):
        """创建对应的生成器实例"""
        model_info = self.MODELS.get(model)
        if not model_info:
            raise ValueError(f"Unknown model: {model}. Available: {list(self.MODELS.keys())}")

        class_name = model_info["class"]

        if class_name == "JimengGenerator":
            return JimengGenerator(ak=ak, sk=sk, model=model)
        elif class_name == "VolcengineSeedanceGenerator":
            return VolcengineSeedanceGenerator(api_key=api_key, endpoint=endpoint, **kwargs)
        elif class_name == "AtlasSoraGenerator":
            return AtlasSoraGenerator(api_key=api_key, **kwargs)
        else:
            raise ValueError(f"Unknown generator class: {class_name}")

    def generate(
        self,
        prompt: str,
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **kwargs,
    ) -> str:
        """
        生成视频

        Args:
            prompt: 视频提示词
            image: 图片路径或 URL (图生视频)
            duration: 视频时长 (秒)
            aspect_ratio: 宽高比

        Returns:
            task_id: 任务 ID
        """
        # 检查模型是否支持图生视频
        if image:
            model_info = self.MODELS.get(self.model, {})
            if not model_info.get("supports_image"):
                raise ValueError(f"Model {self.model} does not support image-to-video")

        return self._generator.generate(prompt, image, duration, aspect_ratio, **kwargs)

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """
        轮询任务状态

        Args:
            task_id: 任务 ID
            interval: 轮询间隔 (秒)
            timeout: 超时时间 (秒)

        Returns:
            video_url: 视频 URL
        """
        return self._generator.poll(task_id, interval, timeout)

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """
        下载视频

        Args:
            url: 视频 URL
            filename: 保存文件名

        Returns:
            local_path: 本地文件路径
        """
        return self._generator.download(url, filename)

    def generate_and_download(
        self,
        prompt: str,
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        output: str = "output.mp4",
        poll_interval: int = 15,
        poll_timeout: int = 900,
    ) -> str:
        """
        生成视频并下载

        Args:
            prompt: 视频提示词
            image: 图片路径或 URL
            duration: 视频时长
            aspect_ratio: 宽高比
            output: 输出文件名
            poll_interval: 轮询间隔
            poll_timeout: 轮询超时

        Returns:
            local_path: 本地文件路径
        """
        task_id = self.generate(prompt, image, duration, aspect_ratio)
        print(f"[{self.model}] Task ID: {task_id}")

        video_url = self.poll(task_id, poll_interval, poll_timeout)
        print(f"[{self.model}] Video URL: {video_url}")

        local_path = self.download(video_url, output)
        print(f"[{self.model}] Saved to: {local_path}")

        return local_path

    @staticmethod
    def list_models() -> dict:
        """列出支持的模型"""
        return {
            name: {
                "supports_image": info["supports_image"],
                "max_duration": info["max_duration"],
            }
            for name, info in VideoGenerator.MODELS.items()
        }


# 兼容旧接口
class GeneratorAdapter:
    """生成器适配器 - 兼容旧接口"""

    def __init__(self, model: str = "auto", **credentials):
        self._gen = VideoGenerator(model=model, **credentials)

    def generate(self, prompt: str, image=None) -> str:
        """生成视频"""
        return self._gen.generate(prompt, image=image)

    def optimize_prompt(self, prompt: str) -> str:
        """优化提示词 (调用 optimizer)"""
        from .optimizer import PromptOptimizer
        optimizer = PromptOptimizer()
        return optimizer.optimize(prompt)

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """下载视频"""
        return self._gen.download(url, filename)